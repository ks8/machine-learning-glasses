from argparse import Namespace
from typing import Callable, List

import torch.nn as nn

from GlassDataset_PyTorch import GlassDataset
from predict import predict


def evaluate_predictions(preds: List[List[float]],
                         targets: List[List[float]],
                         metric_func: Callable) -> List[float]:
    """
    Evaluates predictions using a metric function and filtering out invalid targets.

    :param preds: A list of lists of shape (data_size, num_tasks) with model predictions.
    :param targets: A list of lists of shape (data_size, num_tasks) with targets.
    :param metric_func: Metric function which takes in a list of targets and a list of predictions.
    :return: A list with the score for each task based on `metric_func`.
    """
    data_size, num_tasks = len(preds), len(preds[0])

    # Filter out empty targets
    # valid_preds and valid_targets have shape (num_tasks, data_size)
    valid_preds = [[] for _ in range(num_tasks)]
    valid_targets = [[] for _ in range(num_tasks)]
    for i in range(num_tasks):
        for j in range(data_size):
            if targets[j][i] is not None:  # Skip those without targets
                valid_preds[i].append(preds[j][i])
                valid_targets[i].append(targets[j][i])

    # Compute metric
    results = []
    for i in range(num_tasks):
        # Skip if all targets are identical
        if all(target == 0 for target in valid_targets[i]) or all(target == 1 for target in valid_targets[i]):
            continue
        results.append(metric_func(valid_targets[i], valid_preds[i]))

    return results


def evaluate(model: nn.Module,
             data: GlassDataset,
             metric_func: Callable,
             args: Namespace) -> List[float]:
    """
    Evaluates an ensemble of models on a dataset.

    :param model: A model.
    :param data: A GlassDataset.
    :param metric_func: Metric function which takes in a list of targets and a list of predictions.
    :param args: Arguments.
    :return: A list with the score for each task based on `metric_func`.
    """
    targets = data.y.float().unsqueeze(1)

    preds = predict(
        model=model,
        data=data,
        args=args
    )

    results = evaluate_predictions(
        preds=preds,
        targets=targets,
        metric_func=metric_func
    )

    return results
