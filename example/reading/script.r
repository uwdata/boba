#!/usr/bin/env Rscript

library(readr)
library(lmerTest)
library(car)
library(psych)
library(scales)

speed_data <- read_csv('data.csv')

#calculate reading speed in WPM
speed_data$speed <- speed_data$num_words/(speed_data$adjust_rt/60000)

#remove retake participants
speed_data <- subset(speed_data, retake != 1)

#remove outliers
iqr = IQR(speed_data[speed_data$dyslexia_bin == 0,]$speed,na.rm=TRUE)
cutoff_high = median(speed_data$speed) +3*iqr #3*iqr=645, cutoff_high = 928

#-------remove trials based on speed-------
result_analysis <- speed_data[! speed_data$speed > cutoff_high, ]
result_analysis <- result_analysis[ ! result_analysis$speed < 10,]

#-------remove smartphone users-------
length(unique(subset(result_analysis$uuid, result_analysis$device=='smartphone')))
#remove 64 smartphone users, 363 trials
result_analysis <- result_analysis[! result_analysis$device == 'smartphone',]

#-------remove trials based on comprehension < 2/3-------
result_analysis <- result_analysis[ ! result_analysis$correct_rate < .6,]
#remove 111 trials

result_analysis$log_speed <- log(result_analysis$speed)

#dyslexia in three groups
model <- lmer(log_speed ~ img_width + num_words + page_condition*as.factor(dyslexia) + age + english_native + (1 | uuid), data = result_analysis)
AIC(model)
summary(model)
