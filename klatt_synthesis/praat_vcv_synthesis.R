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
                                     v2_end, voicing = FALSE 
){
  
  #Bandwidth
  lineOut <- paste("Add oral formant bandwidth point...", formant, 0, 60, sep = " ") 
  cat(lineOut, file=out_file_name, sep="\n", append=T)
  
  
  constant_amp <- 60
  
  #Steady state portion of v1
  write_formant_freq_point(out_file_name, formant, 0.0, v1_steady)
  write_formant_freq_point(out_file_name, formant, v1_trans_begin, v1_steady)
  
  #Transition portion of v1: linear interpolation
  write_formant_freq_point(out_file_name, formant, closure_begin, trans_target)
  
  #Amplitude of v1: set to some constant value between 0.0 and closure_begin
  write_formant_amp_point(out_file_name, formant, 0.0, constant_amp) #TODO: I don't know what the amplitude value should be when not in closure
  write_formant_amp_point(out_file_name, formant, closure_begin - 0.01, constant_amp) #Allow 10ms(0.01s) for transition to closure amplitude; correspondence with John
  
  
  
  #Closure: set amplitude to 0 between closure_begin and closure_end unless it's f1; then, closure value is 150Hz. What should amplitude be during the closure?
  if (voicing & formant == 1){
    write_formant_freq_point(out_file_name, formant, closure_begin, 150)
    write_formant_freq_point(out_file_name, formant, closure_end - 0.01, 150) #Allow 10ms(0.01s) for transition from closure value to onset/offset value?
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
                                sound_end, voicing = FALSE, constant_amp = 30 #What should av and the formant amplitudes be?
){
  

  

  #During first vowel
  write_f0_freq_point(out_file_name, 0.0, steady)
  write_f0_freq_point(out_file_name, v1_trans_start, steady)
  write_f0_freq_point(out_file_name, closure_begin, trans_target) 
  
  if(voicing){
  #Voicing during closure
  write_f0_freq_point(out_file_name, closure_begin + 0.01, closure_value) #Allow 10ms(0.01s) for transition to closure for frequency too?
  write_f0_freq_point(out_file_name, voicing_end, closure_value)
  }
  
  
  #During second vowel
  write_f0_freq_point(out_file_name, closure_end, trans_target) #Allow 10ms(0.01s) for transition to closure; correspondence with John
  write_f0_freq_point(out_file_name, v2_trans_stop, steady)
  write_f0_freq_point(out_file_name, sound_end, steady)
  
  #Amplitude up until when voicing ends
  write_f0_amp_point(out_file_name, 0.0, constant_amp)
  write_f0_amp_point(out_file_name, voicing_end - 0.01, constant_amp) #No closure voicing => voicing_end = closure_begin
  
  
  #Turn voicing to amplitude 0 for end of voicing/closure
  write_f0_amp_point(out_file_name, voicing_end, 0)
  write_f0_amp_point(out_file_name, closure_end, 0)
  
  #Turn voicing back up for beginning of second vowel to the end
  write_f0_amp_point(out_file_name, closure_end + 0.01, constant_amp)  #Allow 10ms(0.01s) for transition to closure; correspondence with John
  write_f0_amp_point(out_file_name, sound_end, constant_amp)

  
  
}

#filename: the name of an excel file in this directory with the appropriate parameters
#sheetname: name of the sheet with the data in the excel file
#outputs a list with the named important frequency and time values for the points in the KlattGrid
#time values should be in seconds, frequency values should be in Hz
read_parameters_excel <- function(filename, sheetname){
  values <- read_excel(filename, sheet = sheetname)
  
  closure_begin <- values$VowelDur
  closure_end <- closure_begin + values$ClosureDur
  max_time <- closure_end + values$VowelDur
  closure_voicing_end <- closure_begin + values$ClosureVoicingDur
  
  f0_v1_trans_time <- closure_begin - values$f0TransitionDur
  f0_v2_trans_time <- closure_end + values$f0TransitionDur
  
  F1_v1_trans_time <- closure_begin - values$F1TransitionDur
  F1_v2_trans_time <- closure_end + values$F1TransitionDur
  
  F2_v1_trans_time <- closure_begin - values$OtherFsTransitionDur
  F2_v2_trans_time <- closure_end + values$OtherFsTransitionDur
  
  F3_v1_trans_time <- closure_begin - values$F1TransitionDur
  F3_v2_trans_time <- closure_end + values$OtherFsTransitionDur
  
  F4_v1_trans_time <- closure_begin - values$F1TransitionDur
  F4_v2_trans_time <- closure_end + values$OtherFsTransitionDur
  
  F5_v1_trans_time <- closure_begin - values$F1TransitionDur
  F5_v2_trans_time <- closure_end + values$OtherFsTransitionDur
  
  
  #Put the computed values into the tibble and rename some columns
  values <- values  %>% add_column(closure_begin=closure_begin)
  values <- values  %>% add_column(closure_end=closure_end)
  values <- values  %>% add_column(max_time=max_time)
  values <- values  %>% add_column(closure_voicing_end=closure_voicing_end)
  
  values <- values  %>% add_column(f0_v1_trans_time=f0_v1_trans_time)
  values <- values  %>% add_column(f0_v2_trans_time=f0_v2_trans_time)
  values <- rename(values,f0_trans = f0offset)
  values <- rename(values, f0_closure_value=f0Closure)
  values <- rename(values, f0_steady=f0steady)
  
  values <- values  %>% add_column(F1_v1_trans_time=F1_v1_trans_time)
  values <- values  %>% add_column(F1_v2_trans_time=F1_v2_trans_time)
  values <- rename(values,F1_steady = F1steady)
  values <- rename(values,F1_trans = F1offset)
  values <- rename(values, F1_closure_value = F1Closure)
  
  values <- values  %>% add_column(F2_v1_trans_time=F2_v1_trans_time)
  values <- values  %>% add_column(F2_v2_trans_time=F2_v2_trans_time)
  values <- rename(values,F2_steady = F2steady)
  values <- rename(values,F2_trans = F2offset)
  
  values <- values  %>% add_column(F3_v1_trans_time=F3_v1_trans_time)
  values <- values  %>% add_column(F3_v2_trans_time=F3_v2_trans_time)
  values <- rename(values,F3_steady = F3steady)
  values <- rename(values,F3_trans = F3offset)
  
  values <- values  %>% add_column(F4_v1_trans_time=F4_v1_trans_time)
  values <- values  %>% add_column(F4_v2_trans_time=F4_v2_trans_time)
  values <- rename(values,F4_steady = F4steady)
  values <- rename(values,F4_trans = F4offset)
  
  values <- values  %>% add_column(F5_v1_trans_time=F5_v1_trans_time)
  values <- values  %>% add_column(F5_v2_trans_time=F5_v2_trans_time)
  values <- rename(values,F5_steady = F5steady)
  values <- rename(values,F5_trans = F5offset)
  
  values <- values %>% add_column(closure_value = 10)
 
  #Return the tibble
  values
  
}


#Function to output a KlattGrid file and wav file
#basename: basename of the KlattGrid that produces a wav file
#datapath: path to where the KlattGrid(and its wav file, after it's been run) will be saved
#num_formants: number of formants to output
#p: synthesis parameters for a single sound
output_klattgrid <- function(basename, datapath, num_formants, p){
    output_file_name <- paste(basename, ".KlattGrid", sep="")
    
    
    #Replace file if it already exists
    if (file.exists(output_file_name)) {
      file.remove(output_file_name)
    }
    
    #Opening lines
    lineOut <- paste("Create KlattGrid...", output_file_name, "0", p$max_time, num_formants, "2", "2", num_formants, "1", "1", "1", sep = " ")
    cat(lineOut, file=output_file_name, sep="\n", append=T)
    cat("\n", file=output_file_name, append = T)
    
    
    
    formant_steadies <- c(p$F1_steady, p$F2_steady, p$F3_steady, p$F4_steady, p$F5_steady)
    formant_trans <- c(p$F1_trans, p$F2_trans, p$F3_trans, p$F4_trans, p$F5_trans)
    formant_v1_trans_times <- c(p$F1_v1_trans_time, p$F2_v1_trans_time, p$F3_v1_trans_time, p$F4_v1_trans_time, p$F5_v1_trans_time)
    formant_v2_trans_times <- c(p$F1_v2_trans_time, p$F2_v2_trans_time, p$F3_v2_trans_time, p$F4_v2_trans_time, p$F5_v2_trans_time)
    
    
    #Write point commands for the formants
    for (formant in 1:num_formants){
      write_formant_timecourse(output_file_name, formant, 
                               #For my current purposes I don't need both of these arguments but I think it's more flexible to have them
                               formant_steadies[formant], formant_steadies[formant], 
                               formant_trans[formant], 
                               formant_v1_trans_times[formant], 
                               p$closure_begin, p$closure_end,
                               formant_v2_trans_times[formant], 
                               p$max_time)
      cat("\n\n", file=output_file_name, append=T)
    }
    
    #Write point commands for f0
    write_f0_timecourse(output_file_name, p$f0_steady, p$f0_trans, p$f0_v1_trans_time, p$f0_v2_trans_time, 
                        p$closure_begin,
                        p$f0_closure_value, 
                        p$closure_voicing_end,
                        p$closure_end,
                        p$max_time
    )
    
    
    #Wrap up output commands
    lineOut <- paste("To Sound (special)... 0 0 44100 yes yes no no no no \"Powers in tiers\" yes yes yes Parallel 1 5 1 1 1 1 1 1 1 1 1 1 1 1 1 5 yes")
    cat(lineOut, file=output_file_name, sep="\n", append=T)
    
    lineOut <- paste("select Sound", basename, sep=" ")
    cat(lineOut, file=output_file_name, sep="\n", append=T)
    savePath <- paste(dataPath,"/",basename,".wav", sep="")
    lineOut <- paste("Save as WAV file...", savePath, sep=" ")
    cat(lineOut, file=output_file_name, sep="\n", append=T)
    cat("\n", file=output_file_name, append = T)
  
}




param_file_name <- "sample_klatt_params.xlsx"
sheet_name <- "F1ClosureDur"
p <- read_parameters_excel(param_file_name, sheet_name)
num_formants <- 5 #3 for xclosure voicing experiments
  

base_name <- "fileOut"
dataPath <- "klatt"

for (condition_index in 1:nrow(p)){
  synth_params = p %>% slice(condition_index)
  output_klattgrid(synth_params$Name,dataPath,num_formants,synth_params)
}


