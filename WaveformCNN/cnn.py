#Program to define the architecture of a simple CNN for multiclass classification of waveforms
#based on Donahue's wavegan but updated to newer version of Tensorflow
#Also provides a training function
#Instead of the final layer being passed through a logistic function as in WaveGan,
#I pass it through a softmax function so that more than 2 categories could be learned.
#Also, unlike Donahue, I do not do weight clipping (to be added later).
import tensorflow as tf
debug = True

#Architecture of a CNN from the discriminator model of Donahue's WaveGan.
class WaveCNN(tf.keras.Model):
    #Kernel len: size of kernel window for convolution
    #dim: Number of output filters in the first layer of convolution (will be scaled up/down in other layers)
    #num_classes: length of output vectors
    def __init__(self, kernel_len=25, dim=64,use_batchnorm=True, name="cnn", num_classes=2):
        #TODO: batch normalization training vs inference?
        #TODO: slice_len?
        super(WaveCNN, self).__init__(name=name)


        self.use_batchnorm = use_batchnorm
        if self.use_batchnorm:
            self.batchnorm = tf.keras.layers.BatchNormalization()


        #The tensorflow v1 code from Donahue doesn't specify the kernel initializer; in v1, the default is
        #None and in v2, the default is Glorot Uniform(not sure what Glorot is). v1 doesn't specify what
        #None as the initializer does; is it uniform? Since I don't know what v1 is doing, I'll just use
        #the default in v2 for now.
        # Layer 0
        # [16384, 1] -> [4096, 64]
        self.downconv_0 = tf.keras.layers.Conv1D(dim, kernel_len,4,padding="same")
        self.activ_0 = tf.keras.layers.LeakyReLU(alpha=0.2)

        # Layer 1
        # [4096, 64] -> [1024, 128]
        self.downconv_1 = tf.keras.layers.Conv1D(dim*2, kernel_len,4, padding="same")
        self.activ_1 = tf.keras.layers.LeakyReLU(alpha=0.2)

        # Layer 2
        # [1024, 128] -> [256, 256]
        self.downconv_2 = tf.keras.layers.Conv1D(dim*4,kernel_len,4, padding="same")
        self.activ_2 = tf.keras.layers.LeakyReLU(alpha=0.2)

        # Layer 3
        # [256, 256] -> [64, 512]
        self.downconv_3 = tf.keras.layers.Conv1D(dim * 8, kernel_len, 4, padding="same")
        self.activ_3 = tf.keras.layers.LeakyReLU(alpha=0.2)

        # Layer 4
        # [64, 512] -> [16, 1024]
        self.downconv_4 = tf.keras.layers.Conv1D(dim * 16, kernel_len, 4, padding="same")
        self.activ_4 = tf.keras.layers.LeakyReLU(alpha=0.2)

        #slice_len in original Donahue code? He has 2 extra layers depending on what slice_len is...?
        # Layer 5
        # [16, 1024] -> [
        #Donahue names this downconv but this isn't really downconvolution...?
        # self.downconv_5 = tf.keras.layers.Conv1d(dim * 32, kernel_len, 2, padding="same")
        # self.activ_5 = tf.keras.layers.LeakyReLU(alpha = 0.2)

        #Flatten - in the Donahue code this is to batch_size x -1 (ie a 1D vector for each item in the batch)
        #Since I'm not messing with batch sizes in this architecture class (I think...) I suppose I flatten to
        #just 1D, so shape -1?
        self.flatten = tf.keras.layers.Reshape((1,-1))

        # Combine features into output later
        self.dense = tf.keras.layers.Dense(num_classes)

        self.activ_out = tf.keras.layers.Softmax()
        #Donahue *says* this is connected to a single logit but doesn't use an activation function,
        #and the tensorflow default is linear. It appears he puts the interpretation as probability
        #into training, not the architecture definition. To simplify getting all of the shapes to be compatible,
        # I'm adding the softmax in the architecture instead.



    def call(self, inputs):
        if self.use_batchnorm:
            batchnorm = self.batchnorm #If batchnorm, use a normalizing function
        else:
            batchnorm = lambda x: x #If no batchnorm, just return the input

        #Put input through the network
        if debug:
            print(inputs.shape)
        output = self.activ_0(batchnorm(self.downconv_0(inputs)))
        if debug:
            print(output.shape)
        output = self.activ_1(batchnorm(self.downconv_1(output)))
        if debug:
            print(output.shape)
        output = self.activ_2(batchnorm(self.downconv_2(output)))
        if debug:
            print(output.shape)
        output = self.activ_3(batchnorm(self.downconv_3(output)))
        if debug:
            print(output.shape)
        output = self.activ_4(batchnorm(self.downconv_4(output)))
        #output = self.activ_5(batchnorm(self.downconv_5(output)))
        output = self.flatten(output)
        output = self.dense(output) #Donahue doesn't use batchnorm for the output layer
        #for the discriminator?
        output = self.activ_out(output)
        return output

#Loss function computation for training
#target_y: the gold output
#predicted_y: the output predicted by the model
#Returns the softmax crossentropy loss
# def softmax_crossent_loss(target_y, predicted_y):
#     return tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits(logits=target_y, labels=predicted_y))

# # Updates model's weights with an Adam optimizer with a beta1 of 0.5
# # model: a Keras/tensorflow model
# # x: training inputs
# # y: training outputs
# # num_epochs: number of training steps
# # learning_rate: step size as defined in Adam optimization
# def train(model, x, y, num_epochs, learning_rate=2e-4):
#     optimizer = tf.keras.optimizers.Adam(learning_rate=learning_rate,beta1=0.5)
#     model_vars = model.trainable_variables
#     for epoch in range(num_epochs):
#         train_op = optimizer.minimize(lambda: softmax_crossent_loss(target_y=y, predicted_y=model(x)),var_list=model_vars)
#

#Instead of the above training code, use the built-in compile and specify the options there
#Expose with a function: create_model
def create_model(num_classes):
    model = WaveCNN(num_classes=num_classes)
    #Learning rate, beta1, and clipping values from Donahue
    model.compile(optimizer = tf.keras.optimizers.Adam(learning_rate=2e-4, beta_1=0.5, clipvalue=0.01), loss = 'categorical_crossentropy')
    return model


#Example: Create a model and train it using initial Korean stop data from speakers in the 30-40 age range
if __name__ == "__main__":
    cnn_model = WaveCNN()
    cnn_model.build((2,16384,1))
    cnn_model.summary()
    Y = []  # TODO: plug in data with original labels
    X = []  #TODO: plug in data with loader.py

    num_epochs = 1000 #In wavegan, this is determined by the inception score
    #train(cnn_model, X, Y, num_epochs)
