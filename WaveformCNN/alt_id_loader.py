# From Donahue https://github.com/chrisdonahue/wavegan/blob/master/loader.py
# Modified to keep track of gold labels, assumed to be on the file names
from scipy.io.wavfile import read as wavread
import numpy as np
import librosa

import tensorflow as tf

import sys

debug = False

def decode_audio(fp, fs=None, num_channels=1, normalize=False, fast_wav=False):
  """Decodes audio file paths into 32-bit floating point vectors.

  Args:
    fp: Audio file path. Cerys: this is a byte string (Datasets store strings as bytes; Donahue intended this function to be compatible with Datastes)
    fs: If specified, resamples decoded audio to this rate.
    mono: If true, averages channels to mono.
    fast_wav: Assume fp is a standard WAV file (PCM 16-bit or float 32-bit).

  Returns:
    A np.float32 array containing the audio samples at specified sample rate.
  """

  # Decode with librosa load (slow but supports file formats like mp3).
  _wav, _fs = librosa.core.load(fp, sr=fs, mono=False)
  if _wav.ndim == 2:
    _wav = np.swapaxes(_wav, 0, 1)

  assert _wav.dtype == np.float32

  # At this point, _wav is np.float32 either [nsamps,] or [nsamps, nch].
  # We want [nsamps, 1, nch] to mimic 2D shape of spectral feats.


  if normalize:
    factor = np.max(np.abs(_wav))
    if factor > 0:
      _wav /= factor

  return _wav


def id_decode_extract_and_batch(
    fps,
    batch_size,
    decode_fs,
    decode_num_channels,
    slice_len = 8192,#- maybe not needed since I'm not slicing up the wav files; one wav file = one training datum. I will set it to be as long as a synthesized VCV will likely to be
    decode_normalize=True,
    decode_fast_wav=False,
    decode_parallel_calls=1,
    slice_randomize_offset=False, #- not needed since I'm not slicing up the wav files or discriminating real vs fake and shuffling phase;
        # one wav file = one training datum
    slice_first_only=False, #- not needed since I'm not slicing up the wav files; one wav file = one training datum
    slice_overlap_ratio=0, # - not needed since I'm not slicing up the wav files; one wav file = one training datum
    slice_pad_end=True, #- needed to make slices same length to be compatible for batching; Donahue has this optional,
        # but I may remove it and just automatically pad
    repeat=False,
    shuffle=False,
    shuffle_buffer_size=None,
    prefetch_size=None,
    prefetch_gpu_num=None):
  """Decodes audio file paths into mini-batches of samples.


  Args:
    fps: List of audio file paths.
    batch_size: Number of items in the batch.
    Cerys: not used---slice_len: Length of the sliceuences in samples or feature timesteps.
    decode_fs: (Re-)sample rate for decoded audio files.
    decode_num_channels: Number of channels for decoded audio files.
    decode_normalize: If false, do not normalize audio waveforms.
    decode_fast_wav: If true, uses scipy to decode standard wav files.
    decode_parallel_calls: Number of parallel decoding threads.
    Cerys: not used ---slice_randomize_offset: If true, randomize starting position for slice.
    ---slice_first_only: If true, only use first slice from each audio file.
    ---slice_overlap_ratio: Ratio of overlap between adjacent slices.
    ---slice_pad_end: If true, allows zero-padded examples from the end of each audio file.
    repeat: If true (for training), continuously iterate through the dataset.
    shuffle: If true (for training), buffer and shuffle the sliceuences.
    shuffle_buffer_size: Number of examples to queue up before grabbing a batch.
    prefetch_size: Number of examples to prefetch from the queue.
    prefetch_gpu_num: If specified, prefetch examples to GPU.

  Old:
  /Returns:
    /A tuple of np.float32 tensors representing audio waveforms.
      /audio: [batch_size, slice_len, 1, nch]

  Cerys: updated to also return file names of the waveforms
  Returns:
    A tuple of (string, np.float32 tensor) tuples where the np.float32 tensors represent audio waveforms
    audio: batch_size, slice_len, 1, nch
  """
  # Create dataset of filepaths



  reg_size =  lambda audio: tf.signal.frame(
    audio,
    slice_len,
    frame_step=int(round(slice_len * (1. - slice_overlap_ratio)) + 1e-4),
    pad_end=slice_pad_end,
    pad_value=0,
    axis=0)[:1]
  reshape = lambda audio: tf.reshape(audio, (slice_len,1))



  dataset = tf.data.Dataset.from_tensor_slices(([reshape(reg_size(librosa.core.load(fp).set_shape([None, 1, decode_num_channels]))) for fp in fps], fps))








  # Make batches
  dataset = dataset.batch(batch_size, drop_remainder=False) #note: I changed this from True to False. I think
  #Donahue had it set as True because they used infinite batches (just keep recycling the same data) so it didn;t
  #matter if they threw some data away on a batch; it could get reincorporated on the next batch.
  #Because I don't want the infinite batching (difficult to work with), I don't want to throw away the
  #remaining data.

  if debug:
    length = 0
    for element in dataset:
      print(element)
      length += 1
    print("LENGTH", length)

  # Prefetch a number of batches
  if prefetch_size is not None:
    dataset = dataset.prefetch(prefetch_size)
    if prefetch_gpu_num is not None and prefetch_gpu_num >= 0:
      dataset = dataset.apply(
          tf.data.experimental.prefetch_to_device(
            '/device:GPU:{}'.format(prefetch_gpu_num)))


  # Get tensors - why is this part necessary? Oh, because of prefetching? No... prefetching just returns
  #a dataset with the same interface as any other...
  #Cerys: updated iterator code to Tensorflow v2
  #iterator = iter(dataset)

  #return next(iterator) #Cerys: isn't this throwing away a bunch of batches?
  return dataset


#No longer necessary- batched Datasets let you ignore the batch level
# Cerys: A helper function to pass into Dataset.map to extract either the filenames or the audio from the batched dataset, maintaining
# order
# index: 0 to return the batch with only the first element of each tuple, i.e., just the filenames
#        1 to return the batch with only the second element of each tuple, i.e., just the audio vectors
# def separate_in_batch(index, batch):
#   return [element[index] for element in batch]


