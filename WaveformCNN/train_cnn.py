# Program for loading in categorized wavfile data and training a CNN
import data_processing as data
import cnn
import tensorflow as tf

debug = True

#todo: take command line arguments
wavfile_directory = "sample_wavs/"
label_csv_file = "sample_file_info.csv"
input_length = 16384 #Following Donahue
num_epochs = 10 #todo: What should this be? Donahue's method - inception score- doesn't transfer here
model_save_path = "saved_models/test123"


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
        for element in batched_audio_vectors:
            print("Audio", element)

    #Set up and train model
    print("Setting up the CNN categorizer")
    cnn_model = cnn.create_model(len(category_encoding_map.keys()))
    print("Training the CNN categorizer")
    cnn_model.fit(x=tf.data.Dataset.zip((batched_audio_vectors, batched_encoded_categories)), epochs=num_epochs)

    print("Saving model to ", model_save_path)
    cnn_model.save(model_save_path)




