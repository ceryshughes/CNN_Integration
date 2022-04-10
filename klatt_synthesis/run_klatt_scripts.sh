#!/bin/bash
# Time-stamp: <2022-4-10 23:34:22 oxbow>
# RUN_KLATT_SCRIPTS.SH
# Project: CNN Perceptual Integration
# Purpose: script to create Klatt synthesized training wav files from a directory of KlattGrid scripts
# RUN THIS FROM 


SCRIPTPATH=$PWD/scripts/ # Directory for praat scripts run here



####Get KlattGrid files
for klattgrid in $( ls $SCRIPTPATH ); do

    #### Run them in Praat
    /mnt/c/Users/hughe/Desktop/praat6207_win64/Praat.exe --run $klattgrid

done



