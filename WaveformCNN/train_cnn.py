# Program for loading in categorized wavfile data and training a CNN
from numpy.random import seed
seed(1) #There's randomness in the importing of these libraries, so you have to set the seed early
from tensorflow import random
random.set_seed(2)

import numpy as np
import data_processing as data
import cnn #scratch_cnn as cnn
import tensorflow as tf

import sys

#Program to train and save a CNN voiced vs voiceless stop categorizer.
#Command line arguments: 1st: random seed (number)
# Second: name to save model to under saved_models (string)
# Third: name of directory containing sound data (end with /)
# Fourth: name of stop category information csv file
seed(int(sys.argv[1]))  #Reset seed to user specification
random.set_seed(int(sys.argv[1]))

debug = False


wavfile_directory = sys.argv[3] #"../klatt_synthesis/sounds/"# "sample_wavs/"#
label_csv_file = sys.argv[4]#"laff_vcv/sampled_stop_categories.csv"# "sample_file_info.csv"#
num_epochs = 10 #todo: What should this be? Donahue's method - inception score- doesn't transfer here because it's for GAN productions
model_save_path = "saved_models/"+sys.argv[2] #Model name




if __name__ == "__main__":
    #Load in data
    print("Loading in data from directory", wavfile_directory, "with category-labeling csv file", label_csv_file)
    training_data,\
    category_encoding_map, encoding_category_map = data.get_data(wavfile_directory, label_csv_file)

    print(training_data)
    #exit()


    batched_encoded_categories = training_data.map(lambda category, audio: category)
    batched_audio_vectors = training_data.map(lambda category, audio: audio)
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
        saved_model = tf.keras.models.load_model('saved_models/trial_run_1000_tokens_converge')
        y_pred = np.array(saved_model.predict(batched_audio_vectors))
        print(y_pred)
        print(element for element in np.array(batched_encoded_categories))
        ac = tf.keras.metrics.CategoricalAccuracy()
        ac.update_state(tf.convert_to_tensor(np.array(batched_encoded_categories)), y_pred)
        print(ac.result().numpy())
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
    converge_callback = tf.keras.callbacks.EarlyStopping(monitor='loss', min_delta = 0.001, patience=30) #Stop training condition  #todo: get rid of this magic number. 16 is number of batches per epoch, 10 is number of epochs

    #Save model after each epoch just in case training gets interrupted
    checkpoint_callback = tf.keras.callbacks.ModelCheckpoint(model_save_path, save_freq = "epoch")

    cnn_model.fit(training_data, epochs=num_epochs,
                  callbacks = [converge_callback, checkpoint_callback])



    print("Saving model to ", model_save_path)
    cnn_model.save(model_save_path)





