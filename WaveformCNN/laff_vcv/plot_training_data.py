from laff_vcv.compute_vcv_distributions import VcvToken, Vowel,Stop, \
    plot_vowel_measure, plot_voicing_data, plot_closure_data

import csv


if __name__ == "__main__":
    voiced_stops = ["b","d","g"]
    voiceless_stops = ["p","t", "k"]

    #Read in training synthesis parameters into VCV data type
    training_token_values = "sampled_stop_klatt_params_pulse_voicing_artificial_closure_dur.csv"
    tokens = []
    with open(training_token_values) as csvfile:
        reader = csv.DictReader(csvfile)
        for token in reader:
            name = token["Name"].split("_")
            speaker = name[1]

            stop_label = name[2]
            voicing_dur = float(token["ClosureVoicingDur"])
            closure_dur = float(token["ClosureDur"])

            vowel_label = name[3]
            f1_offset = float(token["F1offset"])
            f1_steady = float(token["F1steady"])
            f0_offset = float(token["f0offset"])
            f0_steady = float(token["f0steady"])

            stop = Stop(stop_label,voicing_dur, closure_dur)
            vowel = Vowel(vowel_label)
            vowel.measurement_dict[0]["steady"] = f0_steady
            vowel.measurement_dict[0]["transit"] = f0_offset
            vowel.measurement_dict[1]["steady"] = f1_steady
            vowel.measurement_dict[1]["transit"] = f1_offset

            tokens.append(VcvToken(speaker, stop, vowel, vowel))


    #Plot for voiced and voiceless groups
    voiced = [token for token in tokens if token.stop.label in voiced_stops]
    voiceless = [token for token in tokens if token.stop.label in voiceless_stops]
    print(len(voiced))
    print(len(voiceless))


    nbins = 10
    plot_dir = "training_data_plots/"

    # Voiced vs voiceless closure durations
    plot_closure_data(voiceless, nbins, label="Voiceless",
                      savename=plot_dir + "VoicelessClosureDur.png")
    plot_closure_data(voiced, nbins, label="Voiced",
                      savename=plot_dir + "VoicedClosureDur.png")

    # Voiced vs voiceless voicing durations
    plot_voicing_data(voiceless, nbins, label="Voiceless",
                      savename=plot_dir + "VoicelessVoicingDur")
    plot_voicing_data(voiced, nbins, label="Voiced",
                      savename=plot_dir + "VoicedVoicingDur")

    # Vowel measurements by voiced vs voiceless

    plot_vowel_measure(1, 0, "transit", voiceless, nbins, label="Voiceless", savename=plot_dir)
    plot_vowel_measure(1, 0, "transit", voiced, nbins, label="Voiced", savename=plot_dir)

    plot_vowel_measure(1, 1, "transit", voiceless, nbins, label="Voiceless", savename=plot_dir)
    plot_vowel_measure(1, 1, "transit", voiced, nbins, label="Voiced", savename=plot_dir)

    plot_vowel_measure(1, 0,"steady", voiceless,nbins,label="Voiceless",savename=plot_dir)
    plot_vowel_measure(1, 0, "steady", voiced, nbins, label="Voiced", savename=plot_dir)

    plot_vowel_measure(1, 1, "steady", voiceless, nbins, label="Voiceless", savename=plot_dir)
    plot_vowel_measure(1, 1, "steady", voiced, nbins, label="Voiced", savename=plot_dir)




