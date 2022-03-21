# CNN_Integration
A replication of the CNNs used in Donahue's WaveGAN discriminator (and motivated by Begus's application of WaveGAN to sound change) for the purposes of conducting probing analogous to human acoustic integration experiments, specifically those in Kingston et al (2008).


Files and directories in WaveformCNN:
cnn.py: Definition of the CNN architecture and training procedure as an extension of the Keras Model class, replicating Donahue's WaveGAN discriminator (although for a truly faithful representation, I still need to add gradient clipping to training)

id_loader.py: Definition of functions for reading the audio data while maintaining file identity information, following Donahue's WaveGAN audio data reading in loader.py

sample_wavs and sample_file_info: dummy data for debugging

sample_data_processing.py: Code for processing the output of id_loader.py for the dummy data in sample_wavs and sample_file_info; once I'm confident in this working, I'll clean it up for real data
test_cnn.py: file for unit tests, not yet done

scratch_files: unorganized snippets of code and notes from when I was figuring out how Donahue's WaveGAN code works

venv: virtual environment information




Expected warnings:
-If you run this code on a machine without a GPU, you may get tensorflow warnings about a lack of GPU. These warnings are just making you aware of the lack of GPU connection and can be ignored in this case.
-In the data processing code(id_loader.py and sample_data_processing.py), the Dataset class may output warnings about the Autograph (used for computing gradients) and optimization; since the Autograph/gradient computation is not necessary for this preprocessing, these warnings can be ignored.
-id_loader.py uses a legacy Tensor wrapper function (py_func) from Donahue that's replaced by a slightly different function in the newer version of Tensorflow; it's low priority for me to update it right now, so there will be a warning notifying you that it's an outdated function.