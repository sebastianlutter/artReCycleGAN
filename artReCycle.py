#!/usr/bin/env python3

'''\
Main script file. Implementation of CycleGAN paper.
Tested with Tensorflow 2.1rc0.
'''

import os
import argparse
import shutil
import json
import tensorflow as tf

import data
import models
from customizations import *


def train(args):
  '''\
  Training function.

  Args:
    args: namespace of arguments. Run 'artRecycle train --help' for info.
  '''

  # Model name and paths
  model_name = '{}|{}'.format(*args.datasets)
  model_path, log_path, logs_path = _prepare_directories(
      model_name, resume=args.cont)

  model_json = os.path.join(model_path, 'keras.json')
  model_checkpoint = os.path.join(model_path, 'model')

  # Define datasets
  image_shape = (300, 300, 3)
  train_datasets, train_size = data.load_pair(*args.datasets, 'train',
      shape=image_shape, batch=args.batch)
  test_datasets, test_size = data.load_pair(*args.datasets, 'test',
      shape=image_shape, batch=args.batch)

  # Define keras model
  keras_model = models.define_model(image_shape)

  # Save keras model
  keras_json = keras_model.to_json()
  keras_json = json.dumps(json.loads(keras_json), indent=2)
  with open(model_json, 'w') as f:
    f.write(keras_json)

  # Resuming
  if args.cont:
    keras_model.load_weights(model_checkpoint)
    print('> Weights loaded')

  # TODO: writers and save graph

  # Training steps
  step_saver = CountersSaver(log_dir=logs_path, log_every=args.logs)

  steps_per_epoch = int(train_size/args.batch) \
      if not args.epoch_steps else args.epoch_steps
  epochs = range(step_saver.epoch, args.epochs)

  # Print job
  print('> Training.  Epochs:', epochs)

  # Training loop
  for epoch in epochs:
    for epoch_step in range(steps_per_epoch):

      # TODO: How to write the forward pass with datasets?

      # Debugging
      print('training step')
      input()

      ## Validation and log
      #if step_saver.step % args.logs == 0 or epoch_step == steps_per_epoch-1:

      #  # Metrics
      #  dA_loss_metric = tf.metrics.Mean('dA_loss')

      #  # Evaluate on test set
      #  for test_batch_A, test_batch_B in zip(*test_datasets):
      #    print(test_batch_A.shape, test_batch_B.shape)

      #    # Accumulate
      #    fake_B, fake_A, dA_loss, dB_loss, gA_loss, gB_loss = \
      #        keras_model((test_batch_A, test_batch_B))

      #    dA_loss_metric.update_state(dA_loss)


      # End step
      step_saver.new_step()

    # End epoch
    step_saver.new_epoch()


def use(args):
  '''\
  Transform images with the net.

  Args:
    args: namespace of arguments. Run 'artRecycle use --help' for info.
  '''

  raise NotImplementedError()


def debug(args):
  '''\
  Debugging function.

  Args:
    args: namespace of arguments. Run --help for info.
  '''
  import matplotlib.pyplot as plt

  print('> Debug')

  # Saving the Tensorboard grpah without training

  # Model
  image_shape = (300, 300, 3)
  keras_model = models.define_model(image_shape)

  keras_model.summary()

  # TensorBoard callback writer
  tbCallback = tf.keras.callbacks.TensorBoard('debug', write_graph=True)
  tbCallback.set_model(keras_model)


def _prepare_directories(model_name, resume=False):
  '''\
  Prepares empty directories where logs and models are saved.
  'log directory' refers to the path of the current log.
  'logs 'directory' refers to the path of all logs (parent dir).

  Args:
    model_name: identifier for this training job
    resume: if true, directories are not erased.
  Returns:
    model directory, log directory, logs directory
  '''

  # Base paths
  model_path = os.path.join('models', model_name)
  logs_path = os.path.join('logs', model_name)
  dirs = (model_path, logs_path)

  # Erase?
  if not resume:

    # Existing?
    existing = []
    for d in dirs:
      if os.path.exists(d):
        existing.append(d)

    # Confirm
    if existing:
      print('Erasing', *existing, '. Continue (Y/n)? ', end='')
      c = input()
      if not c in ('y', 'Y', ''): quit()

    # New
    for d in existing:
      shutil.rmtree(d)
    for d in dirs:
      os.makedirs(d)

  # Logs alwas use new directories (using increasing numbers)
  i = 0
  while os.path.exists(os.path.join(logs_path, str(i))): i += 1
  log_path = os.path.join(logs_path, str(i))
  os.mkdir(log_path)

  return (model_path, log_path, logs_path)


def main():
  '''\
  Main function. Called when this file is executed as script.
  '''

  # Default settings
  batch_size = 30
  learning_rate = 0.001
  epochs = 1
  log_frequency = 1

  # Datasets
  datasets_names = {name for name in data.datasets}

  # Parsing arguments
  parser = argparse.ArgumentParser(description=
      'ArtReCycle: my implementation of CycleGAN with Tensorflow 2.0')
  op_parsers = parser.add_subparsers(help='Operation', dest='op')

  # Train op
  train_parser = op_parsers.add_parser('train', help='Train the net')
  train_parser.add_argument('-d', '--datasets', nargs=2, required=True,
      type=str, choices=datasets_names, metavar=('datasetA', 'datasetB'),
      help='Input dataset. Choose from: '+str(datasets_names))
  train_parser.add_argument('-b', '--batch', type=int, default=batch_size,
      help='Number of elements in each batch')
  train_parser.add_argument('-r', '--rate', type=float, default=learning_rate,
      help='Learning rate')
  train_parser.add_argument('-e', '--epochs', type=int, default=epochs,
      help='Number of epochs to train')
  train_parser.add_argument('-s', '--epoch_steps', type=int, default=None,
      help='Force a specific number of steps in each epoch')
  train_parser.add_argument('-l', '--logs', type=int, default=log_frequency,
      help='Save logs after this number of batches')
  train_parser.add_argument('-c', '--continue', action='store_true', dest='cont',
      help='Loads most recent saved model and resumes training.')

  # Use op
  use_parser = op_parsers.add_parser('use',
      help='Apply the transformation to images')

  # Debug op
  debug_parser = op_parsers.add_parser('debug')
  debug_parser.add_argument('args', nargs='*')

  args = parser.parse_args()

  # Go
  if args.op == 'train':
    train(args)
  elif args.op == 'use':
    use(args)
  elif args.op == 'debug':
    debug(args)


if __name__ == '__main__':
  main()
