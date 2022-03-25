import textgrid
import parselmouth


class VcvToken:
    def __init__(self, stop, vowel1, vowel2):
        self.stop = stop
        self.vowel1 = vowel1
        self.vowel2 = vowel2


class Vowel:
    def __init__(self, label):
        self.label = label #String label
        self.measurement_dict = {
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
    voicing_tier = tg["voicing"]
    closure_tier = tg["closure"]
    vowel_tier = tg["vowel"]

    #Get labels
    vowel_label = grid_file_name[0:2] #Vowel is first 2 characters in name
    stop_label = grid_file_name[3] #Stop is next character

    #Get just the labeled tiers
    voicing_tier = [interval for interval in voicing_tier if len(interval.mark)>0]
    assert len(voicing_tier) == 1
    closure_tier = [interval for interval in closure_tier if len(interval.mark)>0]
    assert len(closure_tier) == 1
    vowel_tier = [interval for interval in vowel_tier if len(interval.mark)>0]
    assert len(vowel_tier) == 2

    #Compute stop values and construct stop
    voicing = voicing_tier[0]
    voicing_dur = 0 if voicing.mark == "0" else voicing.max - voicing.min
    closure = closure_tier[0]
    closure_dur = closure.max - closure.min
    stop = Stop(stop_label, voicing_dur, closure_dur)

    vowel1, vowel2 = read_vowel_measurements(wav_file_name, vowel_tier[0], vowel_tier[1], vowel_label, vowel_label)

    return VcvToken(stop, vowel1, vowel2)


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

    # Steady-state measurement of vowel1: first 90% of the vowel
    v1_steady_min = vowel1.min
    v1_steady_max = vowel1.max * 0.9
    v1_steady_midpoint = (v1_steady_max - v1_steady_max) / 2
    # Transition measurement of vowel1: last 10% of the vowel
    v1_transit_min = v1_steady_max
    v1_transit_max = vowel1.max
    # I'm not sure if this is the best place to measure onset/offset...
    v1_transit_midpoint = (v1_transit_max - v1_transit_min) / 2
    # Transition measurement of vowel2: first 10% of the vowel
    v2_transit_min = vowel2.min
    v2_transit_max = vowel2.max * 0.1
    v2_transit_midpoint = (v2_transit_max - v2_transit_min) / 2
    # Steady-state measurement of vowel2: last 90% of the vowel
    v2_steady_min = v2_transit_max
    v2_steady_max = vowel2.max
    v2_steady_midpoint = (v2_steady_max - v2_steady_min) / 2

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
    pitch = parselmouth.praat.call(sound, "To Pitch", 0.0, 75, 500)  # create a praat pitch object
    vowel1_obj.measurement_dict[0]["steady"] = parselmouth.praat.call(pitch, "Get mean", v1_steady_min, v1_steady_max, "Hertz")  # get mean pitch
    vowel2_obj.measurement_dict[0]["steady"] = parselmouth.praat.call(pitch, "Get mean", v1_steady_min, v1_steady_max, "Hertz")
    vowel1_obj.measurement_dict[0]["transit"] = parselmouth.praat.call(pitch, "Get mean", v1_transit_min, v1_transit_max, "Hertz")
    vowel2_obj.measurement_dict[0]["transit"] = parselmouth.praat.call(pitch, "Get mean", v2_transit_min,
                                                                       v2_transit_max, "Hertz")

    return vowel1_obj, vowel2_obj












