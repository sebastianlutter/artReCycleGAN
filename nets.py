'''\
Networks definitions.
Implementations for the CycleGAN model.
Models are implemented as composite layers, too.

Differences from the paper:
  - Weights initialization
  - Their implementation, not the paper, contains an additional convolution
    layer before the last.
  - Paper says that last activation is also a relu. Their implementation
    contains a tanh instead.
  - Other implementations than the original also add a relu activation
    after the sum of the residual blocks (after skip connections).
'''

import tensorflow as tf
from tensorflow.keras import layers

from layers import *


class CycleGAN(BaseLayer):
  '''\
  Full CycleGAN model.
  Inputs are batch of images from both datasets.
  '''

  def build(self, input_shape):
    ''' Defines the net. '''

    # Preprocessing
    self.preprocessing = ImagePreprocessing(out_size=(256,256))

    # Discriminators
    self.generator_AB = Generator(name='Generator_AB')
    self.generator_BA = Generator(name='Generator_BA')

    # Generators
    self.discriminator_A = Discriminator(name='Discriminator_A')
    self.discriminator_B = Discriminator(name='Discriminator_B')

    # Losses
    self.discriminator_loss = DiscriminatorLoss()
    self.generator_loss = GeneratorLoss()

    # Super
    BaseLayer.build(self, input_shape)


  def call(self, inputs):
    ''' Forward pass '''

    # Separate inputs of the two domains
    images_A, images_B = inputs

    # Image preprocessing
    images_A = self.preprocessing(images_A)
    images_B = self.preprocessing(images_B)

    # Normal transform
    fake_B = self.generator_AB(images_A)
    fake_A = self.generator_BA(images_B)

    # Rename outputs
    fake_A = tf.identity(fake_A, name='fake_A')
    fake_B = tf.identity(fake_B, name='fake_B')

    # Decisions (logits)
    all_for_A = tf.concat((images_A, fake_A), axis=0, name='all_A')
    decision_A = self.discriminator_A(all_for_A)

    all_for_B = tf.concat((images_B, fake_B), axis=0, name='all_B')
    decision_B = self.discriminator_B(all_for_B)

    # Discriminator GAN loss
    discriminator_A_loss = self.discriminator_loss(decision_A)
    discriminator_B_loss = self.discriminator_loss(decision_B)

    # Generator GAN loss
    generator_AB_loss = self.generator_loss(decision_B)
    generator_BA_loss = self.generator_loss(decision_A)

    # Returns
    outputs = (
        fake_A,
        fake_B,
        tf.identity(discriminator_A_loss, name='discriminator_A_loss'),
        tf.identity(discriminator_B_loss, name='discriminator_B_loss'),
        tf.identity(generator_AB_loss, name='generator_AB_loss'),
        tf.identity(generator_BA_loss, name='generator_BA_loss'),
      )
    return outputs


class Debugging(BaseLayer):
  '''\
  This model is only used during development.
  '''

  def build(self, input_shape):
    ''' Defines the net '''

    # Def
    self.layers_stack = [

        ImagePreprocessing(out_size=(256,256)),
        Discriminator(),
        ReduceMean(),
      ]

    # Super
    BaseLayer.build(self, input_shape)


class Discriminator(BaseLayer):
  '''\
  Image discriminator in CycleGAN (PatchGAN).
  Each block is a 2d convolution, instance normalization, and LeakyReLU
  activation. The number of filter double each time, while the image size is
  halved. The final output is a (sigmoid) map of classifications for
  {true, false}. With a 256x256 image input, each pixel of the 16x16 output map
  has 70x70 receptive field.

  From a batch of input images, returns scalar logits for binary
  classification.
  '''

  def build(self, input_shape):
    ''' Defines the net. '''

    # Parameters
    filters = 64
    Activation = lambda: layers.LeakyReLU(0.2)

    # Input block
    self.layers_stack += [
        layers.Conv2D(filters=filters, kernel_size=4, strides=2,
          padding='same'),
        Activation(),
      ]

    # Other blocks
    for i in range(3):

      filters *= 2
      self.layers_stack += [
          layers.Conv2D(filters=filters, kernel_size=4, strides=2,
            padding='same'),
          InstanceNormalization(),
          Activation(),
        ]

    # Output block
    self.layers_stack += [
        layers.Conv2D(filters=1, kernel_size=4, strides=1, padding='same'),
        lambda x: tf.identity(x, name='logits'),
      ]

    # Built
    BaseLayer.build(self, input_shape)


class Generator(BaseLayer):
  '''\
  Image generator in CycleGAN. Transforms images from one domain to another.
  The generator is composed of three parts: encoding, transformation,
  deconding, which are respectively based on convolutional, resnet, and
  convolutional transpose blocks. See paper for a more precise description.
  '''

  class Encoding(BaseLayer):
    ''' Encoding phase of the generator '''

    def build(self, input_shape):

      # Def
      self.layers_stack = [

          GeneralConvBlock( filters=64, kernel_size=7, stride=1, pad=3 ),
          GeneralConvBlock( filters=128, kernel_size=3, stride=2, pad='same' ),
          GeneralConvBlock( filters=256, kernel_size=3, stride=2, pad='same' ),
        ]

      # Super
      BaseLayer.build(self, input_shape)


  class Transformation(BaseLayer):
    ''' Transformation phase of the generator '''

    resnet_blocks = 9

    def build(self, input_shape):

      # Def
      for i in range(self.resnet_blocks):
        self.layers_stack.append( ResNetBlock( filters=256 ) )

      # Super
      BaseLayer.build(self, input_shape)


  class Decoding(BaseLayer):
    ''' Decoding phase of the generator '''

    def build(self, input_shape):

      # Def
      self.layers_stack = [

          GeneralConvTransposeBlock( filters=128, kernel_size=3, stride=2 ),
          GeneralConvTransposeBlock( filters=64, kernel_size=3, stride=2 ),
          GeneralConvBlock( filters=3, kernel_size=7, stride=1, pad=3,
              activation=False ),
          tf.keras.activations.tanh,
        ]

      # Super
      BaseLayer.build(self, input_shape)


  # Generator
  def build(self, input_shape):
    ''' Defines the net '''

    # Def
    self.layers_stack = [

        Generator.Encoding(),
        Generator.Transformation(),
        Generator.Decoding(),
      ]

    # Super
    BaseLayer.build(self, input_shape)
