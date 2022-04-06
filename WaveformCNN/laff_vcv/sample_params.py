import compute_vcv_distributions
import random
import statistics



def normalize(tokens):
    #TODO
    return tokens


#Return a noisy sample from the distribution of VCV tokens in #tokens with a stop label of #label
##tokens: list of Vcv objects
#label: string
def generate_sample_vcv(tokens, label):

    #Calculate stdev for adding noise
    closure_dur_stdev = statistics.stdev([token.stop.closure_dur for token in tokens])
    closure_voicing_stdev = statistics.stdev([token.stop.voicing_dur for token in tokens])

    frequency_stdevs = {
        0: {"steady": statistics.stdev([token.v1.measurement_dict[0]["steady"] for token in tokens]),
            "transit":statistics.stdev([token.v1.measurement_dict[0]["transit"] for token in tokens])},
        1: {"steady": statistics.stdev([token.v1.measurement_dict[1]["steady"] for token in tokens]),
            "transit": statistics.stdev([token.v1.measurement_dict[1]["transit"] for token in tokens])},
        2: {"steady": statistics.stdev([token.v1.measurement_dict[2]["steady"] for token in tokens]),
            "transit": statistics.stdev([token.v1.measurement_dict[2]["transit"] for token in tokens])},
        3: {"steady": statistics.stdev([token.v1.measurement_dict[3]["steady"] for token in tokens]),
            "transit": statistics.stdev([token.v1.measurement_dict[3]["transit"] for token in tokens])},
        4: {"steady": statistics.stdev([token.v1.measurement_dict[4]["steady"] for token in tokens]),
            "transit": statistics.stdev([token.v1.measurement_dict[4]["transit"] for token in tokens])},
        5: {"steady": statistics.stdev([token.v1.measurement_dict[4]["steady"] for token in tokens]),
            "transit": statistics.stdev([token.v1.measurement_dict[4]["transit"] for token in tokens])},
    }
    #TODO: use v2 data?


    #Joint sample of values
    tok_indices = list(range(0, len(tokens)))
    sample_token = tokens[random.sample(tok_indices, 1)]

    #Get closure voicing duration and add noise
    voicing = sample_token.stop.voicing_dur
    voicing += random.uniform(-1 * closure_voicing_stdev, closure_voicing_stdev) #Can I measure variation for a non parameterized distribution?
    voicing = voicing if voicing > 0 else 0

    #Get closure duration and add noise
    closure_dur = sample_token.stop.closure_dur
    closure_dur += random.uniform(-1 * closure_dur_stdev, closure_dur_stdev)
    #If closure_dur becomes 0 from adding noise, set it back to the original
    if closure_dur <= 0:
        closure_dur = sample_token.stop.closure_dur

    #If closure voicing > closure duration, set them equal
    if voicing > closure_dur:
        voicing = closure_dur

    #Construct stop
    new_stop = compute_vcv_distributions.Stop(label,voicing,closure_dur)

    #Construct vowels
    new_v1 = compute_vcv_distributions.Vowel(sample_token.vowel1.label)
    new_v2 = compute_vcv_distributions.Vowel(sample_token.vowel2.label)
    for formant in new_v1.measurement_dict:
        steady_stdv = frequency_stdevs[formant]["steady"]
        new_v1.measurement_dict[formant]["steady"] = sample_token.vowel1.measurement_dict[formant]["steady"]
        new_v1.measurement_dict[formant]["steady"] += random.uniform(-1 * steady_stdv, steady_stdv)

        transit_stdv = frequency_stdevs[formant]["transit"]
        new_v1.measurement_dict[formant]["transit"] = sample_token.vowel1.measurement_dict[formant]["transit"]
        new_v1.measurement_dict[formant]["transit"] += random.uniform(-1 * transit_stdv, transit_stdv)

    for formant in new_v2.measurement_dict:
        new_v2.measurement_dict[formant]["steady"] = new_v1.measurement_dict[formant]["steady"]
        new_v2.measurement_dict[formant]["transit"] = new_v1.measurement_dict[formant]["steady"]

    #Construct new token
    sampled_token = compute_vcv_distributions.VcvToken(sample_token.speaker, new_stop, new_v1, new_v2)

    return sampled_token

def generate_metadata_file(out_file_name, tokens):
    return

def generate_klatt_parameter_file(out_file_name, tokens):
    return


if __name__ == "__main__":
    num_samples_voiced = 500
    num_samples_voiceless = 500

    #Get distributions
    voiced_dist, voiceless_dist = compute_vcv_distributions.get_vcv_data()

    #Randomly sample frequency and stop values
    sampled_voiced_data = []
    for index in range(num_samples_voiced):
        sample = generate_sample_vcv(voiced_dist, "voiced")
        sample_id = str(index) + "_" + sample.speaker
        sampled_voiced_data.append((sample_id, sample))
    sampled_voiceless_data = []
    for index in range(num_samples_voiceless):
        sample = generate_sample_vcv(voiceless_dist, "voiceless")
        sample_id = str(index) + "_" + sample.speaker
        sampled_voiceless_data.append((sample_id,sample))






#Write ID as name to Klatt parameter table file



#Write ID and label to the metadata table file