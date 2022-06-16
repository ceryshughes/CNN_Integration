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

distances <- cbind(distances, Type = ipp_labels)




#Make IPP labels more readable
distances <- mutate(distances, Type = ifelse(Type==1,"IPP",Type))
distances <- mutate(distances, Type = ifelse(Type==-1,"Anti_IPP",Type))

#Only pay attention to IPP and Anti-IPP diagonals
test_distances <- filter(distances, Type != 0)

#Merge IPP and Anti-IPP results into single row for each experiment, each trial
test_distances <- pivot_wider(test_distances,id_cols = c("Trial", "Experiment"),
                              names_from="Type",values_from = "Distance")

#Compute difference between IPP distance and Anti-IPP distance
test_distances <- mutate(test_distances, Effect = IPP - Anti_IPP)

#Compute mean difference and standard deviation across trials, for each experiment
experiment_distances <- group_by(test_distances, Experiment)
experiment_sds <- summarize(experiment_distances, stdev = sd(Effect))
experiment_effects <- summarize(experiment_distances, mean_diff = mean(Effect))
agg_results <- merge(experiment_sds, experiment_effects, by="Experiment")


#Compute how many trials are necessary for 0.8 power for each experiment
#given estimated effect size and standard dev for each experiment
num_trials <- function(row){
  stdev = row[[2]]
  effect = row[[3]]
  power.t.test(delta=effect, sd = stdev, power = 0.8, n= NULL)
  
}  

num_trials_per_exp <- to_vec(for(i in 1:nrow(agg_results)) num_trials(agg_results[i,])$n)
agg_results <- mutate(agg_results, Required_Trial_Num=num_trials_per_exp)





# #Group by experiment
# experiment_distances <- distances %>% 
#   group_by(Experiment)


#Get just the IPP and anti-IPP rows
# ipp_diagonals <- subset(experiment_distances, IPP == 1)
# anti_ipp_diagonals <- subset(experiment_distances, IPP == -1)

#Estimate effect size: 
#Take mean distance for each diagonal

# ipp_mean <-ipp_diagonals %>% summarize(
#                               ipp_mean_dist = mean(Distance),
# )
# 
# 
# anti_ipp_mean <- anti_ipp_diagonals %>% summarize(
#   anti_mean_dist = mean(Distance),
# )

#Get differences between ipp and anti-ipp means for each experiment
# effect_sizes = ipp_mean$ipp_mean_dist - anti_ipp_mean$anti_mean_dist
# aggregated <- cbind(ipp_mean, EffectSize = effect_sizes)
# aggregated <- cbind(aggregated, anti_mean_dist = anti_ipp_mean$anti_mean_dist)
