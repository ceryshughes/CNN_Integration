# CNN_Integration
A replication of the CNNs used in Donahue's WaveGAN discriminator (and motivated by Begus's application of WaveGAN to sound change) for the purposes of conducting probing analogous to human acoustic integration experiments, specifically those in Kingston et al (2008) for eventually implementing a model of Yang (2019)'s account of the contrast shift typology.


Python version used: 3.8

Required Python libraries:

* numpy
* tensorflow
* keras
* librosa
* pandas

For the VCV production data processing code,

* textgrid: https://github.com/kylebgorman/textgrid

* praat-parseltongue


Folders and scripts:

* WaveformCNN: Python code for processing sound data, definining and training the CNN, and running the discrimination task
* laff_vcv: folder for code for the processing LAFF VCV corpus
    * compute_vcv_distributions.py: extracts measurements from each real speech token
          * sample_params.py: creates synthesis parameters for the training data using the measurements from compute_vcv_distributions.py
	  * .xlsx files: synthesis parameters
	  * .csv files: mapping from filenames to category labels (e.g. voiced vs voiceless)
	  * laff_plots, laff_plots_pulse_voicing_new_closures: plots of LAFF measurement distributions distributions, each with a different measurement criterion 
  * discrim_results: output files from discrimination task
  * saved_models: all of the metadata(e.g. weight values) about models after training so they can be loaded later
  * cnn.py: code that defines CNN
  * id_loader.py: code modified from Donahue et al. that processes sound files into Tensorflow Datasets of vectors, but linked with their filenames
  * data_processing.py: code for mapping the filenames to category encodings  to make the output of id_loader interfaceable with model training
  * train_cnn.py: code that builds and trains a CNN given training data
  * discrim_trask.py: code that loads a model and probes its hidden layers for its perceptual distances, emulating the discrimination task used in the Garner paradigm

* klatt_synthesis: R code for using a table of synthesis parameters to generate Praat Klatt synthesis scripts 
    * praat_vcv_synthesis.R: generates Praat Klatt synthesis scripts from tabular synthesis parameters
    * run_klatt-scripts.sh: runs multiple Praat scripts
    * script folders: contain Praat scripts
    * sounds folders: contain Praat synthesized sounds
    * experimental stimuli: Praat scripts and sounds for the discrimination experiments

* laff_vcv_tokens_with_stops: the tokens in the LAFF production data containing a stop, annotated with TextGrids

* analysis/power_estimates.R (should rename this): R code for processing discrimination task results (todo: rename this!)


To train and save a CNN model:
    * train_cnn.py
To evaluate a CNN model's cosine distances between experimental stimuli:
    * discrim_task.py

Still working on: 
    * test_cnn.py - Adding unit testing 




Files and directories in WaveformCNN (more detail):

* cnn.py: Definition of the CNN architecture and training procedure as an extension of the Keras Model class, replicating Donahue's WaveGAN discriminator (although for a truly faithful representation, I still need to add gradient clipping to training)



* id_loader.py: Definition of functions for reading the audio data while maintaining file identity information, following Donahue's WaveGAN audio data reading in loader.py



* sample_wavs and sample_file_info: dummy data for debugging



* sample_data_processing.py: Code for processing the output of id_loader.py for the dummy data in sample_wavs and sample_file_info; once I'm confident in this working, I'll clean it up for real data
test_cnn.py: file for unit tests, not yet done



* scratch_files: unorganized snippets of code and notes from when I was figuring out how Donahue's WaveGAN code works



* venv: virtual environment information




Expected warnings:
* If you run this code on a machine without a GPU, you may get tensorflow warnings about a lack of GPU. These warnings are just making you aware of the lack of GPU connection and can be ignored.
* In the data processing code(id_loader.py and sample_data_processing.py), the Dataset class may output warnings about the Autograph (used for computing gradients) and optimization; since the Autograph/gradient computation is not necessary for this preprocessing, these warnings can be ignored.
* id_loader.py uses a legacy Tensor wrapper function (py_func) from Donahue that's replaced by a slightly different function in the newer version of Tensorflow; it's low priority for me to update it right now because it's still supported, so there will be a warning notifying you that it's an outdated function. 
