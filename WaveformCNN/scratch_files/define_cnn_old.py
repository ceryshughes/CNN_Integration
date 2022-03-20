#Code to set up CNN architecture, adapting Donahue's WaveGan discriminator code
# TODO: convert to Module object-oriented setup, much nicer-looking
import tensorflow as tf
import numpy as np


def conv_layer_setup(x,
    kernel_len=25,
    dim=64,
    use_batchnorm=False):
  batch_size = tf.shape(x)[0]
  slice_len = int(x.get_shape()[1])

  if use_batchnorm:
    batchnorm = lambda x: tf.layers.batch_normalization(x, training=True)
  else:
    batchnorm = lambda x: x

  # Layer 0
  # [16384, 1] -> [4096, 64]
  output = x
  with tf.variable_scope('downconv_0'):
    output = tf.layers.conv1d(output, dim, kernel_len, 4, padding='SAME')
  output = lrelu(output)

  # Layer 1
  # [4096, 64] -> [1024, 128]
  with tf.variable_scope('downconv_1'):
    output = tf.layers.conv1d(output, dim * 2, kernel_len, 4, padding='SAME')
    output = batchnorm(output)
  output = lrelu(output)

  # Layer 2
  # [1024, 128] -> [256, 256]
  with tf.variable_scope('downconv_2'):
    output = tf.layers.conv1d(output, dim * 4, kernel_len, 4, padding='SAME')
    output = batchnorm(output)
  output = lrelu(output)

  # Layer 3
  # [256, 256] -> [64, 512]
  with tf.variable_scope('downconv_3'):
    output = tf.layers.conv1d(output, dim * 8, kernel_len, 4, padding='SAME')
    output = batchnorm(output)
  output = lrelu(output)

  # Layer 4
  # [64, 512] -> [16, 1024]
  with tf.variable_scope('downconv_4'):
    output = tf.layers.conv1d(output, dim * 16, kernel_len, 4, padding='SAME')
    output = batchnorm(output)
  output = lrelu(output)

  #What is this check for? Where does this number come from?
  if slice_len == 32768:
    # Layer 5
    # [32, 1024] -> [16, 2048]
    with tf.variable_scope('downconv_5'):
      output = tf.layers.conv1d(output, dim * 32, kernel_len, 2, padding='SAME')
      output = batchnorm(output)
    output = lrelu(output)
  elif slice_len == 65536:
    # Layer 5
    # [64, 1024] -> [16, 2048]
    with tf.variable_scope('downconv_5'):
      output = tf.layers.conv1d(output, dim * 32, kernel_len, 4, padding='SAME')
      output = batchnorm(output)
    output = lrelu(output)


  return output, batch_size



def output_layer_setup(output, batch_size,output_dim):
  # Flatten
  output = tf.reshape(output, [batch_size, -1])

  # Original: Connect to single logit
  # Modification: allow multiple output variables - softmax
  with tf.variable_scope('output'):
    #Where is the activation function for this layer defined?oh..."output" is output from previous layer,
    #which had lrelu... so is this last cap not nonlinear from that?
    output = tf.layers.dense(output, output_dim)[:, 0]
  return output

def CnnCategorizer( output_dim, x,
    kernel_len=25,
    dim=64,
    use_batchnorm=False):
  model, batch_size = conv_layer_setup(x,kernel_len, dim, use_batchnorm)
  model = output_layer_setup(model, batch_size, output_dim)
  return model



###Donahue code with my comments###

#This scales the relu by some number alpha,
# but how does this output relu? How does it get negative values to 0?
# If alpha = 0.2, how is alpha * inputs ever greater than inputs? Oh, when it's negative... so instead of
# pushing negatives to 0, we just push them up closer to 0
def lrelu(inputs, alpha=0.2):
  return tf.maximum(alpha * inputs, inputs)

# Donahue: "Phase Shuffle is a technique for removing pitched noise artifacts that come from using transposed convolutions in audio
# generation models. Phase shuffle is an operation with hyperparameter . It randomly perturbs the phase of each layer’s
# activations by −n to n samples before input to the next layer.
#
# In the original application in WaveGAN, the authors only apply phase shuffle to the discriminator, as the latent
# vector already provides the generator a mechanism to manipulate the phase of a resultant waveform. Intuitively speaking,
# phase shuffle makes the discriminator’s job more challenging by requiring invariance to the phase of the input waveform."
def apply_phaseshuffle(x, rad, pad_type='reflect'):
  b, x_len, nch = x.get_shape().as_list()

  phase = tf.random_uniform([], minval=-rad, maxval=rad + 1, dtype=tf.int32)
  pad_l = tf.maximum(phase, 0)
  pad_r = tf.maximum(-phase, 0)
  phase_start = pad_r
  x = tf.pad(x, [[0, 0], [pad_l, pad_r], [0, 0]], mode=pad_type)

  x = x[:, phase_start:phase_start+x_len]
  x.set_shape([b, x_len, nch])

  return x

"""
  Input: [None, slice_len, nch]
  Output: [None] (linear output)
"""
def WaveGANDiscriminator(
    x,
    kernel_len=25,
    dim=64,
    use_batchnorm=False,
    phaseshuffle_rad=0):
  batch_size = tf.shape(x)[0]
  slice_len = int(x.get_shape()[1])

  if use_batchnorm:
    batchnorm = lambda x: tf.layers.batch_normalization(x, training=True)
  else:
    batchnorm = lambda x: x

  if phaseshuffle_rad > 0:
    phaseshuffle = lambda x: apply_phaseshuffle(x, phaseshuffle_rad)
  else:
    phaseshuffle = lambda x: x

  # Layer 0
  # [16384, 1] -> [4096, 64]
  output = x
  with tf.variable_scope('downconv_0'):
    output = tf.layers.conv1d(output, dim, kernel_len, 4, padding='SAME')
  output = lrelu(output)
  output = phaseshuffle(output)

  # Layer 1
  # [4096, 64] -> [1024, 128]
  with tf.variable_scope('downconv_1'):
    output = tf.layers.conv1d(output, dim * 2, kernel_len, 4, padding='SAME')
    output = batchnorm(output)
  output = lrelu(output)
  output = phaseshuffle(output)

  # Layer 2
  # [1024, 128] -> [256, 256]
  with tf.variable_scope('downconv_2'):
    output = tf.layers.conv1d(output, dim * 4, kernel_len, 4, padding='SAME')
    output = batchnorm(output)
  output = lrelu(output)
  output = phaseshuffle(output)

  # Layer 3
  # [256, 256] -> [64, 512]
  with tf.variable_scope('downconv_3'):
    output = tf.layers.conv1d(output, dim * 8, kernel_len, 4, padding='SAME')
    output = batchnorm(output)
  output = lrelu(output)
  output = phaseshuffle(output)

  # Layer 4
  # [64, 512] -> [16, 1024]
  with tf.variable_scope('downconv_4'):
    output = tf.layers.conv1d(output, dim * 16, kernel_len, 4, padding='SAME')
    output = batchnorm(output)
  output = lrelu(output)

  if slice_len == 32768:
    # Layer 5
    # [32, 1024] -> [16, 2048]
    with tf.variable_scope('downconv_5'):
      output = tf.layers.conv1d(output, dim * 32, kernel_len, 2, padding='SAME')
      output = batchnorm(output)
    output = lrelu(output)
  elif slice_len == 65536:
    # Layer 5
    # [64, 1024] -> [16, 2048]
    with tf.variable_scope('downconv_5'):
      output = tf.layers.conv1d(output, dim * 32, kernel_len, 4, padding='SAME')
      output = batchnorm(output)
    output = lrelu(output)

  # Flatten
  output = tf.reshape(output, [batch_size, -1])

  # Connect to single logit
  with tf.variable_scope('output'):
    output = tf.layers.dense(output, 1)[:, 0]

  # Don't need to aggregate batchnorm update ops like we do for the generator because we only use the discriminator for training

  return output
