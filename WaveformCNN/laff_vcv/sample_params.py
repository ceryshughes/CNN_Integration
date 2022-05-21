import random
random.seed(1)

import compute_vcv_distributions
from compute_vcv_distributions import VcvToken
import statistics
import csv #todo: convert klatt parameters to csv


debug=True

#Extra closure voicing synthesis parameters
#These values are taken from the Kingston 2008 experimental stimuli values for the closure voicing set
constant_synth_params = {"f0TransitionDur": 0.055, #in seconds
                         "F1TransitionDur": 0.055,
                         "OtherFsTransitionDur": 0.04,
                         "VowelDur": 0.205,
                         "F1Closure": 150, #value of F1 during closure voicing, Hz
                         "f0Closure": 90, #value of f0 during closure voicing, Hz #todo: check these with John because they seem unintuitive
                         #Keep higher formants constant- I just care about relationship between closure+f0+F1
                         #Also, F5 is undefined for pretty much all of the corpus tokens under the standard formant settings
                         "F2steady":1150,
                         "F2offset":800,
                         "F3steady":2400,
                         "F3offset":1750,
                         "F4steady":3300,
                         "F4offset": 3300,#Do I even need to include the higher formants?
                         "F5offset":3850,
                         "F5steady": 3850
                         }

def normalize(tokens):
    #TODO
    return tokens


#Return a noisy sample from the distribution of VCV tokens in #tokens with a stop label of #label
#tokens: list of Vcv objects
#label: string
def generate_sample_vcv(tokens, label, frequency_stdevs, closure_dur_stdev, closure_voicing_stdev):
    #TODO: use v2 data?


    #Joint sample of values
    tok_indices = list(range(0, len(tokens)))
    sample_token = tokens[random.sample(tok_indices, 1)[0]]

    #Get closure voicing duration and add noise
    voicing = sample_token.stop.voicing_dur
    voicing += random.gauss(0, closure_voicing_stdev) #Can I measure variation for a non parameterized distribution?
    voicing = voicing if voicing > 0 else 0

    #Get closure duration and add noise
    closure_dur = sample_token.stop.closure_dur
    closure_dur += random.gauss(0, closure_dur_stdev)
    #If closure_dur becomes 0 from adding noise, set it back to the original
    if closure_dur <= 0:
        closure_dur = sample_token.stop.closure_dur

    #If closure voicing > closure duration, set them equal
    if voicing > closure_dur:
        voicing = closure_dur

    #Construct stop
    new_stop = compute_vcv_distributions.Stop(label,voicing,closure_dur)

    #Construct vowels
    vowel_quality = sample_token.vowel1.label
    new_v1 = compute_vcv_distributions.Vowel(vowel_quality)
    new_v2 = compute_vcv_distributions.Vowel(vowel_quality)
    for formant in new_v1.measurement_dict:
        steady_stdv = frequency_stdevs[vowel_quality][formant]["steady"]
        new_v1.measurement_dict[formant]["steady"] = sample_token.vowel1.measurement_dict[formant]["steady"]
        new_v1.measurement_dict[formant]["steady"] += random.gauss(0, steady_stdv)

        transit_stdv = frequency_stdevs[vowel_quality][formant]["transit"]
        new_v1.measurement_dict[formant]["transit"] = sample_token.vowel1.measurement_dict[formant]["transit"]
        new_v1.measurement_dict[formant]["transit"] += random.gauss(0, transit_stdv)
        if formant == 1 and new_v1.measurement_dict[formant]["transit"] < 90:
            print(vowel_quality, sample_token.vowel1.measurement_dict[formant]["transit"], transit_stdv)

    for formant in new_v2.measurement_dict:
        new_v2.measurement_dict[formant]["steady"] = new_v1.measurement_dict[formant]["steady"]
        new_v2.measurement_dict[formant]["transit"] = new_v1.measurement_dict[formant]["transit"]

    #Construct new token
    noisy_sampled_token = compute_vcv_distributions.VcvToken(sample_token.speaker, new_stop, new_v1, new_v2)

    return sample_token, noisy_sampled_token


#tokens: (string, Vcv object) pair
# where the string is the fileID for the Vcv object
# Outputs to out_file_name the fileIDs and stop labels of each token in tokens
def generate_stop_metadata_file(out_file_name, tokens):
    with open(out_file_name, 'w', newline='') as csvfile:
        fieldnames = ["FileID", "Category"]
        col_writer = csv.writer(csvfile)
        col_writer.writerow(fieldnames)
        writer = csv.DictWriter(csvfile,fieldnames=fieldnames)
        for token in tokens:
            file_id = token[0]
            values = token[1]
            writer.writerow({"FileID":file_id+".wav", "Category": values.stop.label})


#tokens: (string, Vcv object) pair
# where the string is the fileID for the Vcv object
# Outputs to out_file_name the fileIDs and stop labels of each token in tokens
def generate_klatt_parameter_file(out_file_name, tokens):
    with open(out_file_name, 'w', newline='') as csvfile:
        fieldnames = ["Name","VowelDur","ClosureDur","F1offset", "F1steady","F2offset", "F2steady",
                      "F3offset", "F3steady", "F4offset", "F4steady", "F5offset", "F5steady", "f0offset",
                      "f0steady", "f0TransitionDur", "F1TransitionDur", "OtherFsTransitionDur",
                      "F1Closure", "f0Closure", "ClosureVoicingDur"]
        col_writer = csv.writer(csvfile)
        col_writer.writerow(fieldnames)
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        for token in tokens:
            token_label = token[0]
            data = token[1]
            row = {"Name" : token_label,
                    "VowelDur": constant_synth_params["VowelDur"],
                    "ClosureDur" : data.stop.closure_dur,
                    "F1offset": data.vowel1.measurement_dict[1]["transit"],
                    "F1steady": data.vowel1.measurement_dict[1]["steady"],
                    "F2offset": constant_synth_params["F2offset"],
                    "F2steady": constant_synth_params["F2steady"],
                    "F3offset": constant_synth_params["F3offset"],
                    "F3steady": constant_synth_params["F3steady"],
                    "F4offset": constant_synth_params["F4offset"],
                    "F4steady": constant_synth_params["F4steady"],
                    "F5offset": constant_synth_params["F5offset"],
                    "F5steady": constant_synth_params["F5steady"],
                    "f0offset": data.vowel1.measurement_dict[0]["transit"],
                    "f0steady": data.vowel1.measurement_dict[0]["steady"],
                    "f0TransitionDur": constant_synth_params["f0TransitionDur"],
                    "F1TransitionDur": constant_synth_params["F1TransitionDur"],
                    "OtherFsTransitionDur":constant_synth_params["OtherFsTransitionDur"],
                    "F1Closure": constant_synth_params["F1Closure"],
                    "f0Closure": constant_synth_params["f0Closure"],
                    "ClosureVoicingDur": data.stop.voicing_dur
                   }
            writer.writerow(row)

#tokens: list of Vcv object
#Returns:
# a dict of number => vowel label (string) => parameter(string) => double for the noise range for each frequency value
# the noise range for closure duration (double) for stops
# the noise range for closure voicing duration (double) for stops
# informal note: I call this separately for voiced and voiceless stops, so I'm computing the variation for each
# of their distributions separately
def compute_noise_boundaries(tokens):
    # Calculate stdev for adding noise
    closure_dur_stdev = statistics.stdev([token.stop.closure_dur for token in tokens])/3
    closure_voicing_stdev = statistics.stdev([token.stop.voicing_dur for token in tokens])/3

    frequency_stdevs = {}
    for vowel in VcvToken.vowels:
        print(vowel, min([token.vowel1.measurement_dict[1]["steady"] for token in tokens if token.vowel1.label == vowel]))
        print(vowel,
              max([token.vowel1.measurement_dict[1]["steady"] for token in tokens if token.vowel1.label == vowel]))
        frequency_stdevs[vowel] = {
        0: {"steady": statistics.stdev([token.vowel1.measurement_dict[0]["steady"] for token in tokens if token.vowel1.label == vowel])/3,
            "transit": statistics.stdev([token.vowel1.measurement_dict[0]["transit"] for token in tokens if token.vowel1.label == vowel])/3},
        1: {"steady": statistics.stdev([token.vowel1.measurement_dict[1]["steady"] for token in tokens if token.vowel1.label == vowel])/3,
            "transit": statistics.stdev([token.vowel1.measurement_dict[1]["transit"] for token in tokens if token.vowel1.label == vowel])/3},
        2: {"steady": 0,
            "transit": 0},
        3: {"steady": 0,
            "transit": 0},
        4: {"steady": 0,  # statistics.stdev([token.vowel1.measurement_dict[4]["steady"] for token in tokens]),
            "transit": 0},  # statistics.stdev([token.vowel1.measurement_dict[4]["transit"] for token in tokens])},
        5: {"steady": 0,  # statistics.stdev([token.vowel1.measurement_dict[4]["steady"] for token in tokens]),
            "transit": 0}  # statistics.stdev([token.vowel1.measurement_dict[4]["transit"] for token in tokens])},
    }
    return frequency_stdevs, closure_dur_stdev, closure_voicing_stdev


if __name__ == "__main__":
    num_samples_voiced = 500
    num_samples_voiceless = 500
    metadata_fn = "sampled_stop_categories.csv"
    klatt_param_fn = "sampled_stop_klatt_params.csv"
    actual_token_fn = "pulse_voicing_token_measurements.csv"

    #Get distributions
    voiced_dist, voiceless_dist = compute_vcv_distributions.get_vcv_data()
    if debug:
        generate_klatt_parameter_file(actual_token_fn,[(token.vowel1.label+token.stop.label+token.speaker, token) for token in voiced_dist+voiceless_dist])


    #Randomly sample frequency and stop values
    sampled_data = []
    #Should I compute variation for voiced and voiceless separately, or together? For the purposes of adding noise?
    #I think if I want to be drawing noisy samples from each distribution separately, I should compute the
    #variation separately
    d_frequency_stdevs, d_closure_dur_stdev, d_closure_voicing_stdev = compute_noise_boundaries(voiced_dist)
    for index in range(num_samples_voiced):
        original, sample = generate_sample_vcv(voiced_dist, "voiced",
                                     d_frequency_stdevs, d_closure_dur_stdev, d_closure_voicing_stdev)
        sample_id = str(len(sampled_data)) + "_" + sample.speaker + "_" + original.stop.label + "_" + original.vowel1.label
        sampled_data.append((sample_id, sample))

    t_frequency_stdevs, t_closure_dur_stdev, t_closure_voicing_stdev = compute_noise_boundaries(voiceless_dist)
    for index in range(num_samples_voiceless):
        original, sample = generate_sample_vcv(voiceless_dist, "voiceless",
                                     t_frequency_stdevs, t_closure_dur_stdev, t_closure_voicing_stdev)
        sample_id = str(len(sampled_data)) + "_" + sample.speaker + "_" + original.stop.label + "_" + original.vowel1.label
        sampled_data.append((sample_id,sample))

    #Write metadata and Klatt parameter files
    generate_stop_metadata_file(metadata_fn, sampled_data)
    generate_klatt_parameter_file(klatt_param_fn, sampled_data)




