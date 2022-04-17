# From Donahue https://github.com/chrisdonahue/wavegan/blob/master/loader.py
# Modified to keep track of gold labels, assumed to be on the file names
from scipy.io.wavfile import read as wavread
import numpy as np

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
  fp = fp.decode('utf-8')
  if fast_wav:
    # Read with scipy wavread (fast).
    _fs, _wav = wavread(fp)
    if fs is not None and fs != _fs:
      raise NotImplementedError('Scipy cannot resample audio.')
    if _wav.dtype == np.int16:
      _wav = _wav.astype(np.float32)
      _wav /= 32768.
    elif _wav.dtype == np.float32:
      _wav = np.copy(_wav)
    else:
      raise NotImplementedError('Scipy cannot process atypical WAV files.')
  else:
    # Decode with librosa load (slow but supports file formats like mp3).
    import librosa
    _wav, _fs = librosa.core.load(fp, sr=fs, mono=False)
    if _wav.ndim == 2:
      _wav = np.swapaxes(_wav, 0, 1)

  assert _wav.dtype == np.float32

  # At this point, _wav is np.float32 either [nsamps,] or [nsamps, nch].
  # We want [nsamps, 1, nch] to mimic 2D shape of spectral feats.
  if _wav.ndim == 1:
    nsamps = _wav.shape[0]
    nch = 1
  else:
    nsamps, nch = _wav.shape
  _wav = np.reshape(_wav, [nsamps, 1, nch])
 
  # Average (mono) or expand (stereo) channels
  if nch != num_channels:
    if num_channels == 1:
      _wav = np.mean(_wav, 2, keepdims=True)
    elif nch == 1 and num_channels == 2:
      _wav = np.concatenate([_wav, _wav], axis=2)
    else:
      raise ValueError('Number of audio channels not equal to num specified')

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
    slice_len = 65536,#- maybe not needed since I'm not slicing up the wav files; one wav file = one training datum. I will set it to be as long as a synthesized VCV will likely to be
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
  dataset = tf.data.Dataset.from_tensor_slices(fps)

  # Shuffle all filepaths every epoch
  if shuffle:
    dataset = dataset.shuffle(buffer_size=len(fps),seed=1) #note: I added a random seed for reproducibility

  # Repeat
  if repeat:
    dataset = dataset.repeat()

  def _decode_audio_shaped(fp):
    _decode_audio_closure = lambda _fp: decode_audio(
      _fp,
      fs=decode_fs,
      num_channels=decode_num_channels,
      normalize=decode_normalize,
      fast_wav=decode_fast_wav)

    audio = tf.compat.v1.py_func(
        _decode_audio_closure,
        [fp],
        tf.float32,
        stateful=False)
    audio.set_shape([None,1, decode_num_channels])
    return audio



  # Cerys: I think this function is used to slice up longer audio to make more, smaller training examples.
  # I don't want to do that; I want to train on whole VCV sequences, so I tried skipping applying this function.
  #However, that resulted in a lack of padding, which allowed the audio vectors different lengths; they need to
  #all be the same length so they fit into the network properly and can be batched (for some reason Tensorflow
  #Dataset won't batch things of different lengths - tensorflow.python.framework.errors_impl.InvalidArgumentError: Cannot
  # batch tensors with different shapes in component 1". So, I'm going to try and just keep the padding part without
  # the slicing-up part.
  #Parallel
  def _slice(audio):
    # Calculate hop size
    if slice_overlap_ratio < 0:
      raise ValueError('Overlap ratio must be greater than 0')
    slice_hop = int(round(slice_len * (1. - slice_overlap_ratio)) + 1e-4)
    if slice_hop < 1:
      raise ValueError('Overlap ratio too high')

    # Randomize starting phase:  -Cerys: not necessary for me, this is just to handle generator phase artefact
    # if slice_randomize_offset:
    #   start = tf.random_uniform([], maxval=slice_len, dtype=tf.int32)
    #   audio = audio[start:]

    # Extract sliceuences
    audio_slices = tf.signal.frame(
        audio,
        slice_len,
        slice_hop,
        pad_end=slice_pad_end,
        pad_value=0,
        axis=0)

    # Donahue: Only use first slice if requested
    # Me: definitely only use first slice because I only want one audio per VCV sequence,
    # and the VCVs are short so they will fit in the first slice
    audio_slices = audio_slices[:1]

    return audio_slices

  def _slice_dataset_wrapper(audio):
    audio_slices = _slice(audio)
    return tf.data.Dataset.from_tensor_slices(audio_slices)



  # Extract parallel sliceuences from both audio and features
  # Decode audio
  # Cerys: the original line below throws away the file names and replaces them with the audio in those files
  # Dataset elements can be tuples, so instead of throwing out the file names, I make them the first members of the tuple,
  # where the second element is the content audio vector
  # dataset = dataset.map(
  #     _decode_audio_shaped,
  #     num_parallel_calls=decode_parallel_calls)
  fp_dataset = dataset
  dataset = dataset.map(
    _decode_audio_shaped,
    num_parallel_calls=decode_parallel_calls)
  dataset = dataset.flat_map(_slice_dataset_wrapper)
  #dataset = dataset.map(lambda audio: tf.reshape(audio, (slice_len,)))
  dataset = dataset.map(lambda audio: tf.reshape(audio, (slice_len,1)))
  dataset = tf.data.Dataset.zip((fp_dataset, dataset))

  if debug:
    for element in dataset:
      print(element)


  if debug:
    length = 0
    for element in dataset:
      print(element)
      length += 1
    print("LENGTH", length)

  # Shuffle examples
  if shuffle:
    dataset = dataset.shuffle(buffer_size=shuffle_buffer_size)




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


