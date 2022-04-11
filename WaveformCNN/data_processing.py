#Data:
# -inputs are .wav files in a folder with ID names
# -gold labels are in a csv file with a FileID column and a Category column; each row represents a file

debug = False

import id_loader #From Donahue's WaveGan
import pandas
import os
import numpy as np
import tensorflow as tf

# categories: set of string with no duplicates and cardinality >= 2
# Returns a numerical encoding of the categories; specifically,
# if len(categories) is 2,
#   a string : double dictionary, where the float is unique for each key and is 0.0 or 1.0 and the string is a category name
#       from categories
#
# a string : list dictionary, where the list is a unique one-hot vector and the string is a category name from categories
# Also returns a reverse of this dictionary where the keys are either doubles or tuples of doubles(one-hot) and the values
# are the category strings
def category_encoder(categories):
    #if len(categories) == 2:
    #    return {categories[0]:0.0, categories[1]:1.0}, {0.0:categories[0], 1.0:categories[1]}
    #else:
        str_to_onehot = {}
        onehot_to_str = {}
        for index, category in enumerate(categories):
            str_to_onehot[category] = [0.0] * len(categories)
            str_to_onehot[category][index] = 1.0
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




def get_data(wav_file_dir, info_csv, batch_size= 64 if not debug else 2,
             decode_fs = 16000,
             fast_wav = False,
             shuffle = True,
             prefetch_gpu_num = 0):
    """ Generates objects from data files
    Args:
        -wav_file_dir: string name of directory where the wav files are stored(must contain only .wav files)
        -info_csv: a csv file with two columns, FileID and Category, that lists the category label for each file in wav_file_dir

        Processing args:
        batch size: size of batches in output
        decode_fs: sampling rate for audio in samples per second
        shuffle: True to shuffle the dataset order; False not to shuffle the dataset order (retains category information either way)
        prefetch_size: how much data to prefetch (?)
        prefetch_gpu_num: from Donahue, If nonnegative, prefetch examples to this GPU (Tensorflow device num)
    Returns: - a batched dataset of audio vectors (Tensorflow Dataset of int.32 vector with 65536 samples)
             - a corresponding batched dataset of the vectors' file IDs (Tensorflow Dataset of string vectors)
             - a corresponding list of the vectors' categories in either binary or one-hot representation (Tensorflow Dataset of either int.32 or vector of int.32)
          - a dictionary of possible categories and their mappings to 0 or 1 if binary or one-hot lists if multiclass
    """


    #Cerys: this is ok as long as there are no directories or non-wav-files in sample_wavs
    all_sample_filenames = [wav_file_dir+fn for fn in os.listdir(wav_file_dir)]

    #This returns a batched Tensorflow Dataset?
    sample_gold_batches = id_loader.id_decode_extract_and_batch(all_sample_filenames,
        batch_size=batch_size,
        decode_fs=decode_fs,
        decode_num_channels=1,
        decode_fast_wav=fast_wav,
        decode_parallel_calls=4,
        repeat=False, #Originally true in Donahue; I set it to False because repeat means create a structure where you "repeat the data indefinitely"
        shuffle=shuffle,
        shuffle_buffer_size=4096,
        prefetch_size=batch_size * 4,
        prefetch_gpu_num=prefetch_gpu_num)


    #Separate the audio data from the filenames
    batch_filenames = sample_gold_batches.map(lambda fn, audio: fn)
    batch_filenames = batch_filenames.map(tensor_basename)
    batch_audio_vectors = sample_gold_batches.map(lambda fn, audio: audio)

    #Change the filenames to string categories
    file_category_maps = get_golds(info_csv)
    batch_categories = batch_filenames.map(lambda name: tensor_categories(name, file_category_maps))
    if debug:
        for element in batch_categories:
            print("Category",element)
    category_to_encoding, encoding_to_category = category_encoder(list(set(file_category_maps.values())))
    batch_encoded_categories = batch_categories.map(lambda category: tensor_encodings(category, category_to_encoding))
    if debug:
        for element in batch_encoded_categories:
            print("Encoding",element)
    batch_encoded_categories = batch_encoded_categories.map(lambda x: tf.cast(x,dtype=tf.float32)) #Can't be integers, has to be floats for Keras


    return batch_audio_vectors, batch_filenames, batch_encoded_categories, category_to_encoding, encoding_to_category

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
                             [tensor], tf.double)









if __name__ == "__main__":
    audio, filenames, gold_labels, category_encodings, encoding_categories= get_data("sample_wavs", "sample_file_info.csv")
    #print(audio)
    print("Gold labels")
    for element in audio:
        print(element)
    for element in gold_labels:
        print(element)
    print("Category encodings")
    print(category_encodings)