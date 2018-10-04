"""Dataloader for Data objects, adapted from PyTorch Geometric repository at https://github.com/rusty1s/pytorch_geometric, by Kirk Swanson"""
# Load modules
from __future__ import print_function, division
import torch.utils.data
from batch_PyTorch import Batch

class DataLoader(torch.utils.data.DataLoader):
    def __init__(self, dataset, batch_size=1, shuffle=True, **kwargs):
        """Initialize a DataLoader object using the custom collate_fn from Batch class"""
        super(DataLoader, self).__init__(
            dataset,
            batch_size,
            shuffle,
            collate_fn=lambda batch: Batch.from_data_list(batch),
            **kwargs)