import textgrid
import parselmouth
import os
import matplotlib.pyplot as plt
import math

debug = False

class VcvToken:
    def __init__(self, speaker, stop, vowel1, vowel2):
        self.speaker = speaker #String speaker label
        #todo: should probably save token # too so I can go back and look at recording if I ever need to
        self.stop = stop #Stop object
        self.vowel1 = vowel1 #Vowel object for first vowel
        self.vowel2 = vowel2 #Vowel object for second vowel


class Vowel:
    def __init__(self, label):
        self.label = label #String label
        self.measurement_dict = {
            # steady: during the part of the vowel away from the closure
            # transit: the part of the vowel close to the closure
            # frequency measurements in Hz
            0: {"steady": 0, "transit":0}, #f0
            1: {"steady": 0, "transit":0}, #F1
            2: {"steady": 0, "transit":0}, #F2
            3: {"steady": 0,"transit":0}, #F3
            4:{"steady": 0, "transit":0}, #F4
            5:{"steady": 0, "transit":0} #F5
        } #Making these integers --> might as well be a list, but
        # I haven't decided whether I want the keys to be integers or strings


class Stop:
    def __init__(self, label, voicing_dur, closure_dur):
        self.voicing_dur = voicing_dur #float dur, in seconds
        self.label = label #String label
        self.closure_dur = closure_dur #float dur, in seconds

# grid_file_name: the name of a Praat textgrid with voicing, closure, and vowel interval tiers
# wav_file: the name of the corresponding wav file
# Returns a VCV token object with vowel and stop fields populated
def read_measurements(grid_file_name, wav_file_name):
    tg = textgrid.TextGrid.fromFile(grid_file_name)
    voicing_tier = [tier for tier in tg.tiers if tier.name == "voicing"][0]
    closure_tier = [tier for tier in tg.tiers if tier.name == "closure"][0]
    vowel_tier = [tier for tier in tg.tiers if tier.name == "vowel"][0]

    #Get labels
    label_info = os.path.basename(grid_file_name)
    vowel_label = label_info[0:2] #Vowel is first 2 characters in name
    stop_label = label_info[2] #Stop is next character TODO: fix for glottal stops, which are empty strings
    #if debug:
   #     print(vowel_label, stop_label)
    split_name = label_info.split("_")
    speaker_info = split_name[1]

    #Get just the labeled tiers
    voicing_tier = [interval for interval in voicing_tier if len(interval.mark)>0]
    #While debugging, check that the textgrids have been properly annotated
    assert len(voicing_tier) == 1
    closure_tier = [interval for interval in closure_tier if len(interval.mark)>0]
    assert len(closure_tier) == 1
    vowel_tier = [interval for interval in vowel_tier if len(interval.mark)>0]
    assert len(vowel_tier) == 2

    #Compute stop values and construct stop
    voicing = voicing_tier[0]
    voicing_dur = 0 if voicing.mark == "0" else voicing.maxTime - voicing.minTime
    closure = closure_tier[0]
    closure_dur = closure.maxTime - closure.minTime
    stop = Stop(stop_label, voicing_dur, closure_dur)

    vowel1, vowel2 = read_vowel_measurements(wav_file_name, vowel_tier[0], vowel_tier[1], vowel_label, vowel_label)

    return VcvToken(speaker_info, stop, vowel1, vowel2)

#praat_object: Parselmouth praat object to get the estimate from
#frequency_type: string, "f0" or "formant"
#formant_num: define if frequency type is formant, the number of the formant to estimate
#point: True if estimating at a certain point, False if estimating over an interval
#timepoint: define if point, in seconds, time to take the estimate from
#span_begin: define if not point, in seconds, start of interval
#span_begin: define if not point, in seconds, end of interval
#For point estimates, repeats at slightly earlier timepoint until the result is a defined number
#or the offset is greater than 30ms
#offsetdirection: move measurement backward (-1) or forward(1)
#Returns the estimate and the offset used to calculate it
def get_praat_estimate(praat_object, frequency_type, formant_num = 0, point=True, timepoint=0, span_begin=0, span_end=0, offsetDirection = -1):
    estimate = math.nan
    offset = 0
    if point:
        #If the value isn't defined at this particular point, try budging by a few ms
        while math.isnan(estimate) and offset <= 0.04:
            if frequency_type == "formant":
                estimate = parselmouth.praat.call(praat_object, "Get value at time", formant_num,
                                                      timepoint + offsetDirection*offset, 'Hertz', 'Linear')
            else:
                estimate = parselmouth.praat.call(praat_object, "Get value at time",
                                                  timepoint + offsetDirection * offset, 'Hertz', 'Linear')
            offset += .001
        offset -= .001
    else:
        if frequency_type == "formant":
            estimate = parselmouth.praat.call(praat_object, "Get mean", formant_num,
                                              span_begin, span_end, 'Hertz')
        else:
            estimate = parselmouth.praat.call(praat_object,"Get mean",
                                              span_begin, span_end, 'Hertz')
    return estimate, offset




#wav_file_name: string name of a wav file
#vowel1: a textgrid interval object corresponding to the first vowel
#vowel2: a textgrid interval object corresponding to the second vowel
#vowel1_label: the string label for vowel1
#vowel2_label: the string label for vowel2
#returns two Vowel objects corresponding to vowel1 and vowel2
#Adapted from the examples in https://github.com/drfeinberg/PraatScripts/blob/master/Measure%20Pitch%2C%20HNR%2C%20Jitter%2C%20Shimmer%2C%20and%20Formants.ipynb
def read_vowel_measurements(wav_file_name, vowel1, vowel2, vowel1_label, vowel2_label):
    vowel1_obj = Vowel(vowel1_label)
    vowel2_obj = Vowel(vowel2_label)

    # Steady-state measurement of vowel1: first 99% of the vowel - I don't have a good reason for picking this number; suggestions?
    v1_steady_min = vowel1.minTime
    v1_steady_max = vowel1.maxTime * 0.99 #TODO: reduce this split
    #put vowel into many slices and get values for each slice - look for standard deviation to see if there's something weird
    #getting measurement near closure- calculate slope and interpolate endpoint from earlier measurements?
    #grab last few windows and check variance
    #if checking by hand, do a variable sample
    v1_steady_midpoint = v1_steady_min + (v1_steady_max - v1_steady_min) / 2.0
    # Transition measurement of vowel1: last 10% of the vowel
    v1_transit_min = v1_steady_max
    v1_transit_max = vowel1.maxTime
    # I'm not sure if this is the best place to measure onset/offset...
    v1_transit_midpoint = v1_transit_min + (v1_transit_max - v1_transit_min) / 2.0
    # Transition measurement of vowel2: first 10% of the vowel
    v2_transit_min = vowel2.minTime
    v2_transit_max = vowel2.maxTime * 0.01
    v2_transit_midpoint = v2_transit_min + (v2_transit_max - v2_transit_min) / 2.0
    # Steady-state measurement of vowel2: last 90% of the vowel
    v2_steady_min = v2_transit_max
    v2_steady_max = vowel2.maxTime
    v2_steady_midpoint = v2_steady_min + (v2_steady_max - v2_steady_min) / 2.0

   # if debug:
   #     print("\t", v1_steady_min, v1_steady_max, v1_steady_midpoint)

    # Read wavfile with Praat for formant data
    sound = parselmouth.Sound(wav_file_name)
    #TODO: adjust parameters for different speakers
    formants = parselmouth.praat.call(sound, "To Formant (burg)", 0.0025, 5, 5000, 0.025, 50)

    #Take midpoint measurements of steady state vs transition regions
    formant_range = range(1,5)
    for formant_num in formant_range:

        #########First vowel

        #Value during the flat part of the vowel
        v1_steady, offset = get_praat_estimate(formants, "formant", formant_num, point=True,
                                               timepoint=v1_steady_midpoint)
        if math.isnan(v1_steady) or offset > 0:
            print(wav_file_name, "v1 steady", formant_num, v1_steady, "offset", offset, v1_steady_midpoint)

        #Value during the transitional part of the vowel
        v1_transit, offset = get_praat_estimate(formants, "formant", formant_num, point=True,
                                               timepoint=vowel1.maxTime)
        if math.isnan(v1_transit) or offset > 0:
            print(wav_file_name, "v1 transit", formant_num, v1_transit, "offset", offset)

        ########Second vowel
        # Value during the flat part of the vowel
        v2_steady, offset = get_praat_estimate(formants, "formant", formant_num, point=True,
                                                   timepoint=v2_steady_midpoint, offsetDirection=1)
        if math.isnan(v2_steady) or offset > 0:
            print(wav_file_name, "v2 steady", formant_num, v2_steady, "offset", offset)

        # Value during the transitional part of the vowel
        v2_transit, offset = get_praat_estimate(formants, "formant", formant_num, point=True,
                                                    timepoint=vowel2.minTime, offsetDirection=1)
        if math.isnan(v2_transit) or offset > 0:
            print(wav_file_name, "v2 transit", formant_num, v2_transit, "offset", offset)

        vowel1_obj.measurement_dict[formant_num]["steady"] = v1_steady
        vowel1_obj.measurement_dict[formant_num]["transit"] = v1_transit
        vowel2_obj.measurement_dict[formant_num]["steady"] = v2_steady
        vowel2_obj.measurement_dict[formant_num]["transit"] = v2_transit

    #Take f0 measurements of steady state vs transition regions (worried f0 won't be well defined if I go too near the  closure)
    #TODO: adjust parameters for different speakers
    #check for cleanness in f0 contours
    pitch = parselmouth.praat.call(sound, "To Pitch", 0.0, 75, 500)  # create a praat pitch object

    #Vowel1 steady pitch
    v1_steady_f0, offset = get_praat_estimate(pitch,"f0",point=False,span_begin=v1_steady_min,span_end=v1_steady_max)
    if math.isnan(v1_steady_f0) or offset > 0:
        print(wav_file_name, "v1 steady f0", v1_steady_f0, "offset", offset)

    #Vowel2 steady pitch
    v2_steady_f0, offset = get_praat_estimate(pitch, "f0", point=False, span_begin=v2_steady_min,
                                              span_end=v2_steady_max)
    if math.isnan(v2_steady_f0) or offset > 0:
        print(wav_file_name, "v2 steady f0", v2_steady_f0, "offset", offset)

    #Vowel1 transitional pitch
    v1_transit_f0, offset = get_praat_estimate(pitch, "f0", point=True, timepoint=vowel1.maxTime)
    if math.isnan(v1_transit_f0) or offset > 0:
        print(wav_file_name, "v1 transit f0", v1_transit_f0, "offset", offset)

    # Vowel2 transitional pitch
    v2_transit_f0, offset = get_praat_estimate(pitch, "f0", point=True, timepoint=vowel2.minTime, offsetDirection=1)
    if math.isnan(v2_transit_f0) or offset > 0:
        print(wav_file_name, "v2 transit f0", v2_transit_f0, "offset", offset)


    vowel1_obj.measurement_dict[0]["steady"] = v1_steady_f0
    vowel2_obj.measurement_dict[0]["steady"] = v2_steady_f0
    vowel1_obj.measurement_dict[0]["transit"] = v1_transit_f0
    vowel2_obj.measurement_dict[0]["transit"] = v2_transit_f0

    return vowel1_obj, vowel2_obj

#tokens: list of VCV
#label: specific stop (string) for title
#speaker: speaker identity (string) for title
def plot_closure_data(tokens, nbins, label = "", speaker = "", savename=""):
    plt.title(" ".join([label, speaker, 'Closure durations']))
    plt.xlabel("Time(s)")
    plt.ylabel("Tokens")
    plt.hist([token.stop.closure_dur for token in tokens], bins=nbins)
    if savename != "":
        plt.savefig(savename)
    plt.show()


#tokens: list of VCV
#label: specific stop for title
#speaker: speaker identity (string) for title
def plot_voicing_data(tokens, nbins, label = "", speaker = "", savename=""):
    plt.title(" ".join([label, speaker,'Voicing durations']))
    plt.xlabel("Time(s)")
    plt.ylabel("Tokens")
    plt.hist([token.stop.voicing_dur for token in tokens], bins=nbins)
    if savename != "":
        plt.savefig(savename)
    plt.show()


#TODO: plot closure/voicing duration ratio


#tokens: list of VCV
#vowel_order: 1 or 2 (first or second vowel)
#measure: 0 for f0, 1-5 for formants 1-5
#location: string, "steady" or "transit"
#label: specific vowel quality (string) for title
#speaker: speaker identity (string) for title
def plot_vowel_measure(vowel_order, measure, location, tokens, nbins, label ="", speaker="", savename=""):
    #plt.figure()
    title_measure = 'F'+str(measure) if measure > 0 else "f0"
    title_location = "away from closure" if location == "steady" else "near closure"
    title_vowel = "First vowel" if vowel_order == 1 else "Second vowel"
    plt.title(" ".join([speaker, label, title_vowel, title_measure, title_location]))
    plt.xlabel("Frequency(Hz)")
    plt.ylabel("Tokens")


    #Check for nan values
    nan_check = [token for token in tokens if math.isnan(token.vowel1.measurement_dict[measure][location])]
    if debug and len(nan_check) > 0:
        nan_token = nan_check[0]
        print("F", measure, "Nan value for this speaker, vowel, stop combo:", nan_token.speaker, nan_token.vowel1.label, nan_token.stop.label)

    values = [token.vowel1.measurement_dict[measure][location] for token in tokens]
    values = [value for value in values if not math.isnan(value)]

    plt.hist(values, bins=nbins)
    if savename != "":
        plt.savefig(savename)
    plt.show()



#Helper function: creates plots for f0 and each formant
#condition: function that takes a token and returns a boolean; only the tokens that result in True
#will be included in the plots
#label: extra substring to be added to plot file names and titles
def plot_vowel_measures(tokens,condition, label):
    # Plot steady f0
    plot_vowel_measure(1, 0, "steady", [token for token in tokens if condition(token)],
                       nbins, label=label, savename=plot_dir + label + "_v1_steady_f0.png")
    plot_vowel_measure(2, 0, "steady", [token for token in tokens if condition(token)],
                       nbins, label=label, savename=plot_dir + label + "_v2_steady_f0.png")

    # Plot transition f0
    plot_vowel_measure(1, 0, "transit", [token for token in tokens if condition(token)],
                       nbins, label=label, savename=plot_dir + label + "_v1_transition_f0.png")
    plot_vowel_measure(2, 0, "transit", [token for token in tokens if condition(token)],
                       nbins, label=label, savename=plot_dir + label + "_v2_transition_f0.png")

    # Plot transition/steady for each formant
    for formant_no in range(1, 6):
        plot_vowel_measure(1, formant_no, "steady", [token for token in tokens if condition(token)],
                           nbins, label=label,
                           savename=plot_dir + label + "_v1_steady_F" + str(formant_no) + ".png")
        plot_vowel_measure(2, formant_no, "steady", [token for token in tokens if condition(token)],
                           nbins, label=label,
                           savename=plot_dir + label + "_v2_steady_F" + str(formant_no) + ".png")

        plot_vowel_measure(1, formant_no, "transit", [token for token in tokens if condition(token)],
                           nbins, label=label,
                           savename=plot_dir + label + "_v1_transition_F" + str(formant_no) + ".png")
        plot_vowel_measure(2, formant_no, "transit", [token for token in tokens if condition(token)],
                           nbins, label=label,
                           savename=plot_dir + label + "_v2_transition_F" + str(formant_no) + ".png")

#Returns two lists of VCV objects with values measured from the Laff corpus
#The first list is composed of voiced stops(bdg), the second voiceless stops(ptk)
def get_vcv_data(path="../../laff_vcv_tokens_with_stops"):
    files = os.listdir(path)
    token_names = list(set([file[0:file.index(".")] for file in files]))
    token_names.sort()

    voiced_stops = ["b", "d", "g"]  # this should be done with something like enums, but that's low priority for now
    voiceless_stops = ["p", "t", "k"]

    tokens = []
    for token_name in token_names:
        #print("Working on", token_name)
        filename = path + "/" + token_name
        vcv = read_measurements(filename + ".TextGrid", filename + ".wav")
        #if debug:
        #    print("\t", vcv.stop.voicing_dur, vcv.stop.closure_dur)
        #    print("\t", vcv.vowel1.measurement_dict)
        tokens.append(vcv)

    #Filter out glottal stops
    voiced_stops = [token for token in tokens if token.stop.label in voiced_stops]
    voiceless_stops = [token for token in tokens if token.stop.label in voiceless_stops]

    return voiced_stops, voiceless_stops

if __name__ == "__main__":
    path = "../../laff_vcv_tokens_with_stops"
    files = os.listdir(path)
    token_names = list(set([file[0:file.index(".")] for file in files]))
    token_names.sort()

    voiced_stops = ["b","d","g"]#technically this should be done with enums, but that's low priority for now
    voiceless_stops = ["p","t","k"] #TODO: glottal stops

    tokens = []
    for token_name in token_names:
        print("Working on", token_name)
        filename = path + "/"+token_name
        vcv = read_measurements(filename+".TextGrid", filename+".wav")
        #if debug:
        #    print("\t", vcv.stop.voicing_dur, vcv.stop.closure_dur)
        #    print("\t", vcv.vowel1.measurement_dict)
        tokens.append(vcv)

    #Get list of unique vowels, stops, and speakers for splitting up data
    vowels = list(set([vcv.vowel1.label for vcv in tokens]))
    vowels.sort()

    stops = list(set([vcv.stop.label for vcv in tokens]))
    stops.sort()

    speakers = list(set([vcv.speaker for vcv in tokens]))
    speakers.sort()

   # if debug:
   #     print(set([token.stop.label for token in tokens]))


    ###Plotting!
    #Not sure how to pick the number of bins(continuous values); I went with 20
    nbins = 20
    plot_dir = "laff_plots/"

    #Voiced vs voiceless closure durations
    plot_closure_data([token for token in tokens if token.stop.label not in voiced_stops],nbins, label="Voiceless", savename=plot_dir+"VoicelessClosureDur.png")
    plot_closure_data([token for token in tokens if token.stop.label in voiced_stops], nbins, label="Voiced", savename=plot_dir+"VoicedClosureDur.png")

    #Voiced vs voiceless voicing durations
    plot_voicing_data([token for token in tokens if token.stop.label not in voiced_stops], nbins, label="Voiceless", savename=plot_dir+"VoicelessVoicingDur")
    plot_voicing_data([token for token in tokens if token.stop.label in voiced_stops], nbins, label="Voiced", savename=plot_dir+"VoicedVoicingDur")

    #Vowel measurements by vowel
    if debug:
        for vowel in vowels:
            plot_vowel_measures(tokens, lambda token: token.vowel1.label == vowel, label=vowel)

    if debug:
        #Vowel measurements by vowel x stop TODO: glottal stops
        for vowel in vowels:
            for stop in voiceless_stops + voiced_stops:
                plot_vowel_measures(tokens, lambda token: token.vowel1.label == vowel and token.stop.label == stop, label = vowel+"_"+stop)

    #Vowel measurements by stop
    for stop in voiceless_stops+voiced_stops:
        plot_vowel_measures(tokens, lambda token: token.stop.label == stop, label=stop)







