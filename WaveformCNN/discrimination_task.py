import scipy
import scipy.spatial
import tensorflow as tf
from tensorflow import keras
import data_processing as data
debug = True

#Returns the cosine distance between the model's representation for
#stimuli1 and stimuli2.
#Has model predict the output for stimuli1 as input, then gets the activations
#at the layer named layer_name. These activations are the model's representation for stimuli1.
#Repeats the same procedure for stimuli2.
#Computes the cosine distance between the two representations.
#model should be a Keras Sequential model, and
# Stimuli1 and Stimuli2 should be valid input types for model
def get_cosine_distance(intermediate_model, stimuli1, stimuli2):
    stimuli1_rep = intermediate_model(stimuli1)
    stimuli2_rep = intermediate_model(stimuli2)
    if debug:
        print("Reps for stimuli")
        print(stimuli1_rep)
        print(stimuli2_rep)
        print("\n")

    return scipy.spatial.distance.cosine(stimuli1_rep, stimuli2_rep)

#Computes cosine similarity of each pair of stimuli in the file named stimuli_directory
#and returns the result as a dictionary of stimuli_1_filename, stimuli_2_filename: cosine distance
def run_task(model, stimuli_directory, stimuli_metadata_csv):
    #Load stimuli for an experiment
    batched_audio_vectors, \
    batched_filenames, \
    batched_encoded_categories, \
    category_encoding_map, encoding_category_map = data.get_data(stimuli_directory, stimuli_metadata_csv)

    stimuli_audio = batched_audio_vectors.unbatch()
    filenames = batched_filenames.unbatch() #Don't really care about categories(voiced/voiceless)
    #for the stimuli- kind of meaningless
    #Just care about stimuli identity (filename)

    stimuli = tf.data.Dataset.zip((filenames, stimuli_audio))

    #For each pair of stimuli, compute cosine distances
    stimuli = list(stimuli.as_numpy_iterator())
    pair_indices = []
    for i in range(len(stimuli)):
        for j in range(len(stimuli)):
            # Inefficient but working with small numbers of stimuli anyway
            if (i,j) not in pair_indices and (j,i) not in pair_indices:
                pair_indices.append((i,j))
    stimuli_pairs = [(stimuli[i], stimuli[j]) for i,j in pair_indices]
    stimuli_pair_distances = {}
    for index,pair in enumerate(stimuli_pairs):
        stimuli_pair_distances[pair_indices[index]] =\
            get_cosine_distance(model, pair[0], pair[1])

    stimuli_pair_distances = {(filenames[pair[0]],
                                         filenames[pair[1]]):
                                  stimuli_pair_distances[(pair)] for pair in pair_indices}

    return stimuli_pair_distances


if __name__ == "__main__":
    #Run parameters: model, experimental stimuli directories, results file name, hidden layer name
    model_save_name = "saved_models/trial_run_1000_tokens_converge"
    root = "../klatt_synthesis/experimental_stimuli/"
    stimuli_directory_names = [root+"f1_voicing_dur", root+"f1_closure_dur", root+"f0_voicing_dur", root+"f0_closure_dur"]
    stimuli_metadata_file_names = [directory_name+"/metadata.csv" for directory_name in stimuli_directory_names]
    stimuli_directory_names = [name+"/sounds" for name in stimuli_directory_names]
    results_file_name = "discrim_results/trial_run_1000_tokens_converge_discrim_results.txt"
    layer_name = "hidden_rep"



    # Layer activation extraction code based on
    # tutorial at https://keras.io/getting_started/faq/#how-can-i-obtain-the-output-of-an-intermediate-layer-feature-extraction
    # Get access to probing layer
    model = keras.models.load_model(model_save_name)
    intermediate_layer_model = keras.Model(inputs=model.input,
                                           outputs=model.get_layer(layer_name).output)

    #Get cosine distances for each pair of stimuli in each task and save in a list of pairs:
    # task name (same name as the directory for the stimuli), dictionary of stimuli filename pairs to cosine
    # distances
    tasks = []
    for index, directory_name in enumerate(stimuli_directory_names):
        stimuli_pair_distances = run_task(intermediate_layer_model, directory_name, stimuli_metadata_file_names[index])
        tasks.append((directory_name, stimuli_pair_distances))

    #Write cosine distances for each pair in each task to output file
    output_file = open(results_file_name, "w+")
    for task_name, stimuli_distances in tasks:
        output_file.write(task_name+"\n")
        for stimuli_pair in stimuli_distances:
            output_file.write(str(stimuli_pair)+"\t")
            output_file.write(str(stimuli_distances[stimuli_pair])+"\t")
            output_file.write("\n")
        output_file.write("\n\n")
    output_file.close()



