library("plyr")
library("tidyverse")
library("comprehenr")
library("lmerTest")




setwd("~/CNN_Perceptual_Integration_Channel_Bias/Experiment/analysis")



distances <-
  list.files(path = "../WaveformCNN/discrim_results/", pattern = "*.csv", full.names = TRUE) %>% 
  map_df(~read.csv(.))




#For each task:

#Hard-code identify which diagonal is the IPP and add as column
#IPP: 1
#Anti-IPP: -1
ipp <- function(row){
  anti_ipp_symbol <- -1
  ipp_symbol <- 1
    
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
      result <- ipp_symbol
    }
    if(stim1_f0 == 1 & stim1_Closure == 1 & stim2_f0 == 0 & stim2_Closure == 0){
      result <- ipp_symbol
    }
    #Anti-IPP diagonal (don't know which will be stim1 vs stim2)
    if(stim1_f0 == 0 & stim1_Closure == 1 & stim2_f0 == 1 & stim2_Closure == 0){
      result <- anti_ipp_symbol
    }
    if(stim1_f0 == 1 & stim1_Closure == 0 & stim2_f0 == 0 & stim2_Closure == 1){
      result <- anti_ipp_symbol
    }
  }
  else if(experiment == "f1_closure_dur_high_f0" | experiment == "f1_closure_dur_low_f0"){
    #IPP diagonal (don't know which will be stim1 vs stim2)
    if(stim1_f1 == 0 & stim1_Closure == 0 & stim2_f1 == 1 & stim2_Closure == 1){
      result <- ipp_symbol
    }
    if(stim1_f1 == 1 & stim1_Closure == 1 & stim2_f1 == 0 & stim2_Closure == 0){
      result <- ipp_symbol
    }
    #Anti IPP diagonal (don't know which will be stim1 vs stim2)
    if(stim1_f1 == 0 & stim1_Closure == 1 & stim2_f1 == 1 & stim2_Closure == 0){
      result <- anti_ipp_symbol
    }
    if(stim1_f1 == 1 & stim1_Closure == 0 & stim2_f1 == 0 & stim2_Closure == 1){
      result <- anti_ipp_symbol
    }
  }
  else if(experiment == "f0_voicing_dur"){
    #IPP diagonal (don't know which will be stim1 vs stim2)
    if(stim1_f0 == 0 & stim1_voicing == 1 & stim2_f0 == 1 & stim2_voicing == 0){
      result <- ipp_symbol
    }
    if(stim1_f0 == 1 & stim1_voicing == 0 & stim2_f0 == 0 & stim2_voicing == 1){
      result <- ipp_symbol
    }
    #Anti IPP diagonal (don't know which will be stim1 vs stim2)
    if(stim1_f0 == 1 & stim1_voicing == 1 & stim2_f0 == 0 & stim2_voicing == 0){
      result <- anti_ipp_symbol
    }
    if(stim1_f0 == 0 & stim1_voicing == 0 & stim2_f0 == 1 & stim2_voicing == 1){
      result <- anti_ipp_symbol
    }
  }
  else if (experiment == "f1_voicing_dur"){
    #IPP diagonal (don't know which will be stim1 vs stim2)
    if(stim1_f1 == 0 & stim1_voicing == 1 & stim2_f1 == 1 & stim2_voicing == 0){
      result <- ipp_symbol
    }
    if(stim1_f1 == 1 & stim1_voicing == 0 & stim2_f1 == 0 & stim2_voicing == 1){
      result <- ipp_symbol
    }
    #Anti-IPP diagonal (don't know which will be stim1 vs stim2)
    if(stim1_f1 == 1 & stim1_voicing == 1 & stim2_f1 == 0 & stim2_voicing == 0){
      result <- anti_ipp_symbol
    }
    if(stim1_f1 == 0 & stim1_voicing == 0 & stim2_f1 == 1 & stim2_voicing == 1){
      result <- anti_ipp_symbol
    }
  }
  result
}

#Add IPP column (1 if pair is on the IPP dimension, -1 if pair is on the anti-IPP,
# 0 if on neither)
ipp_labels <- to_vec(for(i in 1:nrow(distances)) ipp(distances[i,]))

distances <- cbind(distances, Type = ipp_labels)

#Only pay attention to IPP and Anti-IPP diagonals
test_distances <- filter(distances, Type != 0)

####Make linear model version of data:####
#Change Type column name to IPP and Trial column name to Model
#and change values to Anti-IPP = 0 and IPP = 1
lm_distances <- mutate(test_distances, Type = ifelse(Type==-1,-.5,Type))
lm_distances <- mutate(lm_distances, Type = ifelse(Type==1,.5,Type))
lm_distances <- rename(lm_distances, IPP = Type)
lm_distances <- rename(lm_distances, Model = Trial)


####Make estimating effect sizes version of data:####
#Make IPP labels more readable for effect sizes version
test_distances <- mutate(test_distances, Type = ifelse(Type==1,"IPP",Type))
test_distances <- mutate(test_distances, Type = ifelse(Type==-1,"Anti_IPP",Type))


#Merge IPP and Anti-IPP results into single row for each experiment, each trial
#To compute effect sizes 
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



###Regression Modeling###
cue_pairings_results <- split(lm_distances, lm_distances$Experiment)

model_results <- list()
for (cue_pairing in cue_pairings_results){
  pairing_name <- cue_pairing[1,]$Experiment
  output <- lmer("Distance~IPP+(1|Model)", data=cue_pairing)
  model_results <- c(model_results, pairing_name=output)
  print(pairing_name)
  print(output)
  print(anova(output))
  print("")
  print("")
}

##Plotting###
pretty_title <- function(name){
  title <- name
  if (name=="f1_voicing_dur"){
    title <- "F1 x Closure Voicing Duration"
  }
  if (name=="f0_voicing_dur"){
    title <- "f0 x Closure Voicing Duration"
  }
  if(name=="f1_closure_dur_low_f0"){
    title <- "F1 x Closure Duration (low f0)"
  }
  if(name=="f1_closure_dur_high_f0"){
    title <- "F1 x Closure Duration (high f0)"
  }
  if(name=="f0_closure_dur_high_f1"){
    title <- "F0 x Closure Duration (high F1)"
  }
  if(name=="f0_closure_dur_low_f1"){
    title <- "F0 x Closure Duration (low F1)"
  }
  title
}

#Make data nice for plotting xy plots
cue_pairings_results_wide <- rename(test_distances, Model=Trial)
cue_pairings_results_wide <- split(cue_pairings_results_wide, cue_pairings_results_wide$Experiment)

xy_plots <- list()
for (cue_pairing in cue_pairings_results_wide){
  pairing_name <- cue_pairing[1,]$Experiment
  title <- pretty_title(pairing_name)
  p <- ggplot(data=cue_pairing, aes(x=IPP, y=Anti_IPP)) + ggtitle(title)+
    geom_point() + xlab("Distance on Natural Dimension") + 
    ylab("Distance on Mismatched Dimension") 
  print(p)
  dev.copy(pdf, paste("xy_plots/xy_",title,".pdf", sep=""))
  dev.off()
  xy_plots <- c(xy_plots, p)
}
#xy_plots[[2]]

#Xy plot for all data, not split
p <- ggplot(data=test_distances, aes(x=IPP, y=Anti_IPP))+ 
  ggtitle("Cosine distances across model versions")+
  geom_point() + xlab("Distance on Natural Dimension") + 
  ylab("Distance on Mismatched Dimension") 
p


#Make data nice for box plots
long_lm <- mutate(lm_distances, IPP = ifelse(IPP==-.5,"Mismatched",IPP))
long_lm <- mutate(long_lm, IPP = ifelse(IPP==.5,"Natural",IPP))
cue_pairings_long <-  split(long_lm, long_lm$Experiment)
box_plots <- list()
for (cue_pairing in cue_pairings_long){
  pairing_name <- cue_pairing[1,]$Experiment
  title <- pretty_title(pairing_name)
  p <- ggplot(data=cue_pairing, aes(x=IPP, y=Distance)) + ggtitle(title)+
    geom_boxplot() + xlab("Stimuli Dimension") + 
    ylab("Distance")
  print(p)
  dev.copy(pdf, paste("box_plots/box_plot_",title,".pdf", sep=""))
  dev.off()
  box_plots <- c(box_plots, p)
}
box_plots[[2]]


#Histograms of cosine distances
histograms <- list()
for (cue_pairing in cue_pairings_long){
  pairing_name <- cue_pairing[1,]$Experiment
  title <- pretty_title(pairing_name)
  p <- ggplot(data=cue_pairing, aes(x=Distance, fill=IPP)) + ggtitle(title)+
    geom_histogram() + xlab("Cosine Distance") + 
    ylab("Frequency") + scale_color_brewer(palette = "PuOr")
  print(p)
  dev.copy(pdf, paste("histograms/histogram_",title,".pdf", sep=""))
  dev.off()
  histograms <- c(histograms, p)
}
 


#From https://stackoverflow.com/questions/1169539/linear-regression-and-group-by-in-r
#Regression model to determine how task dimension predicts distance
# models <- dlply(distances, "Experiment", function(df){
#   lm(Distance ~ Type, data=df)
# })
# 
# ldply(models, coef)
# 
# # Print the summary of each model
# l_ply(models, summary, .print = TRUE)
#factor experiment number and see if there's an interaction between experiment number
#/experiment type and trial


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
