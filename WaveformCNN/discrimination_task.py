import scipy
import scipy.spatial
import tensorflow
from tensorflow import keras

#Returns the cosine distance between the model's representation for
#stimuli1 and stimuli2.
#Has model predict the output for stimuli1 as input, then gets the activations
#at the layer named layer_name. These activations are the model's representation for stimuli1.
#Repeats the same procedure for stimuli2.
#Computes the cosine distance between the two representations.
#Layer activation extraction code based on # From tutorial at https://keras.io/getting_started/faq/#how-can-i-obtain-the-output-of-an-intermediate-layer-feature-extraction
#model should be a Keras Sequential model, and
# Stimuli1 and Stimuli2 should be valid input types for model, and
# layer_name should be the string name of one of the layers in the model
def get_cosine_distance(model, layer_name, stimuli1, stimuli2):
    intermediate_layer_model = keras.Model(inputs=model.input,
                                           outputs=model.get_layer(layer_name).output)
    stimuli1_rep = intermediate_layer_model(stimuli1)
    stimuli2_rep = intermediate_layer_model(stimuli2)

    return scipy.spatial.distance.cosine(stimuli1_rep, stimuli2_rep)