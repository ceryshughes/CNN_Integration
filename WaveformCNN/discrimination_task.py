import scipy
import scipy.spatial
import tensorflow as tf
from tensorflow import keras
import data_processing as data
import sys
import csv
debug = True



class Task():
    #name: name of the task (string)
    #stimuli: list of (vector, category_encoding, rep) pairs
    #       where each pair has a string condition/category encoding
    #       and a vector corresponding to the audio of the stimuli
    #       and a vector corresponding to the model representation of the audio
    #encoding_categories: dictionary from one-hot encodings to categories (strings)
    #category_encodings: dictionary from categories(strings) to one-hot encodings
    #distances: dictionary of (string category, string category) => number (distance between stimuli of the categories)
    def __init__(self, name, stimuli = None, category_encodings = None, encoding_categories = None, distances = None):
        self.name = name
        self.stimuli = stimuli
        self.category_encodings = category_encodings
        self.encoding_categories = encoding_categories
        self.distances = distances

        #Get the varied cues used in stimuli categories based on
        #category names
        category_names = self.category_encodings.keys()
        self.cue_names = [string for string in category_names.split("_") if string != "0" and string != "1"]

    #Returns dictionary of cue:value read from stimulus_category(string of value_cue_value_cue...)
    def cue_values(self, stimulus_category):
        cats_vals = stimulus_category.split("_")
        cat_val_dict = {}
        index = 0
        while index < len(cats_vals) - 1:
            cat_val_dict[index+1] = cat_val_dict[index]
            index += 2
        return cat_val_dict



#Returns the cosine distance between the model's representation for
#stimuli1 and stimuli2.
#Has model predict the output for stimuli1 as input, then gets the activations
#at the layer named layer_name. These activations are the model's representation for stimuli1.
#Repeats the same procedure for stimuli2.
#Computes the cosine distance between the two representations.
#model should be a Keras Sequential model, and
# Stimuli1 and Stimuli2 should be valid input types for model
# def get_cosine_distance(intermediate_model, stimuli1, stimuli2):
#     stimuli1 = stimuli1[None,:] #Add batch dimension - batch of 1
#     stimuli2 = stimuli2[None,:]
#     if debug:
#         print("Stimuli input shapes")
#         print(stimuli1.shape)
#         print(stimuli2.shape)
#     stimuli1_rep = intermediate_model.predict(stimuli1)
#     stimuli2_rep = intermediate_model.predict(stimuli2)
#     if debug:
#         print("Reps for stimuli")
#         print(stimuli1_rep.shape)
#         print(stimuli2_rep.shape)
#         print("\n")
#
#     return scipy.spatial.distance.cosine(stimuli1_rep, stimuli2_rep)


#Computes cosine similarity of each pair of stimuli in the file named stimuli_directory
#and returns the data in a Task object
#Requires stimuli_directory be formatted as "...../task_name/sounds/"
def run_task(model, stimuli_directory, stimuli_metadata_csv):

    #Create task and name it by the experiment
    split_path = stimuli_directory.split("/")
    task_data = Task(name=split_path[len(split_path)-3])

    #Load stimuli for an experiment
    batched_cats_and_audio, \
    category_encoding_map, encoding_category_map = data.get_data(stimuli_directory, stimuli_metadata_csv)

    task_data.category_encodings = category_encoding_map
    task_data.encoding_categories = encoding_category_map
    stimuli = batched_cats_and_audio.unbatch()

    #Get model representation for each stimulus by calling model.predict
    #and adding a batch dimension with [None,:]
    list_stimuli = list(stimuli.as_numpy_iterator())
    list_stimuli_with_model_reps = []
    for stimulus in list_stimuli:
        audio = stimulus[0]
        label = stimulus[1]
        model_rep = model.predict(audio[None,:])
        stim_with_model_rep = (audio, label, model_rep)
        list_stimuli_with_model_reps.append(stim_with_model_rep)
    list_stimuli = list_stimuli_with_model_reps


    #stimuli = tf.data.Dataset.map(stimuli, lambda audio, label: (audio, label, model.predict(audio[None,:])))

    #For each pair of stimuli, compute cosine distances
    #Compute set of possible pairs
    pair_indices = []
    for i in range(len(list_stimuli)):
        for j in range(len(list_stimuli)):
            # Inefficient but working with small numbers of stimuli per task anyway
            if (i,j) not in pair_indices and (j,i) not in pair_indices and i!=j:
                pair_indices.append((i,j))
    stimuli_pairs = [(list_stimuli[i], list_stimuli[j]) for i,j in pair_indices]

    #compute cosine distances
    distances = {}
    for index,pair in enumerate(stimuli_pairs):
        stimulus1 = pair[0]
        stimulus2 = pair[1]
        category_pair = (encoding_category_map[tuple(stimulus1[1])], encoding_category_map[tuple(stimulus2[1])])
        stim1_rep = stimulus1[2]
        stim2_rep = stimulus2[2]
        distances[category_pair] = scipy.spatial.distance.cosine(stim1_rep, stim2_rep)

    task_data.distances = distances

    return task_data


#Writes results for each task in tasks (list of Task object) to file named output_fn
def write_output(output_fn, tasks):
    output_file = open(output_fn, "w+")
    for task in tasks:
        output_file.write(task.name + "\n")
        for stimuli_pair in task.distances:
            distance = task.distances[stimuli_pair]

            # Write stimuli categories and their distance
            output_file.write(stimuli_pair[0] + "\t" + stimuli_pair[1] + "\t")
            output_file.write(str(distance) + "\t")

            output_file.write("\n")
        output_file.write("\n\n")
    output_file.close()

#Each row corresponds to a pair of stimuli
#Each row has experiment name, cue values for Stim1, cue values for Stim2 (blanks for the cues that
#aren't manipulated in the experiment)
# diagonal?(1 for diagonal, 0 for not diagonal) and distance
def csv_write_output(output_fn, tasks):
    fields = ["Experiment","Distance", "Diagonal?"]
    cues = set().union(*[set(task.cue_names) for task in tasks]) #Get names of all the cue fields across tasks
    stim1_cues = ["stim1_"+cue_name for cue_name in cues]
    stim2_cues = ["stim2_"+cue_name for cue_name in cues]
    fields += stim1_cues
    fields+= stim2_cues

    with open(output_fn, 'w+', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fields)
        for task in tasks:
            for stimuli_pair in task.distances: #A row for each stimulus pair
                stim1 = stimuli_pair[0]
                stim2 = stimuli_pair[1]

                cue_values_stim1 = task.cue_values(stim1)
                cue_values_stim2 = task.cue_values(stim2)

                #compute if the stimulus pair is along the diagonal in the space
                diagonal = 1
                for cue in cue_values_stim1:
                    if cue_values_stim1[cue] == cue_values_stim2[cue]:
                        diagonal = 0

                #update the key names for the cue values so they can be added separately to the CSV
                formatted_cue_values_stim1 = {"stim1_"+name: value for name, value in cue_values_stim1}
                formatted_cue_values_stim2 = {"stim2_"+name: value for name, value in cue_values_stim2}

                distance = task.distances[stimuli_pair]
                pair_dict = {"Experiment": task.name, "Distance": distance,"Diagonal": diagonal}
                pair_dict.update(formatted_cue_values_stim1)
                pair_dict.update(formatted_cue_values_stim2)
                writer.writerow(pair_dict)





if __name__ == "__main__":
    seed_num = sys.argv[1]
    #Run parameters: model, experimental stimuli directories, results file name, hidden layer name
    model_save_name = "saved_models/saved_models/run_seed_"+seed_num
    root = "../klatt_synthesis/experimental_stimuli/"
    stimuli_directory_names = [root+"f1_voicing_dur",
                               root+"f1_closure_dur_low_f0", root+"f1_closure_dur_high_f0",
                               root+"f0_voicing_dur",
                               root+"f0_closure_dur_low_f1", root+"f0_closure_dur_high_f1"]
    stimuli_metadata_file_names = [directory_name+"/metadata.csv" for directory_name in stimuli_directory_names]
    stimuli_directory_names = [name+"/sounds/" for name in stimuli_directory_names]
    results_file_name = "discrim_results/run_seed_"+seed_num+"_discrim_results.txt"
    layer_name = "hidden_rep"



    # Layer activation extraction code based on
    # tutorial at https://keras.io/getting_started/faq/#how-can-i-obtain-the-output-of-an-intermediate-layer-feature-extraction
    # Get access to probing layer
    model = keras.models.load_model(model_save_name)
    intermediate_layer_model = keras.Model(inputs=model.input,
                                           outputs=model.get_layer(layer_name).output)
    if debug:
        intermediate_layer_model.summary()
    #Get cosine distances for each pair of stimuli in each task and save in a list of pairs:
    # task name (same name as the directory for the stimuli), dictionary of stimuli filename pairs to cosine
    # distances
    tasks = []
    for index, directory_name in enumerate(stimuli_directory_names):
        task_info = run_task(intermediate_layer_model, directory_name, stimuli_metadata_file_names[index])
        tasks.append(task_info)

    #Write cosine distances for each pair in each task to output file
    write_output(results_file_name, tasks)




