#Program to define the architecture of a simple CNN for multiclass classification of waveforms
#based on Donahue's wavegan but updated to newer version of Tensorflow
#Also provides a training function
#Instead of the final layer being passed through a logistic function as in WaveGan,
#I pass it through a softmax function so that more than 2 categories could be learned.
#Also, unlike Donahue, I do not do weight clipping (to be added later).
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
debug = False

#Architecture of a CNN from the discriminator model of Donahue's WaveGan.
class WaveCNN():

    # Kernel len: size of kernel window for convolution
    # dim: Number of output filters in the first layer of convolution (will be scaled up/down in other layers)
    # num_classes: length of output vectors
    #Initializes self.model, a replication of WaveGan's CNN discriminator model
    #The last hidden layer can be accessed with the name "hidden_rep"
    def __init__(self, kernel_len=32, dim=64, use_batchnorm=True, name="cnn", num_classes=2):
        # TODO: batch normalization training vs inference?
        # TODO: slice_len?
        self.model = tf.keras.Sequential()

        # The tensorflow v1 code from Donahue doesn't specify the kernel initializer; in v1, the default is
        # None and in v2, the default is Glorot Uniform(not sure what Glorot is). v1 doesn't specify what
        # None as the initializer does; is it uniform? Since I don't know what v1 is doing, I'll just use
        # the default in v2 for now.
        # Layer 0
        # [16384, 1] -> [4096, 64]
        self.model.add(layers.Conv1D(dim, kernel_len,strides=4,padding="same"))
        if use_batchnorm:
            self.model.add(layers.BatchNormalization())
        self.model.add(layers.LeakyReLU(alpha=0.2))

        # Layer 1
        # [4096, 64] -> [1024, 128]
        self.model.add(layers.Conv1D(dim * 2, kernel_len, strides=4, padding="same"))
        if use_batchnorm:
            self.model.add(layers.BatchNormalization())
        self.model.add(layers.LeakyReLU(alpha=0.2))

        # Layer 2
        # [1024, 128] -> [256, 256]
        self.model.add(layers.Conv1D(dim*4,kernel_len,strides=4, padding="same"))
        if use_batchnorm:
             self.model.add(layers.BatchNormalization())
        self.model.add(layers.LeakyReLU(alpha=0.2))

        # Layer 3
        # [256, 256] -> [64, 512]
        self.model.add(layers.Conv1D(dim * 8, kernel_len, strides=4, padding="same"))
        if use_batchnorm:
            self.model.add(layers.BatchNormalization())
        self.model.add(layers.LeakyReLU(alpha=0.2))

        # Layer 4
        # [64, 512] -> [16, 1024]
        self.model.add(layers.Conv1D(dim * 16, kernel_len, strides=4, padding="same"))
        if use_batchnorm:
            self.model.add(layers.BatchNormalization())
        self.model.add(layers.LeakyReLU(alpha=0.2))

        # Layer 5
        # [64, 512] -> [16, 1024]
        self.model.add(layers.Conv1D(dim * 32, kernel_len, strides=2, padding="same"))
        if use_batchnorm:
            self.model.add(layers.BatchNormalization())
        self.model.add(layers.LeakyReLU(alpha=0.2))

        # slice_len in original Donahue code? He has 2 extra layers depending on what slice_len is...?
        # Layer 5
        # [16, 1024] -> [
        # Donahue names this downconv but this isn't really downconvolution...?
        # self.downconv_5 = tf.keras.layers.Conv1d(dim * 32, kernel_len, 2, padding="same")
        # self.activ_5 = tf.keras.layers.LeakyReLU(alpha = 0.2)

        # Flatten - in the Donahue code this is to batch_size x -1 (ie a 1D vector for each item in the batch)
        # Since I'm not messing with batch sizes in this architecture class (I think...) I suppose I flatten to
        # just 1D, so shape -1?
        self.model.add(layers.Reshape((-1,), name="hidden_rep"))#,name="hidden_rep"))

        # Combine features into output later
        self.model.add(layers.Dense(num_classes))

        self.model.add(layers.Softmax())
        # Donahue *says* this is connected to a single logit but doesn't use an activation function,
        # and the tensorflow default is linear. It appears he puts the interpretation as probability
        # into training, not the architecture definition. To simplify getting all of the shapes to be compatible,
        # I'm adding the softmax in the architecture instead.















#Set up model, set up its training parameters, and expose with a function
#num_classes: number of categories for the classifier
def create_model(num_classes):
    model = WaveCNN(num_classes=num_classes).model
    #Learning rate, beta1, and clipping values from Donahue
    model.compile(optimizer = tf.keras.optimizers.Adam(learning_rate=2e-4, beta_1=0.5, clipvalue=0.01), loss = 'categorical_crossentropy',
                metrics=["accuracy"])
    return model


#Example: Create a model and train it using initial Korean stop data from speakers in the 30-40 age range
if __name__ == "__main__":
    cnn_model = WaveCNN().model
    cnn_model.build((2,8192,1))
    cnn_model.summary()
    Y = []  # TODO: plug in data with original labels
    X = []  #TODO: plug in data with loader.py

    num_epochs = 1000 #In wavegan, this is determined by the inception score
    #train(cnn_model, X, Y, num_epochs)
