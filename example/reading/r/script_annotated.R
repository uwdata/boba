#!/usr/bin/env Rscript

library(readr)
library(lmerTest)
library(car)
library(psych)
library(scales)
library(brms)

speed_data <- read_csv('data.csv')

# calculate reading speed in WPM
speed_data$speed <- speed_data$num_words/(speed_data$adjust_rt/60000)

# remove retake participants
speed_data <- subset(speed_data, retake != 1)

# remove outliers
iqr = IQR(speed_data[speed_data$dyslexia_bin == 0,]$speed,na.rm=TRUE)
cutoff_high = median(speed_data$speed) +3*iqr #3*iqr=645, cutoff_high = 928

# remove trials based on speed
result_analysis <- speed_data[! speed_data$speed > cutoff_high, ]
result_analysis <- result_analysis[ ! result_analysis$speed < 10,]

# remove smartphone users
# removed 64 smartphone users, 363 trials
result_analysis <- result_analysis[! result_analysis$device == 'smartphone',]

# remove trials based on comprehension < 2/3
# removed 111 trials
result_analysis <- result_analysis[ ! result_analysis$correct_rate < .6,]

# wrangle variables
result_analysis$log_speed <- log(result_analysis$speed)
result_analysis$dyslexia = as.factor(result_analysis$dyslexia)

# --- (M1)
# fit linear mixed model
model <- lmer(log_speed ~ img_width + num_words + page_condition*dyslexia + age + english_native + (1 | uuid),
              data = result_analysis)
summary(model)

# --- (M2)
# fit bayesian model
model <- brm(speed ~ img_width + num_words + page_condition*dyslexia + age + english_native + (1 | uuid),
             data = result_analysis, family = shifted_lognormal(), chains = 4, cores = 4, iter = 1000)
summary(model)
pdf(file="./results/out_{{_n}}.pdf")
plot(model, pars = c("page_condition", "dyslexia", "img_width", "num_words", "age", "english_native"))
marginal_effects(model)
