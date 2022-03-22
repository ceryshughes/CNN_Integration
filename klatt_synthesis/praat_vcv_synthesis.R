# Script adapted from newmanSynthesis_06_feb22.Rmd
# Modified to produce V-stop-V sequences with varying closure durations, 
# offset/onset formant and f0 values, and closure voicing durations


library(tidyverse)
library(knitr)
library(ggpubr)

library(readxl) #For reading in the desired parameter values from a file (since there are a lot of them!)



#Writes a single timepoint command for a single formant to out_file_name
#formant: number from 1 to 5 representing which formant
#time: time in seconds where the point should go
#frequency: frequency value in Hertz for the formant at this timepoint
write_formant_freq_point <- function(out_file_name, formant, time, frequency){
  lineOut <- paste("Add oral formant frequency point...", formant, time, frequency, sep = " ")
  cat(lineOut, file=out_file_name, sep="\n", append=T)
  
}

#Writes a single timepoint command for a single formant to out_file_name
#formant: number from 1 to 5 representing which formant
#time: time in seconds where the point should go
#amp: amplitude value(is this in dB?) for the formant at this timepoint
write_formant_amp_point <- function(out_file_name, formant, time, amp){
  lineOut <- paste("Add oral formant amplitude point...", formant, time, amp, sep = " ")
  cat(lineOut, file=out_file_name, sep="\n", append=T)
}


#Writes a single timepoint command for f0 to out_file_name
#time: time in seconds where the point should go
#frequency: frequency value in Hertz for f0 at this timepoint
write_f0_freq_point <- function(out_file_name, time, frequency) {
  lineOut <- paste("Add pitch point...", time, frequency, sep = " ")
  cat(lineOut, file=out_file_name, sep="\n", append=T)
}



#Writes a voicing amplitude command to out_file_name
#time: time in seconds where the point should go
#amp: amplitude value(is this in dB?) for the formant at this timepoint
write_f0_amp_point <- function(out_file_name, time, amp){
  lineOut <- paste("Add voicing amplitude point...", time, amp, sep = " ") 
  cat(lineOut, file=output_file_name, sep="\n", append=T)
}

#Important time regions:
#Steady state
#Transition
#Closure
#Closure voicing end
#Transition
#Steady state


#Writes point commands to output file for the timecourse of a VCV token (where C is a stop) for a single formant 
#(let the first vowel in VCV be called v1 and the second v2). Time/v1 starts at 0.0s
#
# formant: number 1-5 for formants 1 through 5
# v1_steady: the frequency (Hz) for the formant in the steady state portion of the first vowel in VCV
# v2_steady: the frequency for the formant in the steady state portion of the second vowel in VCV
# trans_target: the frequency (Hz) to transition to/away from at the closure
# v1_trans_begin: the timepoint(s) when v1 should start linearly changing from v1_steady to trans_target
# closure_begin: the timepoint(s) when the closure(=formant amplitude is set to 0) begins
# closure_end: the timepoint(s) when the closure(=formant amplitude is set to 0) ends
# v2_steady_begin: the timepoint(s) when v2 should stop linearly transitioning from trans_target to v2_steady
# v2_end: the timepoint when v2 (and the whole VCV sound/utterance) ends
#Except during the closure, formant amplitude is:
write_formant_timecourse <- function(out_file_name, 
                                     formant,
                                     v1_steady,
                                     v2_steady,
                                     trans_target,
                                     v1_trans_begin,
                                     closure_begin,
                                     closure_end,
                                     v2_steady_begin,
                                     v2_end 
){
  
  constant_amp <- 1
  
  #Steady state portion of v1
  write_formant_freq_point(out_file_name, formant, 0.0, v1_steady)
  write_formant_freq_point(out_file_name, formant, v1_trans_begin, v1_steady)
  
  #Transition portion of v1: linear interpolation
  write_formant_freq_point(out_file_name, formant, closure_begin, trans_target)
  
  #Amplitude of v1: set to some constant value between 0.0 and closure_begin
  write_formant_amp_point(out_file_name, formant, 0.0, constant_amp) #TODO: I don't know what the amplitude value should be when not in closure
  write_formant_amp_point(out_file_name, formant, closure_begin - 0.01, constant_amp) #Allow 10ms(0.01s) for transition to closure amplitude; correspondence with John
  
  
  
  #Closure: set amplitude to 0 between closure_begin and closure_end unless it's f1; then, closure value is 150Hz
  if (formant == 1){
    write_formant_freq_point(out_file_name, formant, closure_begin, 150)
    write_formant_freq_point(out_file_name, formant, closure_end, 150)
  } else{
    write_formant_amp_point(out_file_name, formant, closure_begin, 0 ) 
    write_formant_amp_point(out_file_name, formant, closure_end, 0)
  }
  
  
  
  #Transition portion of v2 to steady portion of v2: linear interpolation
  write_formant_freq_point(out_file_name, formant, closure_end, trans_target) 
  write_formant_freq_point(out_file_name, formant, v2_steady_begin, v2_steady)
  
  #Steady state portion of v2
  write_formant_freq_point(out_file_name, formant, v2_end, v2_steady)
  
  #Amplitude of v2: set to some constant value between closure_end and v2_end
  write_formant_amp_point(out_file_name, formant, closure_end + 0.01, constant_amp) #Allow 10ms(0.01s) for transition to closure amplitude; correspondence with John
  write_formant_amp_point(out_file_name, formant, v2_end, constant_amp)
  
}

#Writes point commands to output file for the timecourse of a VCV token (where C is a stop and v1=first vowel, v2=second vowel) for f0
#Time starts at 0.0s
#steady: frequency of f0 during vowels before/after the transition to closure
#trans_target: the frequency f0 linearly transitions to toward the closure
#v1_trans_start: when f0 begins transitioning before the closure for v1
#v2_trans_stop: when f0 stops transitioning after the closure for v2
#closure_begin: the timepoint(seconds) when the closure begins
#closure_value: the frequency of f0 during the closure
#voicing_end: the timepoint(seconds) during the closure when voicing ends
#closure_end: the timepoint(seconds) when the closure ends and the second V begins
#sound_end: the timepoint(seconds) when the second V(and the sound as a whole) ends
write_f0_timecourse <- function(out_file_name, 
                                steady,
                                trans_target,
                                v1_trans_start,
                                v2_trans_stop,
                                closure_begin,
                                closure_value = 90,
                                voicing_end,
                                closure_end,
                                sound_end
){
  constant_amp <- 1
  
  #During first vowel
  write_f0_freq_point(out_file_name, 0.0, steady)
  write_f0_freq_point(out_file_name, v1_trans_start, steady)
  write_f0_freq_point(out_file_name, closure_begin - 0.01, trans_target) #Allow 10ms(0.01s) for transition to closure; correspondence with John
  
  #Amplitude up until when voicing ends
  write_f0_amp_point(out_file_name, 0.0, constant_amp)
  write_f0_amp_point(out_file_name, voicing_end - 0.01, constant_amp) #No closure voicing => voicing_end = closure_begin
  
  #Voicing during closure
  write_f0_freq_point(out_file_name, closure_begin, closure_value)
  write_f0_freq_point(out_file_name, voicing_end, closure_value)
  
  #Turn voicing to amplitude 0 for end of voicing/closure
  write_f0_amp_point(out_file_name, voicing_end, 0)
  write_f0_amp_point(out_file_name, closure_end, 0)
  
  #Turn voicing back up for beginning of second vowel to the end
  write_f0_amp_point(out_file_name, closure_end + 0.01, constant_amp)  #Allow 10ms(0.01s) for transition to closure; correspondence with John
  write_f0_amp_point(out_file_name, sound_end, constant_amp)
  
  #During second vowel
  write_f0_freq_point(out_file_name, closure_end, trans_target) #Allow 10ms(0.01s) for transition to closure; correspondence with John
  write_f0_freq_point(out_file_name, v2_trans_stop, steady)
  write_f0_freq_point(out_file_name, sound_end, steady)
  
  
}

#I don't know what the best practice is for R; in Python/Java/C/Ruby/etc, we have a "main" function 
#where we put our code that executes. In R scripts I've seen, people just run individual lines/blocks
#straight out of the script/in the console...
#Set desired values - would it be smarter to read these off a file since there are so many?
max_time <- 1



f0_steady <- 1
f0_trans <- 1
f0_v1_trans_time <- 1
f0_v2_trans_time <- 1

F1_steady <- 1
F1_trans <- 1
F1_v1_trans_time <- 1
F1_v2_trans_time <- 1


F2_steady <- 1
F2_trans <- 1
F2_v1_trans_time <- 1
F2_v2_trans_time <- 1


F3_steady <- 1
F3_trans <- 1
F3_v1_trans_time <- 1
F3_v2_trans_time <- 1

F4_steady <- 1
F4_trans <- 1
F4_v1_trans_time <- 1
F4_v2_trans_time <- 1

F5_steady <- 1
F5_trans <- 1
F5_v1_trans_time <- 1
F5_v2_trans_time <- 1

closure_begin <- 1
closure_end <- 1
closure_voicing_end <- 1
closure_value <- 1 #How much amplitude should be on voicing during the closure? I don't know what this should be


output_file_name <- "fileOut.KlattGrid"
fileName <- "sound"
dataPath <- "klatt"

formant_steadies <- c(F1_steady, F2_steady, F3_steady, F4_steady, F5_steady)
formant_trans <- c(F1_trans, F2_trans, F3_trans, F4_trans, F5_trans)
formant_v1_trans_times <- c(F1_v1_trans_time, F2_v1_trans_time, F3_v1_trans_time, F4_v1_trans_time, F5_v1_trans_time)
formant_v2_trans_times <- c(F1_v2_trans_time, F2_v2_trans_time, F3_v2_trans_time, F4_v2_trans_time, F5_v2_trans_time)

num_formants <- 5 #3 for xclosure voicing experiments

#Write point commands for the formants
for (formant in 1:num_formants){
  write_formant_timecourse(output_file_name, formant, 
                           #For my current purposes I don't need both of these arguments but I think it's more flexible to have them
                           formant_steadies[formant], formant_steadies[formant], 
                           formant_trans[formant], 
                           formant_v1_trans_times[formant], 
                           closure_begin, closure_end,
                           formant_v2_trans_times[formant], 
                           max_time)
}

#Write point commands for f0
write_f0_timecourse(output_file_name, f0_steady, f0_trans, f0_v1_trans_time, f0_v2_trans_time, 
                    closure_begin,
                    closure_value, 
                    closure_voicing_end,
                    closure_end,
                    max_time
                    )


#Wrap up output commands
lineOut <- paste("To Sound (special)... 0 0 44100 yes yes no no no no \"Powers in tiers\" yes yes yes Parallel 1 5 1 1 1 1 1 1 1 1 1 1 1 1 1 5 yes")
cat(lineOut, file=output_file_name, sep="\n", append=T)

lineOut <- paste("select Sound", fileName, sep=" ")
cat(lineOut, file=output_file_name, sep="\n", append=T)
savePath <- paste(dataPath,"/",fileName,".wav", sep="")
lineOut <- paste("Save as WAV file...", savePath, sep=" ")
cat(lineOut, file=output_file_name, sep="\n", append=T)
cat("\n", file=output_file_name, append = T)

