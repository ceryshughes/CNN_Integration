#library("dplyr")                                    # Load dplyr package
#library("plyr")                                     # Load plyr package
#library("readr")                                    # Load readr package
library("tidyverse")
library("comprehenr")

setwd("~/CNN_Perceptual_Integration_Channel_Bias/Experiment/analysis")



distances <-
  list.files(path = "../WaveformCNN/discrim_results/", pattern = "*.csv", full.names = TRUE) %>% 
  map_df(~read.csv(.))




#For each task:

#Hard-code identify which diagonal is the IPP and add as column
ipp <- function(row){
  experiment <- row[["Experiment"]]
  stim1_f0 <- row[["stim1_f0"]]
  stim2_f0 <- row[["stim2_f0"]]
  
  stim1_Closure <- row[["stim1_Closure"]]
  stim2_Closure <- row[["stim2_Closure"]]
  
  stim1_f1 <- row[["stim1_F1"]]
  stim2_f1 <- row[["stim2_F1"]]
  
  stim1_voicing <- row[["stim1_voicing"]]
  stim2_voicing <- row[["stim2_voicing"]]
  
  result <- 0
  if(experiment == "f0_closure_dur_high_f1" | experiment == "f0_closure_dur_low_f1"){
    #IPP diagonal (don't know which will be stim1 vs stim2)
    if(stim1_f0 == 0 & stim1_Closure == 0 & stim2_f0 == 1 & stim2_Closure == 1){
      result <- 1
    }
    if(stim1_f0 == 1 & stim1_Closure == 1 & stim2_f0 == 0 & stim2_Closure == 0){
      result <- 1
    }
    #Anti-IPP diagonal (don't know which will be stim1 vs stim2)
    if(stim1_f0 == 0 & stim1_Closure == 1 & stim2_f0 == 1 & stim2_Closure == 0){
      result <- -1
    }
    if(stim1_f0 == 1 & stim1_Closure == 0 & stim2_f0 == 0 & stim2_Closure == 1){
      result <- -1
    }
  }
  else if(experiment == "f1_closure_dur_high_f0" | experiment == "f1_closure_dur_low_f0"){
    #IPP diagonal (don't know which will be stim1 vs stim2)
    if(stim1_f1 == 0 & stim1_Closure == 0 & stim2_f1 == 1 & stim2_Closure == 1){
      result <- 1
    }
    if(stim1_f1 == 1 & stim1_Closure == 1 & stim2_f1 == 0 & stim2_Closure == 0){
      result <- 1
    }
    #Anti IPP diagonal (don't know which will be stim1 vs stim2)
    if(stim1_f1 == 0 & stim1_Closure == 1 & stim2_f1 == 1 & stim2_Closure == 0){
      result <- -1
    }
    if(stim1_f1 == 1 & stim1_Closure == 0 & stim2_f1 == 0 & stim2_Closure == 1){
      result <- -1
    }
  }
  else if(experiment == "f0_voicing_dur"){
    #IPP diagonal (don't know which will be stim1 vs stim2)
    if(stim1_f0 == 0 & stim1_voicing == 1 & stim2_f0 == 1 & stim2_voicing == 0){
      result <- 1
    }
    if(stim1_f0 == 1 & stim1_voicing == 0 & stim2_f0 == 0 & stim2_voicing == 1){
      result <- 1
    }
    #Anti IPP diagonal (don't know which will be stim1 vs stim2)
    if(stim1_f0 == 1 & stim1_voicing == 1 & stim2_f0 == 0 & stim2_voicing == 0){
      result <- -1
    }
    if(stim1_f0 == 0 & stim1_voicing == 0 & stim2_f0 == 1 & stim2_voicing == 1){
      result <- -1
    }
  }
  else if (experiment == "f1_voicing_dur"){
    #IPP diagonal (don't know which will be stim1 vs stim2)
    if(stim1_f1 == 0 & stim1_voicing == 1 & stim2_f1 == 1 & stim2_voicing == 0){
      result <- 1
    }
    if(stim1_f1 == 1 & stim1_voicing == 0 & stim2_f1 == 0 & stim2_voicing == 1){
      result <- 1
    }
    #Anti-IPP diagonal (don't know which will be stim1 vs stim2)
    if(stim1_f1 == 1 & stim1_voicing == 1 & stim2_f1 == 0 & stim2_voicing == 0){
      result <- -1
    }
    if(stim1_f1 == 0 & stim1_voicing == 0 & stim2_f1 == 1 & stim2_voicing == 1){
      result <- -1
    }
  }
  result
}

#Add IPP column (1 if pair is on the IPP dimension, -1 if pair is on the anti-IPP,
# 0 if on neither)
ipp_labels <- to_vec(for(i in 1:nrow(distances)) ipp(distances[i,]))

distances <- cbind(distances, IPP = ipp_labels)



#Group by experiment
experiment_distances <- distances %>% 
  group_by(Experiment)


#Get just the IPP and anti-IPP rows
ipp_diagonals <- subset(experiment_distances, IPP == 1)
anti_ipp_diagonals <- subset(experiment_distances, IPP == -1)

#Estimate effect size: 
#Take mean distance for each diagonal

ipp_mean <-ipp_diagonals %>% summarize(
                              ipp_mean_dist = mean(Distance),
)


anti_ipp_mean <- anti_ipp_diagonals %>% summarize(
  anti_mean_dist = mean(Distance),
)

#Get differences between ipp and anti-ipp means for each experiment
effect_sizes = ipp_mean$ipp_mean_dist - anti_ipp_mean$anti_mean_dist
aggregated <- cbind(ipp_mean, EffectSize = effect_sizes)
aggregated <- cbind(aggregated, anti_mean_dist = anti_ipp_mean$anti_mean_dist)



#Estimate variability:
#Re-compute difference between diagonals for each trial, non-grouped
distances <- rename(distances, Type = IPP )
distances <- mutate(distances, Type = ifelse(Type==1,"IPP",Type))
distances <- mutate(distances, Type = ifelse(Type==-1,"Anti_IPP",Type))

test_distances <- filter(distances, Type != 0)

test_distances <- pivot_wider(test_distances,id_cols = c("Trial", "Experiment"),
                              names_from="Type",values_from = "Distance")

test_distances <- 
trial_diffs <- distances %>% group_by(Experiment) %>% group_by(Trial) %>%
  summarize (trial_effect = )
trial_ipp_diagonals <- subset(distances, IPP == 1)
trial_anti_ipp_diagonals <- subset(distances, IPP == -1)
trial_differences <- trial_ipp_diagonals %>% group_by(Trial) trial_ipp_diagonals$






#Given effect size, variability, and power, estimate number of trials
power.t.test(delta=effect_sizes, sd = sd_experiments, power = 0.8)
