#!/usr/bin/env Rscript
# --- (BOBA_CONFIG)
{
  "graph": [
    "RC->LM1->O1",
    "RC->LM2->O2",
    "OLR1->O1",
    "OLR2->O2"
  ],
  "decisions": [
    {"var": "brmsfamily", "options": ["shifted_lognormal", "lognormal"]}
  ],
  "outputs": [
    {"name": "aic/waic", "value": "aic"}
  ],
  "before_execute": "cp ../../data.csv ./code/ && mkdir results"
}
# --- (END)

library(readr)
library(lmerTest)
library(car)
library(psych)
library(scales)
library(brms)
library(ordinal)

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

# wrangle variables
result_analysis$log_speed <- log(result_analysis$speed)
result_analysis$dyslexia = as.factor(result_analysis$dyslexia)
result_analysis$correct_num = round(result_analysis$correct_rate * 3, 0)
result_analysis$acc = result_analysis$correct_num + 1
result_analysis$correct_num = as.factor(result_analysis$correct_num)

# --- (RC)
# remove trials based on comprehension < 2/3
# removed 111 trials
result_analysis <- result_analysis[ ! result_analysis$correct_rate < .6,]

# --- (LM1)
# fit linear mixed model
model <- lmer(log_speed ~ page_condition*dyslexia + img_width + num_words + age + english_native + (1 | uuid),
              data = result_analysis)
print.odds = FALSE

# --- (OLR1)
# fit ordinal logistic regression using accuracy as DV
model <- clmm(correct_num ~ page_condition*dyslexia + num_words + age + english_native + (1 | uuid),
              data=result_analysis)
print.odds = TRUE

# --- (LM2)
# fit bayesian model
model <- brm(speed ~ page_condition*dyslexia + img_width + num_words + age + english_native + (1 | uuid),
             data = result_analysis, family = {{brmsfamily}}(), file = '../results/brmsfit_{{_n}}',
             save_all_pars = TRUE, silent = TRUE, refresh = 0, seed = 0,
             chains = 4, cores = 4, iter = 1000)

# --- (OLR2)
# fit bayesian model to accuracy
model <- brm(acc ~ page_condition*dyslexia + num_words + age + english_native + (1 | uuid),
             data = result_analysis, family = cumulative(), file = '../results/brmsfit_{{_n}}',
             save_all_pars = TRUE, silent = TRUE, refresh = 0, seed = 0,
             chains = 4, cores = 4, iter = 1000)

# --- (O1)
aic = AIC(model)
sink('../results/summary_{{_n}}.txt')
summary(model)

if(print.odds){
    print("Odds ratio:")
    exp(coef(model))
}

# --- (O2)
# evaluate fit
aic = waic(model)$waic

# output resultsf
sink('../results/summary_{{_n}}.txt')
summary(model)
sink()
pdf(file="../results/plots_{{_n}}.pdf")
plot(model)
marginal_effects(model)
