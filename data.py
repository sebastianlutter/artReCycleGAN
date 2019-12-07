'''\
Data module: loading Datasets.

This project uses the following convention for datases:
Each dataset is a set of jpeg pictures in a directory. In the same directory,
an info file, usually called 'dataset.txt', contains the list of images to
load from that folder (some images might be excluded). This file must contain
an empty line: this is interpreted as the separator for the training/testing
split.
'''

import os
import tensorflow as tf


# Supported datasets. 'name': 'info file'
datasets = {
    'sisley': '../datasets/art/Alfred Sisley/dataset.txt',
    'guillaumin': '../datasets/art/Armand Guillaumin/dataset.txt',
    'caravaggio': '../datasets/art/Caravaggio/dataset.txt',
    'monet': '../datasets/art/Claude Monet/dataset.txt',
    'manet': '../datasets/art/Edouard Manet/dataset.txt',
    'caillebotte': '../datasets/art/Gustave Caillebotte/dataset.txt',
    'signac': '../datasets/art/Paul Signac/dataset.txt',
    'vangogh': '../datasets/art/Vincent van Gogh/dataset.txt',
    'foto': '../datasets/foto/dataset.txt',
    'summer': '../datasets/summer/dataset.txt',
    'winter': '../datasets/winter/dataset.txt',
}


def _dataset_files(name, split):
  '''\
  Returns all filenames that compose the requested dataset.

  Args:
    name: a dataset name
    split: 'train' or 'test'

  Returns:
    Dataset of all filenames, total number of images.
  '''

  # Checks
  if not name in datasets or not split in ('train', 'test'):
    raise ValueError('Illegal dataset specification')

  # Dataset info
  info_file = datasets[name]
  dataset_dir = os.path.dirname(info_file)
  with open(info_file) as dataset_info:
    files = dataset_info.read().splitlines()

  # Split
  for split_i in range(len(files)):
    if len(files[split_i]) == 0:
      break
  if split == 'train':
    files = files[:split_i]
  else:
    files = files[split_i+1:]

  # Paths
  files = [os.path.join(dataset_dir, f) for f in files]

  # Dataset
  return tf.data.Dataset.from_tensor_slices(files), len(files)


def load(name, split, shape=(256, 256, 3), batch=None):
  '''\
  Returns a Dataset. The dataset is already transformed to create the input
  pipeline.

  Args:
    name: a dataset name
    split: 'train' or 'test'
    shape: desired shape of each image
    batch: how many samples to return. If None, the entire dataset is returned.

  Returns:
    Tf Dataset (infinite number of elements)
  '''
  # TODO: incorrect image ratios. Missing random crop, flip etc

  def load_image(path):
    ''' Parses a single image. '''

    img = tf.io.read_file(path)
    img = tf.image.decode_jpeg(img, channels=shape[2])
    img = tf.image.resize(img, shape[0:2])
    return img

  # Dataset of paths
  images, size = _dataset_files(name, split)

  # Select batch
  if not batch or batch < 1 or batch > size :
    batch = size

  # Input pipeline
  images = images.shuffle(min(size, 10000))
  images = images.map(load_image)
  images = images.batch(batch)
  images = images.prefetch(1)

  return images