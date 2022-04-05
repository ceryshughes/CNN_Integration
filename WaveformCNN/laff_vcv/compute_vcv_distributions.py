import textgrid
import parselmouth
import os
import matplotlib.pyplot as plt
import math

debug = True

class VcvToken:
    def __init__(self, speaker, stop, vowel1, vowel2):
        self.speaker = speaker #String speaker label
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
    if debug:
        print(vowel_label, stop_label)
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
    v1_steady_midpoint = v1_steady_min + (v1_steady_max - v1_steady_max) / 2.0
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

    if debug:
        print("\t", v1_steady_min, v1_steady_max, v1_steady_midpoint)

    # Read wavfile with Praat for formant data
    sound = parselmouth.Sound(wav_file_name)
    #TODO: adjust parameters for different speakers
    formants = parselmouth.praat.call(sound, "To Formant (burg)", 0.0025, 5, 5000, 0.025, 50)

    #Take midpoint measurements of steady state vs transition regions
    formant_range = range(1,6)
    for formant_num in formant_range:
        vowel1_obj.measurement_dict[formant_num]["steady"] = parselmouth.praat.call(formants,"Get value at time", formant_num, v1_steady_midpoint,
                                                                          'Hertz', 'Linear') #I think this str vs object typing warning for the first argument
                                                                            # is due to the imperfect documentation of call; it seems both are allowed
        vowel1_obj.measurement_dict[formant_num]["transit"] = parselmouth.praat.call(formants,"Get value at time", formant_num,
                                                                                     v1_transit_midpoint,'Hertz', 'Linear')
        vowel2_obj.measurement_dict[formant_num]["steady"] = parselmouth.praat.call(formants,"Get value at time", formant_num,
                                                                                    v2_steady_midpoint, 'Hertz', 'Linear')
        vowel2_obj.measurement_dict[formant_num]["transit"] = parselmouth.praat.call(formants, "Get value at time",
                                                                                    formant_num, v2_transit_midpoint,
                                                                                    'Hertz', 'Linear')

    #Take f0 measurements of steady state vs transition regions (worried f0 won't be well defined if I go too near the  closure)
    #TODO: adjust parameters for different speakers
    #check for cleanness in f0 contours
    pitch = parselmouth.praat.call(sound, "To Pitch", 0.0, 75, 500)  # create a praat pitch object
    vowel1_obj.measurement_dict[0]["steady"] = parselmouth.praat.call(pitch, "Get mean", v1_steady_min, v1_steady_max, "Hertz")  # get mean pitch
    vowel2_obj.measurement_dict[0]["steady"] = parselmouth.praat.call(pitch, "Get mean", v1_steady_min, v1_steady_max, "Hertz")
    vowel1_obj.measurement_dict[0]["transit"] = parselmouth.praat.call(pitch, "Get mean", v1_transit_min, v1_transit_max, "Hertz")
    vowel2_obj.measurement_dict[0]["transit"] = parselmouth.praat.call(pitch, "Get mean", v2_transit_min,
                                                                       v2_transit_max, "Hertz")

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
        if debug:
            print("\t", vcv.stop.voicing_dur, vcv.stop.closure_dur)
            print("\t", vcv.vowel1.measurement_dict)
        tokens.append(vcv)

    #Get list of unique vowels, stops, and speakers for splitting up data
    vowels = list(set([vcv.vowel1.label for vcv in tokens]))
    vowels.sort()

    stops = list(set([vcv.stop.label for vcv in tokens]))
    stops.sort()

    speakers = list(set([vcv.speaker for vcv in tokens]))
    speakers.sort()

    if debug:
        print(set([token.stop.label for token in tokens]))


    ###Plotting!
    #Not sure how to pick the number of bins(continuous values); I went with 20
    nbins = 20
    plot_dir = "laff_plots/"

    #Voiced vs voiceless closure durations
    plot_closure_data([token for token in tokens if token.stop.label not in voiced_stops],nbins, label="Voiceless", savename=plot_dir+"VoicelessClosure.png")
    plot_closure_data([token for token in tokens if token.stop.label in voiced_stops], nbins, label="Voiced", savename=plot_dir+"VoicedClosure.png")

    #Voiced vs voiceless voicing durations
    plot_closure_data([token for token in tokens if token.stop.label not in voiced_stops], nbins, label="Voiceless", savename=plot_dir+"VoicelessVoicingDur")
    plot_closure_data([token for token in tokens if token.stop.label in voiced_stops], nbins, label="Voiced", savename=plot_dir+"VoicelessVoicedDur")

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







