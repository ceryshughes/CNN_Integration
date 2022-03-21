#Data:
# -inputs are .wav files in a folder with ID names
# -gold labels are in a csv file with a FileID column and a Category column; each row represents a file

debug = False

import cnn
import id_loader #From Donahue's WaveGan
import pandas
import os
import sys
import argparse
import numpy as np
import tensorflow as tf

# categories: set of string with no duplicates and cardinality >= 2
# Returns a numerical encoding of the categories; specifically,
# if len(categories) is 2,
#   a string : integer dictionary, where the integer is unique for each key and is 0 or 1 and the string is a category name
#       from categories
#
# a string : list dictionary, where the list is a unique one-hot vector and the string is a category name from categories
# Also returns a reverse of this dictionary where the keys are either ints or tuples of ints(one-hot) and the values
# are the category strings
def category_encoder(categories):
    if len(categories) == 2:
        return {categories[0]:0, categories[1]:1}, {0:categories[0], 1:categories[1]}
    else:
        str_to_onehot = {}
        onehot_to_str = {}
        for index, category in enumerate(categories):
            str_to_onehot[category] = [0] * len(categories)
            str_to_onehot[category][index] = 1
            onehot_to_str[tuple(str_to_onehot[category])] = category
        return str_to_onehot, onehot_to_str



# Returns a copy of data but with the category representations changed according to category_encoding
# category_encoding: a dictionary from string categories to category encodings (of any type)
# data: a list of string
# OR
# category_encoding: a dictionary from category encodings (int or tuple of int) to category strings
# data: a list of the same type as category_encoding's keys (int or tuple of int)
def categories_to_encoding(category_encoding, data):
    return [category_encoding[item] for item in data]




# gold_file_name: name of the csv file with a FileID column and a Category column; each row represents a file
# Returns a string:string dictionary of the form
# data filename : data category
def get_golds(gold_file_name):
    golds = pandas.read_csv(gold_file_name)
    return {row[1]['FileID']:row[1]['Category'] for row in golds.iterrows()}



# Reads dummy wav files from sample_wavs directory just as a sanity check and as a skeleton/example to hook
# everything up
# args: file reading args
# Returns: - a batched dataset of audio vectors
#          - a corresponding batched dataset of the vectors' file IDs
#          - a corresponding list of the vectors' categories in either binary or one-hot representation
#          - a dictionary of possible categories and their mappings to 0 or 1 if binary or one-hot lists if multiclass
def get_sample_data(args):
    #TODO: sample wav input filenames

    #Cerys: this is ok as long as there are no directories in sample_wavs
    all_sample_filenames = ["sample_wavs/"+fn for fn in os.listdir("sample_wavs")]

    #This returns a batched Tensorflow Dataset?
    sample_gold_batches = id_loader.id_decode_extract_and_batch(all_sample_filenames,
        batch_size=args.train_batch_size,
        #slice_len=args.data_slice_len,
        decode_fs=args.data_sample_rate,
        decode_num_channels=args.data_num_channels,
        decode_fast_wav=args.data_fast_wav,
        decode_parallel_calls=4,
        #slice_randomize_offset=False if args.data_first_slice else True,
        #slice_first_only=args.data_first_slice,
        #slice_overlap_ratio=0. if args.data_first_slice else args.data_overlap_ratio,
        #slice_pad_end=True if args.data_first_slice else args.data_pad_end,
        repeat=False, #Originally true in Donahue; I set it to False because repeat means create a structure where you "repeat the data indefinitely"
        shuffle=False, #Todo: switch to True
        shuffle_buffer_size=4096,
        prefetch_size=args.train_batch_size * 4,
        prefetch_gpu_num=args.data_prefetch_gpu_num)

    #print(sample_gold_batches)
    #sample_gold_batches = sample_gold_batches[:, :, 0] Donahue's code does this; not sure why, it may be an earlier version thing

    #Separate the audio data from the filenames
    batch_filenames = sample_gold_batches.map(lambda fn, audio: fn)
    batch_filenames = batch_filenames.map(tensor_basename)
    batch_audio_vectors = sample_gold_batches.map(lambda fn, audio: audio)

    #Change the filenames to string categories
    file_category_maps = get_golds("sample_file_info.csv")
    batch_categories = batch_filenames.map(lambda name: tensor_categories(name, file_category_maps))
    category_to_encoding, encoding_to_category = category_encoder(list(set(file_category_maps.values())))
    batch_encoded_categories = batch_categories.map(lambda category: tensor_encodings(category, category_to_encoding))


    return batch_audio_vectors, batch_filenames, batch_encoded_categories, category_to_encoding

#Tensorflow strings can't be used like normal Python strings; if you want to call a string function on them,
# you have to wrap operations in a
#function that takes a Numpy array and then apply it using numpy_func
def helper_basename(numpy_strings):
    result = [os.path.basename(filename) for filename in numpy_strings]
    if debug:
        print(numpy_strings)
        print(result)
    return np.array(result)



#Note: these two can be combined into one function because they do the same thing
def helper_categories(numpy_strings, file_category_maps):
    return np.array([file_category_maps[file.decode('utf-8')] for file in numpy_strings])
   # return np.apply_along_axis(lambda file: file_category_maps[file], 0, numpy_strings)
def helper_encodings(numpy_strings, category_encodings):
    return np.array([category_encodings[cat.decode('utf-8')] for cat in numpy_strings])
    #return np.apply_along_axis(lambda file: category_encodings[file], 0, numpy_strings)

def tensor_basename(tensor):
    return tf.numpy_function(helper_basename, [tensor], tf.string)

#Note: these two can be combined into one function because they do the same thing
def tensor_categories(tensor, file_category_maps):
    return tf.numpy_function(lambda string: helper_categories(string, file_category_maps),
                             [tensor], tf.string)
def tensor_encodings(tensor, category_encodings):
    return tf.numpy_function(lambda string: helper_categories(string, category_encodings),
                             [tensor], tf.int32)




#Returns an argument parser with the arguments from Donahue's WaveGan
def arguments():
    parser = argparse.ArgumentParser()

    parser.add_argument('mode', type=str, choices=['train', 'preview', 'incept', 'infer'])
    parser.add_argument('train_dir', type=str,
                        help='Training directory')

    data_args = parser.add_argument_group('Data')
    data_args.add_argument('--data_dir', type=str,
                           help='Data directory containing *only* audio files to load')
    data_args.add_argument('--data_sample_rate', type=int,
                           help='Number of audio samples per second')
    data_args.add_argument('--data_slice_len', type=int, choices=[16384, 32768, 65536],
                           help='Number of audio samples per slice (maximum generation length)')
    data_args.add_argument('--data_num_channels', type=int,
                           help='Number of audio channels to generate (for >2, must match that of data)')
    data_args.add_argument('--data_overlap_ratio', type=float,
                           help='Overlap ratio [0, 1) between slices')
    data_args.add_argument('--data_first_slice', action='store_true', dest='data_first_slice',
                           help='If set, only use the first slice each audio example')
    data_args.add_argument('--data_pad_end', action='store_true', dest='data_pad_end',
                           help='If set, use zero-padded partial slices from the end of each audio file')
    data_args.add_argument('--data_normalize', action='store_true', dest='data_normalize',
                           help='If set, normalize the training examples')
    data_args.add_argument('--data_fast_wav', action='store_true', dest='data_fast_wav',
                           help='If your data is comprised of standard WAV files (16-bit signed PCM or 32-bit float), use this flag to decode audio using scipy (faster) instead of librosa')
    data_args.add_argument('--data_prefetch_gpu_num', type=int,
                           help='If nonnegative, prefetch examples to this GPU (Tensorflow device num)')

    wavegan_args = parser.add_argument_group('WaveGAN')
    wavegan_args.add_argument('--wavegan_latent_dim', type=int,
                              help='Number of dimensions of the latent space')
    wavegan_args.add_argument('--wavegan_kernel_len', type=int,
                              help='Length of 1D filter kernels')
    wavegan_args.add_argument('--wavegan_dim', type=int,
                              help='Dimensionality multiplier for model of G and D')
    wavegan_args.add_argument('--wavegan_batchnorm', action='store_true', dest='wavegan_batchnorm',
                              help='Enable batchnorm')
    wavegan_args.add_argument('--wavegan_disc_nupdates', type=int,
                              help='Number of discriminator updates per generator update')
    wavegan_args.add_argument('--wavegan_loss', type=str, choices=['dcgan', 'lsgan', 'wgan', 'wgan-gp'],
                              help='Which GAN loss to use')
    wavegan_args.add_argument('--wavegan_genr_upsample', type=str, choices=['zeros', 'nn'],
                              help='Generator upsample strategy')
    wavegan_args.add_argument('--wavegan_genr_pp', action='store_true', dest='wavegan_genr_pp',
                              help='If set, use post-processing filter')
    wavegan_args.add_argument('--wavegan_genr_pp_len', type=int,
                              help='Length of post-processing filter for DCGAN')
    wavegan_args.add_argument('--wavegan_disc_phaseshuffle', type=int,
                              help='Radius of phase shuffle operation')

    train_args = parser.add_argument_group('Train')
    train_args.add_argument('--train_batch_size', type=int,
                            help='Batch size')
    train_args.add_argument('--train_save_secs', type=int,
                            help='How often to save model')
    train_args.add_argument('--train_summary_secs', type=int,
                            help='How often to report summaries')

    preview_args = parser.add_argument_group('Preview')
    preview_args.add_argument('--preview_n', type=int,
                              help='Number of samples to preview')

    incept_args = parser.add_argument_group('Incept')
    incept_args.add_argument('--incept_metagraph_fp', type=str,
                             help='Inference model for inception score')
    incept_args.add_argument('--incept_ckpt_fp', type=str,
                             help='Checkpoint for inference model')
    incept_args.add_argument('--incept_n', type=int,
                             help='Number of generated examples to test')
    incept_args.add_argument('--incept_k', type=int,
                             help='Number of groups to test')

    parser.set_defaults(
        data_dir='./sample_wavs',
        data_sample_rate=16000,
        data_slice_len=16384,
        data_num_channels=1,
        data_overlap_ratio=0.,
        data_first_slice=False,
        data_pad_end=False,
        data_normalize=False,
        data_fast_wav=False,
        data_prefetch_gpu_num=0,
        wavegan_latent_dim=100,
        wavegan_kernel_len=25,
        wavegan_dim=64,
        wavegan_batchnorm=False,
        wavegan_disc_nupdates=5,
        wavegan_loss='wgan-gp',
        wavegan_genr_upsample='zeros',
        wavegan_genr_pp=False,
        wavegan_genr_pp_len=512,
        wavegan_disc_phaseshuffle=2,
        train_batch_size=2, #TODO: 64, Changing this to 2 temporarily for testing
        train_save_secs=300,
        train_summary_secs=120,
        preview_n=32,
        incept_metagraph_fp='./eval/inception/infer.meta',
        incept_ckpt_fp='./eval/inception/best_acc-103005',
        incept_n=5000,
        incept_k=10)
    return parser

def train_cnn(wav_data, gold_data):
    model = cnn.create_model()
    model.fit(wav_data, gold_data)


if __name__ == "__main__":
    args = arguments().parse_args()
    audio, filenames, gold_labels, category_encodings = get_sample_data(args)
    #print(audio)
    print("Gold labels")
    for element in gold_labels:
        print(element)
    print("Category encodings")
    print(category_encodings)