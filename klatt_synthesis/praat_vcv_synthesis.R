# Script adapted from newmanSynthesis_06_feb22.Rmd
# Modified to produce V-stop-V sequences with varying closure durations, 
# offset/onset formant and f0 values, and closure voicing durations


library(tidyverse)
library(tibble)
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
  cat(lineOut, file=out_file_name, sep="\n", append=T)
}

#Important time regions:
#Steady state
#Transition
#Closure
#Closure voicing end
#Transition
#Steady state



write_formant_amplitude_timecourse <- function (out_file_name, 
                                               formant,
                                               v1_end,
                                               closure_begin, 
                                               closure_end,
                                               v2_begin,
                                               max_time,
                                               voicing=FALSE,
                                               voicing_end=0,
                                               silence_begin=0){
  formant_amp <- 60
  
  #Formant amplitude in v1
  write_formant_amp_point(out_file_name, formant, 0, formant_amp)
  
  if(voicing & formant == 1){
    #F1 holding during the closure
    write_formant_amp_point(out_file_name, formant, v1_end, formant_amp)
    write_formant_amp_point(out_file_name, formant, closure_begin, formant_amp/2)
    write_formant_amp_point(out_file_name, formant, voicing_end, formant_amp/2)
    #F1 transition to silence for silent part of the closure
    write_formant_amp_point(out_file_name, formant, silence_begin, 0)
    
  }else{
    #Formant amplitude is positive up until the end of v1, then transitions to 0 for the closure
    write_formant_amp_point(out_file_name, formant, v1_end, formant_amp)
    write_formant_amp_point(out_file_name, formant, closure_begin, 0)
    write_formant_amp_point(out_file_name, formant, closure_end, 0)
  }
  
  #Formants come back for v2
  write_formant_amp_point(out_file_name, formant, v2_begin, formant_amp)
  write_formant_amp_point(out_file_name, formant, max_time, formant_amp)
}

#TODO: write formant freq timecourse
write_formant_freq_timecourse <- function(out_file_name, 
                              formant,
                              steady_freq,
                              offset_freq,
                              v1_trans_time,
                              v1_end,
                              closure_begin, 
                              closure_end,
                              v2_begin,
                              v2_trans_time,
                              max_time,
                              voicing=FALSE,
                              voicing_end=0,
                              closure_freq = 0){
  
  #Steady frequency in beginning of vowel
  write_formant_freq_point(out_file_name, formant, 0, steady_freq)
  
  #Interpolate to offset frequency
  write_formant_freq_point(out_file_name, formant, v1_trans_time, steady_freq)
  write_formant_freq_point(out_file_name, formant, v1_end, offset_freq)
  
  #If F1 and closure voicing, switch to closure voicing frequency value
  if (voicing & formant == 1){
    write_formant_freq_point(out_file_name, formant, closure_begin, closure_freq)
    write_formant_freq_point(out_file_name, formant, voicing_end, closure_freq)
    print(paste(v1_end,closure_begin, voicing_end, sep=" "))
    #Switch back to offset frequency before the closure ends, during silence
    write_formant_freq_point(out_file_name, formant, closure_end, offset_freq)
  }
  
  #Transition from offset frequency to steady frequency at the beginning of v2
  write_formant_freq_point(out_file_name, formant, v2_begin, offset_freq)
  write_formant_freq_point(out_file_name, formant, v2_trans_time, steady_freq)
  
  #Steady freq to the end of the sound (maybe this point isn't necessary)
  write_formant_freq_point(out_file_name, formant, max_time, steady_freq)
  
}




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
                                     bandwidth,
                                     v1_steady,
                                     v2_steady,
                                     trans_target,
                                     v1_trans_begin,
                                     v1_end,
                                     closure_begin,
                                     closure_end,
                                     v2_begin,
                                     v2_steady_begin,
                                     v2_end, 
                                     voicing_end = 0,
                                     silence_begin = 0,
                                     closure_freq = 0,
                                     voicing = FALSE  
){
  
  #Bandwidth
  lineOut <- paste("Add oral formant bandwidth point...", formant, 0, bandwidth, sep = " ") 
  cat(lineOut, file=out_file_name, sep="\n", append=T)
  
  
  #Write amplitude timecourse
  write_formant_amplitude_timecourse(out_file_name, 
                                     formant,
                                     v1_end,
                                     closure_begin, 
                                     closure_end,
                                     v2_begin=v2_begin,
                                     max_time=v2_end,
                                     voicing=voicing,
                                     voicing_end=voicing_end,
                                     silence_begin=silence_begin)
  
  #Write frequency timecourse
  write_formant_freq_timecourse(out_file_name, 
                                formant,
                                steady_freq = v1_steady,
                                offset_freq = trans_target,
                                v1_trans_time = v1_trans_begin,
                                v1_end,
                                closure_begin, 
                                closure_end,
                                v2_begin,
                                v2_trans_time = v2_steady_begin,
                                max_time = v2_end,
                                voicing=voicing,
                                voicing_end=voicing_end,
                                closure_freq = closure_freq)
  
  
  
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
write_f0_timecourse <- function(out_file_name, times, freqs, voicing){
  
  write_f0_freq_timecourse(out_file_name, times, freqs, voicing)
  write_f0_amp_timecourse(out_file_name, times, voicing)
}

write_f0_freq_timecourse <- function(out_file_name, times, freqs, voicing){
  if (voicing){
    #Vowel: steady f0, then transition to end
    write_f0_freq_point(out_file_name, 0, freqs$f0steady)
    write_f0_freq_point(out_file_name, times$f0_v1_trans_time, freqs$f0steady)
    write_f0_freq_point(out_file_name, times$v1_end, freqs$f0offset)
    
    #Transition to f0 value for closure voicing
    write_f0_freq_point(out_file_name, times$closure_begin,freqs$f0Closure)
    write_f0_freq_point(out_file_name, times$voicing_end, freqs$f0Closure)
    
    #Onset f0 for vowel 2, then transition to steady frequency
    write_f0_freq_point(out_file_name, times$closure_end, freqs$f0offset)
    write_f0_freq_point(out_file_name, times$v2_begin, freqs$f0offset)
    write_f0_freq_point(out_file_name, times$f0_v2_trans_time, freqs$f0steady)
    write_f0_freq_point(out_file_name, times$v2_end, freqs$f0steady)
  }else{
    
    #Vowel: steady f0, then transition to end
    write_f0_freq_point(out_file_name, 0, freqs$f0steady)
    write_f0_freq_point(out_file_name, times$f0_v1_trans_time, freqs$f0steady)
    write_f0_freq_point(out_file_name, times$v1_end, freqs$f0offset)
    
    #Onset f0 for vowel 2, then transition to steady frequency
    write_f0_freq_point(out_file_name, times$v2_begin, freqs$f0offset)
    write_f0_freq_point(out_file_name, times$f0_v2_trans_time, freqs$f0steady)
    write_f0_freq_point(out_file_name, times$v2_end, freqs$f0steady)
  }
}



write_f0_amp_timecourse <- function(out_file_name,timepoint_params, voicing){
  f0_amp <- 60
  if(voicing){
    #Amplitude during vowel through closure voicing
    write_f0_amp_point(out_file_name, 0, f0_amp)
    write_f0_amp_point(out_file_name, timepoint_params$voicing_end, f0_amp)
    
    #Turn to 0 for rest of the closure
    write_f0_amp_point(out_file_name, timepoint_params$silence_begin, 0)
    write_f0_amp_point(out_file_name, timepoint_params$closure_end, 0)
    
    #Turn back up for second vowel
    write_f0_amp_point(out_file_name, timepoint_params$v2_begin, f0_amp)
    write_f0_amp_point(out_file_name, timepoint_params$v2_end, f0_amp)
    
  }
  else{
    #Amplitude during vowel
    write_f0_amp_point(out_file_name, 0, f0_amp)
    write_f0_amp_point(out_file_name, timepoint_params$v1_end, f0_amp)
    
    #Turn to 0 for closure
    write_f0_amp_point(out_file_name, timepoint_params$closure_begin, 0)
    write_f0_amp_point(out_file_name, timepoint_params$closure_end, 0)
    
    #Turn back up for second vowel
    write_f0_amp_point(out_file_name, timepoint_params$v2_begin, f0_amp)
    write_f0_amp_point(out_file_name, timepoint_params$v2_end, f0_amp)
    
  }
}


#Returns a list of named times when transitions should occur
get_waypoints <- function(values){
  
  #Small transition times because Klatt linear interpolation - can't change instantaneously
  higher_formants_fade <- 0.01
  closure_voicing_fade <- 0.01
  voicing_return_time <- 0.01
  
  #Waypoints around the closure a bit different for if there's closure voicing or not
  if (values$ClosureVoicingDur > 0){
    voicing <- TRUE
    v1_end <- values$VowelDur
    closure_begin <- values$VowelDur + higher_formants_fade
    voicing_end <- closure_begin + values$ClosureVoicingDur
    silence_begin <- voicing_end + closure_voicing_fade
    closure_end <- silence_begin + (values$ClosureDur - values$ClosureVoicingDur)
    v2_begin <- closure_end + voicing_return_time
    v2_end <- v2_begin + values$VowelDur
  }else{
    voicing <- FALSE
    v1_end <- values$VowelDur
    closure_begin <-values$VowelDur + closure_voicing_fade
    closure_end <- closure_begin + values$ClosureDur
    v2_begin <- closure_end + voicing_return_time
    v2_end <- v2_begin + values$VowelDur
  }
  
  #Formant and f0 transition points within-vowel are the same for both  
  f0_v1_trans_time <- values$VowelDur - values$f0TransitionDur
  f0_v2_trans_time <- v2_begin + values$f0TransitionDur
  
  F1_v1_trans_time <- values$VowelDur - values$F1TransitionDur
  F1_v2_trans_time <- v2_begin + values$F1TransitionDur
  
  F2_v1_trans_time <- values$VowelDur - values$OtherFsTransitionDur
  F2_v2_trans_time <- v2_begin + values$OtherFsTransitionDur
  
  F3_v1_trans_time <- values$VowelDur - values$OtherFsTransitionDur
  F3_v2_trans_time <- v2_begin + values$OtherFsTransitionDur
  
  F4_v1_trans_time <- values$VowelDur - values$OtherFsTransitionDur
  F4_v2_trans_time <- v2_begin + values$OtherFsTransitionDur
  
  F5_v1_trans_time <- values$VowelDur - values$OtherFsTransitionDur
  F5_v2_trans_time <- v2_begin + values$OtherFsTransitionDur
  
  if (voicing){
    #Pack the values into a named list
    waypoints <- list(
      voicing = voicing,
      v1_end = v1_end,
      closure_begin = closure_begin,
      voicing_end = voicing_end,
      silence_begin = silence_begin,
      closure_end = closure_end,
      v2_begin = v2_begin,
      v2_end = v2_end
    )
  }else{
      waypoints <- list(
        voicing = voicing,
        v1_end = v1_end,
        closure_begin = closure_begin,
        closure_end = closure_end,
        v2_begin = v2_begin,
        v2_end = v2_end
      )
  }
  
  vowel_transition_times <- list(
    f0_v1_trans_time = values$VowelDur - values$f0TransitionDur,
    f0_v2_trans_time = v2_begin + values$f0TransitionDur,
    
    F1_v1_trans_time = values$VowelDur - values$F1TransitionDur,
    F1_v2_trans_time = v2_begin + values$F1TransitionDur,
    
    F2_v1_trans_time = values$VowelDur - values$OtherFsTransitionDur,
    F2_v2_trans_time = v2_begin + values$OtherFsTransitionDur,
    
    F3_v1_trans_time = values$VowelDur - values$OtherFsTransitionDur,
    F3_v2_trans_time = v2_begin + values$OtherFsTransitionDur,
    
    F4_v1_trans_time = values$VowelDur - values$OtherFsTransitionDur,
    F4_v2_trans_time = v2_begin + values$OtherFsTransitionDur,
    
    F5_v1_trans_time = values$VowelDur - values$OtherFsTransitionDur,
    F5_v2_trans_time = v2_begin + values$OtherFsTransitionDur
    
  )
  
  waypoints <- append(waypoints, vowel_transition_times)
  
  #Return the changing timepoints
  waypoints
  
    
  
  
  
}


#num_formants: number of formants specified(3 or 5)
#values: synthesis parameter values
#Returns a named list with the frequency values:
#steady, offset for each formant number and for f0
#values for f0 and F1 during closure voicing
get_frequency_parameters <- function(values, num_formants){
  freqs <- list(
    f0Closure = values$f0Closure,
    F1Closure = values$F1Closure,
    
    f0steady = values$f0steady,
    f0offset = values$f0offset,
    
    F1steady = values$F1steady,
    F1offset = values$F1offset,
    
    F2steady = values$F2steady,
    F2offset = values$F2offset,
    
    F3steady = values$F3steady,
    F3offset = values$F3offset
  )
  
  if (num_formants == 5){
    higher_forms <- list(
      F4steady = values$F4steady,
      F4offset = values$F4offset,
      
      F5steady = values$F5steady,
      F5offset = values$F5offset
    )
    freqs <- append(freqs, higher_forms)
  }
  
  #Return frequency values
  freqs
  
}




#Function to output a KlattGrid file and wav file
#basename: basename of the KlattGrid that produces a wav file
#gridPath: path to where the KlattGrid will be saved (end in /)
#soundPath: path to where Sound will be saved in the KlattGrid Praat commands
#num_formants: number of formants to output
#waypoints: synthesis timepoint parameters for a single sound
#freqs: synthesis frequency parameters for a single sound
output_klattgrid <- function(basename, gridPath, soundPath, num_formants, waypoints, freqs, voicing){
    klatt_name <- paste(basename, ".KlattGrid", sep="")
    output_file_name <- paste(gridPath, klatt_name, sep="")
    
    
    #Replace file if it already exists
    if (file.exists(output_file_name)) {
      file.remove(output_file_name)
    }
    
    #Opening lines
    lineOut <- paste("Create KlattGrid...", klatt_name, "0", waypoints$v2_end, num_formants, "2", "2", num_formants, "1", "1", "1", sep = " ")
    cat(lineOut, file=output_file_name, sep="\n", append=T)
    cat("\n", file=output_file_name, append = T)
    
    
    #Values for each formant to iterate over
    bandwidths = c(60,90,120,250,250)
    if (num_formants == 5){
      formant_steadies <- c(freqs$F1steady, freqs$F2steady, freqs$F3steady, freqs$F4steady, freqs$F5steady)
      formant_offsets <- c(freqs$F1offset, freqs$F2offset, freqs$F3offset, freqs$F4offset, freqs$F5offset)
      formant_v1_trans_times <- c(waypoints$F1_v1_trans_time, waypoints$F2_v1_trans_time, waypoints$F3_v1_trans_time, waypoints$F4_v1_trans_time, waypoints$F5_v1_trans_time)
      formant_v2_trans_times <- c(waypoints$F1_v2_trans_time, waypoints$F2_v2_trans_time, waypoints$F3_v2_trans_time, waypoints$F4_v2_trans_time, waypoints$F5_v2_trans_time)
    }else{
      formant_steadies <- c(freqs$F1steady, freqs$F2steady, freqs$F3steady)
      formant_offsets <- c(freqs$F1offset, freqs$F2offset, freqs$F3offset)
      formant_v1_trans_times <- c(waypoints$F1_v1_trans_time, waypoints$F2_v1_trans_time, waypoints$F3_v1_trans_time)
      formant_v2_trans_times <- c(waypoints$F1_v2_trans_time, waypoints$F2_v2_trans_time, waypoints$F3_v2_trans_time)
    }
    
    #Write point commands for the formants
    for (formant in 1:num_formants){
      voicing_end <- 0
      silence_begin <- 0
      f1_closure_freq <- 0
      if(voicing){ #These values are defined for tokens with closure voicing but not those without
        voicing_end <- waypoints$voicing_end
        silence_begin <- waypoints$silence_begin
        f1_closure_freq <- freqs$F1Closure
      }
     
      
      write_formant_timecourse(output_file_name, 
                               formant,
                               bandwidths[formant],
                               v1_steady=formant_steadies[formant],
                               v2_steady=formant_steadies[formant],
                               trans_target=formant_offsets[formant],
                               v1_trans_begin=formant_v1_trans_times[formant],
                               v1_end = waypoints$v1_end,
                               closure_begin = waypoints$closure_begin,
                               closure_end = waypoints$closure_end,
                               v2_begin = waypoints$v2_begin,
                               v2_steady_begin = formant_v2_trans_times[formant],
                               v2_end = waypoints$v2_end, 
                               voicing_end = voicing_end,
                               silence_begin = silence_begin,
                               closure_freq = f1_closure_freq,
                               voicing = voicing)  
      cat("\n\n", file=output_file_name, append=T)
    }
    
    #Write point commands for f0
    write_f0_timecourse(output_file_name, waypoints, freqs, voicing)
    
    
    #Wrap up output commands
    lineOut <- paste("To Sound (special)... 0 0 44100 yes yes no no no no \"Powers in tiers\" yes yes yes Parallel 1 5 1 1 1 1 1 1 1 1 1 1 1 1 1 5 yes")
    cat(lineOut, file=output_file_name, sep="\n", append=T)
    
    lineOut <- paste("select Sound", basename, sep=" ")
    cat(lineOut, file=output_file_name, sep="\n", append=T)
    savePath <- paste(soundPath,basename,".wav", sep="")
    lineOut <- paste("Save as WAV file...", savePath, sep=" ")
    cat(lineOut, file=output_file_name, sep="\n", append=T)
    cat("\n", file=output_file_name, append = T)
  
}




#param_file_name <- "sample_klatt_params.xlsx"
param_file_name <- "experimental_stimuli/f0_voicing_dur/klatt_params.xlsx"
sheet_name <- "klatt_params"
p <- read_excel(param_file_name, sheet = sheet_name)
  


gridPath <- "experimental_stimuli/f0_voicing_dur/scripts/"
soundPath <- "C:/Users/hughe/Documents/CNN_Perceptual_Integration_Channel_Bias/Experiment/klatt_synthesis/experimental_stimuli/f0_voicing_dur/sounds/" 

for (condition_index in 1:nrow(p)){
  synth_params <- p %>% slice(condition_index)
  timepoints <- get_waypoints(synth_params)
  # if(timepoints$voicing){
  #   num_formants = 3
  # }else{
  #   num_formants = 5
  # }
  num_formants = 3
  freqs <- get_frequency_parameters(synth_params, num_formants)
  if(timepoints$voicing){
  print(paste(synth_params$Name,timepoints$v1_end, timepoints$closure_begin, sep = ' '))
  }
  
  output_klattgrid(synth_params$Name,gridPath, soundPath,num_formants, timepoints, freqs, timepoints$voicing)
}


