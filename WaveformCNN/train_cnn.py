# Program for loading in categorized wavfile data and training a CNN
from numpy.random import seed
seed(1)
from tensorflow import random
random.set_seed(2)

import numpy as np
import data_processing as data
import cnn
import tensorflow as tf


debug = True

#todo: take command line arguments
wavfile_directory = "../klatt_synthesis/sounds_100/"# "sample_wavs/"#
label_csv_file = "laff_vcv/sampled_stop_categories_100.csv"# "sample_file_info.csv"#
num_epochs = 1000 #todo: What should this be? Donahue's method - inception score- doesn't transfer here because it's for GAN productions
model_save_path = "saved_models/trial_run_100_tokens_converge_2"




if __name__ == "__main__":
    #Load in data
    print("Loading in data from directory", wavfile_directory, "with category-labeling csv file", label_csv_file)
    batched_audio_vectors, \
    batched_filenames,\
    batched_encoded_categories,\
    category_encoding_map, encoding_category_map = data.get_data(wavfile_directory, label_csv_file)

    if debug:
        print("Categories are ", category_encoding_map.keys())
        print("Audio Dataset", batched_audio_vectors)
        print("Gold Dataset", batched_encoded_categories)
        for element in batched_encoded_categories:
            print("Label",element)
        index = 0
        for element in batched_audio_vectors:
            print("Audio", element, element.shape)
            if index > 1:
                break

    if debug:
        saved_model = tf.keras.models.load_model('saved_models/trial_run_100_tokens_converge_2')
        y_pred = np.array(saved_model.predict(batched_audio_vectors))
        y_pred = np.round(y_pred)
        print(y_pred)
        print(np.array(batched_encoded_categories))
        exit()
    #Set up and train model
    print("Setting up the CNN categorizer")
    cnn_model = cnn.create_model(len(category_encoding_map.keys()))
    print("Training the CNN categorizer")
    #This callback ends training when the metric it's monitoring stops changing by more than "delta"
    #Because the loss doesn't decrease on every single epoch (not fully batch, and stochasticity in gradient
    #descent), "patience" gives the model a chance to run for a few more epochs before properly deciding to stop
    #todo: the delta value I pick is somewhat arbitrary; in my ML education it's always been arbitrary, but
    #maybe I should check the literature to see if there's a more principled way to decide, e.g. by seeing
    #how much loss usually changes for this task+model
    converge_callback = tf.keras.callbacks.EarlyStopping(monitor='loss', min_delta = 0.0001, patience=30)
    cnn_model.fit(x=tf.data.Dataset.zip((batched_audio_vectors, batched_encoded_categories)), epochs=num_epochs,
                  callbacks = [converge_callback])

    print("Saving model to ", model_save_path)
    cnn_model.save(model_save_path)





