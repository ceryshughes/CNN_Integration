import textgrid


class VcvToken:
    def __init__(self, stop, vowel1, vowel2):
        self.stop = stop
        self.vowel1 = vowel1
        self.vowel2 = vowel2


class Vowel:
    def __init__(self, label):
        self.label = label #String label
        self.measurement_dict = {
            "f0": {"steady": 0, "trans":0},
            "F1": {"steady": 0, "trans":0},
            "F2": {"steady": 0, "trans":0},
            "F3": {"steady": 0,"trans":0},
            "F4":{"steady": 0, "trans":0},
            "F5":{"steady": 0, "trans":0}
        }


class Stop:
    def __init__(self, label, voicing_dur, closure_dur):
        self.voicing_dur = voicing_dur
        self.label = label
        self.closure_dur = closure_dur

# grid_file_name: the name of a Praat textgrid with voicing, closure, and vowel interval tiers
# wav_file: the name of the corresponding wav file
# Returns voicing duration(float, in seconds), closure duration(float, in seconds),
# and a dictionary
def read_measurements(grid_file_name, wav_file_name):
    tg = textgrid.TextGrid.fromFile(grid_file_name)
    voicing_tier = tg["voicing"]
    closure_tier = tg["closure"]
    vowel_tier = tg["vowel"]

    #Get labels
    vowel_label = grid_file_name[0:2] #Vowel is first 2 characters in name
    stop_label = grid_file_name[3] #Stop is next character

    voicing_duration = voicing_tier






