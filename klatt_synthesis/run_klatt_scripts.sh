#!/bin/bash
# Time-stamp: <2022-4-10 23:34:22 oxbow>
# RUN_KLATT_SCRIPTS.SH
# Project: CNN Perceptual Integration
# Purpose: script to create Klatt synthesized training wav files from a directory of KlattGrid scripts
# RUN THIS FROM C:\Users\hughe\Documents\CNN_Perceptual_Integration_Channel_Bias\Experiment\klatt_synthesis


SCRIPTPATH=scripts_pulse_voicing_artificial_closure_dur/ # Directory for praat scripts run here; end with /



####Get KlattGrid files
for klattgrid in $( ls $SCRIPTPATH ); do

    #### Run them in Praat
    /mnt/c/Users/hughe/Desktop/praat6207_win64/Praat.exe --run $SCRIPTPATH$klattgrid

done



