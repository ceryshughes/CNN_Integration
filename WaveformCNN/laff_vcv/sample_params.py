import compute_vcv_distributions
import random

#Noise margins
#TODO: look in literature for variation and JNDs, cf Lisa Davidson
closure_voicing_noise_ = 0.02 #seconds
closure_duration_noise_ = 0.02 #seconds
F1_noise_ = 50 #Hertz
f0_noise_ = 30 #Hertz


def normalize(tokens):
    #TODO
    return tokens

def generate_sample_vcv(tokens):
    tok_indices = list(range(0, len(tokens)))
    #Randomly sample closure voicing, + noise
    voicing = tokens[random.sample(tok_indices, 1)].stop.voicing_dur
    voicing += random.uniform(-1 * closure_voicing_noise_, closure_voicing_noise_)
    voicing = voicing if voicing > 0 else 0

    #Randomly sample closure duration, + noise
    closure_dur = tokens[random.sample(tok_indices, 1)].stop.closure_dur
    closure_dur += random.uniform(-1 * closure_duration_noise_, closure_duration_noise_)
    #If closure_dur = 0, set it to the minimum observed closure duration
    if closure_dur <= 0:
        closure_dur = min([token.stop.closure_dur for token in tokens])

    #If closure voicing > closure duration, set them equal
    if voicing > closure_dur:
        voicing = closure_dur

    #Randomly sample f0 steady and f0 transit (from the same token), + noise
    #TODO: update this for aggregated vowels
    f0_steady = tokens[random.sample(tok_indices, 1)].vowel1.measurement_dict[0]["steady"]
    f0_steady += random.uniform(-1 * f0_noise_, f0_noise_)
    #todo: check this is in a sensible range (ie > some small number) - it should be, depending on the noise range
    f0_transit = tokens[random.sample(tok_indices, 1)].vowel1.measurement_dict[0]["transit"]
    f0_transit += random.uniform(-1 * f0_noise_, f0_noise_)

    #Randomly sample f1 steady and f1 transit (from the same token), + noise
    # TODO: update this for aggregated vowels
    F1_steady = tokens[random.sample(tok_indices, 1)].vowel1.measurement_dict[1]["steady"]
    F1_steady += random.uniform(-1 * F1_noise_, F1_noise_)
    # todo: check this is in a sensible range (ie > some small number) - it should be, depending on the noise range
    F1_transit = tokens[random.sample(tok_indices, 1)].vowel1.measurement_dict[1]["transit"]
    F1_transit += random.uniform(-1 * F1_noise_, F1_noise_)

    return




if __name__ == "__main__":
    num_samples_voiced = 500
    num_samples_voiceless = 500

    #Get distributions
    voiced_dist, voiceless_dist = compute_vcv_distributions.get_vcv_data()


#TODO: aggregate vowel data

#Randomly sample f0 steady, f0 transit, f1 steady, f1 transit (higher formants? not independent?), closure duration, closure voicing duration
#from either voiced or voiceless distributions


#Add small random noise value


#Write ID as name to Klatt parameter table file



#Write ID and label to the metadata table file