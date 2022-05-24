import librosa
import os
import numpy as np

wav_file_dir = "../../klatt_synthesis/dummy_sounds"
all_sample_filenames = [wav_file_dir+'/'+fn for fn in os.listdir(wav_file_dir)]
a_filenames = [wav_file for wav_file in all_sample_filenames if "a" in wav_file]
i_filenames = [wav_file for wav_file in all_sample_filenames if "i" in wav_file.split("/")[4]]
print(a_filenames[0], i_filenames[0])
vec_a = librosa.load(a_filenames[0])
vec_i = librosa.load(i_filenames[0])
print(vec_a[0])
print(vec_i[0])
print(np.array_equal(vec_a[0],vec_i[0]))