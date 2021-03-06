""" Deep Learning for glass-vs-liquid data """
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
import tensorflow as tf
import numpy as np 
import json
from generator_glassliquid import Generator
from collections import Counter
np.random.seed(0)
from sklearn.model_selection import train_test_split
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

""" Load the metadata """
with open('metadata/metadata.json', 'r') as f:
	metadata = json.load(f)

""" Shuffle the data """
np.random.shuffle(metadata)

""" Functions to convert the labels to one hot """
def get_unique_labels(metadata):
	return list(set([row['label'] for row in metadata]))

def create_one_hot_mapping(unique_labels):
	one_hot_mapping = dict()

	for i, label in enumerate(unique_labels):
		one_hot = np.zeros(len(unique_labels))
		one_hot[i] = 1
		one_hot_mapping[label] = one_hot

	return one_hot_mapping

def convert_to_one_hot(metadata, one_hot_mapping):
	for row in metadata:
		row['original_label'] = row['label']
		row['label'] = one_hot_mapping[row['label']]

	return metadata

""" Convert the data to one hot """
unique_labels = get_unique_labels(metadata)
one_hot_mapping = create_one_hot_mapping(unique_labels)
metadata = convert_to_one_hot(metadata, one_hot_mapping)

""" Define input and output sizes """
im_size = 250
n_outputs = len(unique_labels)

""" Create batch generators for train and test """
train_metadata, remaining_metadata = train_test_split(metadata, test_size=0.3, random_state=0)
validation_metadata, test_metadata = train_test_split(remaining_metadata, test_size = 0.5, random_state = 0)

train_generator = Generator(train_metadata, im_size=im_size, num_channel=4)
validation_generator = Generator(validation_metadata, im_size=im_size, num_channel=4)
test_generator = Generator(test_metadata, im_size=im_size, num_channel=4)

""" Hyperparameters """
batch_size = 80
epochs = 2
batches_per_epoch = 10
examples_per_eval = 1000
eta = 1e-3
beta = 0.01

""" Function that builds the graph for the neural network """
def deepnn(x):
	# First convolutional layer
	x_image = tf.reshape(x, [-1, 250, 250, 3])
	W_conv1 = tf.get_variable("W_conv1", shape=[10, 10, 3, 6])
	b_conv1 = tf.get_variable("b_conv1", shape=[6])
	h_conv1 = tf.nn.relu(conv2d(x_image, W_conv1) + b_conv1)
 
	# Second convolutional layer
	W_conv2 = tf.get_variable("W_conv2", shape=[5, 5, 6, 16])
	b_conv2 = tf.get_variable("b_conv2", shape=[16])
	h_conv2 = tf.nn.relu(conv2d(h_conv1, W_conv2) + b_conv2)

	# Fully connected layer
	W_fc1 = tf.get_variable("W_fc1", shape=[237 * 237 * 16, 80])
	b_fc1 = tf.get_variable("b_fc1", shape=[80])
	h_conv2_flat = tf.reshape(h_conv2, [-1, 237*237*16])
	h_fc1 = tf.nn.relu(tf.matmul(h_conv2_flat, W_fc1) + b_fc1)

	# Dropout on the fully connected layer
	keep_prob = tf.placeholder(tf.float32)
	h_fc1_drop = tf.nn.dropout(h_fc1, keep_prob, seed=0)

	# Output layer
	W_fc2 = tf.get_variable("W_fc2", shape=[80, n_outputs])
	b_fc2 = tf.get_variable("b_fc2", shape=[n_outputs])
	y_conv = tf.matmul(h_fc1_drop, W_fc2) + b_fc2

	# Returns the prediction and the dropout probability placeholder
	return y_conv, keep_prob, W_conv1, W_conv2, W_fc1, W_fc2


def conv2d(x, W):
	"""conv2d returns a 2d convolution layer with full stride."""
	return tf.nn.conv2d(x, W, strides=[1, 1, 1, 1], padding='VALID')

def main(_):
	# Input data
	x = tf.placeholder(tf.float32, [None, im_size, im_size, 3])

	# Output
	y_ = tf.placeholder(tf.float32, [None, n_outputs])

	# Build the graph for the deep net
	y_conv, keep_prob, W_conv1, W_conv2, W_fc1, W_fc2 = deepnn(x)

	# Define the los and the optimizer
	loss = tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits(labels=y_, logits=y_conv))
	regularizers = tf.nn.l2_loss(W_conv1) + tf.nn.l2_loss(W_conv2) + tf.nn.l2_loss(W_fc1) + tf.nn.l2_loss(W_fc2)
	loss = tf.reduce_mean(loss + beta*regularizers)
	train_step = tf.train.AdamOptimizer(eta).minimize(loss)
	correct_prediction = tf.equal(tf.argmax(y_conv, 1), tf.argmax(y_, 1))
	accuracy = tf.reduce_mean(tf.cast(correct_prediction, tf.float32))

	# Save GPU memory preferences
	config = tf.ConfigProto()
	config.gpu_options.allow_growth = True

	""" Lists for plotting """
	train_losses = []
	train_accuracies = []
	validation_losses = []
	validation_accuracies = []

	# Saver
	saver = tf.train.Saver()

	# Run the network
	with tf.Session(config=config) as sess:

		# Initialize variables
		sess.run(tf.global_variables_initializer())

		saver.restore(sess, "/project/depablo/kswanson/model.ckpt")

		# Compute total validation set error
		validation_total_accuracies = []
		for validation_X, validation_Y in validation_generator.data_in_batches(len(validation_generator.metadata), batch_size):
			validation_total_accuracies.append(accuracy.eval(feed_dict={
					x: validation_X, y_: validation_Y, keep_prob: 1.0}))

		validation_accuracy = np.mean(validation_total_accuracies)

		print('final validation accuracy %g' % (validation_accuracy))

		# Compute total test set error
		test_total_accuracies = []
		for test_X, test_Y in test_generator.data_in_batches(len(test_generator.metadata), batch_size):
			test_total_accuracies.append(accuracy.eval(feed_dict={
					x: test_X, y_: test_Y, keep_prob: 1.0}))

		test_accuracy = np.mean(test_total_accuracies)

		print('final test accuracy %g' % (test_accuracy))

		
	train_counts = Counter(row['original_label'] for row in train_generator.metadata)
	validation_counts = Counter(row['original_label'] for row in validation_generator.metadata)
	test_counts = Counter(row['original_label'] for row in test_generator.metadata)

	f = open('test_saver.txt', 'w')
	f.write('final validation accuracy %g \n' % (validation_accuracy))
	f.write('test accuracy %g \n' % (test_accuracy))
	f.write('train counts glass %g, liquid %g \n' % (train_counts['glass'], train_counts['liquid']))
	f.write('validation counts glass %g, liquid %g \n' % (validation_counts['glass'], validation_counts['liquid']))
	f.write('test counts glass %g, liquid %g \n' % (test_counts['glass'], test_counts['liquid']))
	f.write('epochs = %d, eta = %g, batch_size = %g' % (epochs, eta, batch_size))
	f.close()

# Run the program 
if __name__ == '__main__':
	tf.app.run(main=main)





  

