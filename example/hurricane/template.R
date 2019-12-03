#!/usr/bin/env Rscript

library(readr)
library(MASS)
library(tidyverse)
library(broom.mixed)

df <- read_csv('../data.csv',
    col_types = cols(
        Year = col_integer(),
        Category = col_integer(),
        Gender_MF = col_integer(),
        alldeaths = col_integer()
    )) %>%
    # rename some variables
    dplyr::select(
        year = Year,
        name = Name,
        dam = NDAM,
        death = alldeaths,
        female = Gender_MF,
        masfem = MasFem,
        category = Category,
        pressure = Minpressure_Updated_2014,
        wind = HighestWindSpeed
    ) %>%
    # create new variables
    mutate(
        log_death = log(death + 1),
        log_dam = log(dam),
        post = ifelse(year>1979, 1, 0),
        zdam = scale(dam),
        zcat = scale(category),
        zmin = -scale(pressure),
        zwin = scale(wind),
        z3 = (zmin + zcat + zwin) / 3
    ) %>%
    # remove outliers
    filter(!(name %in% {{outliers}})) %>%
    # operationalize feminity
    mutate(
        feminity = {{feminity}},
        damage =  {{damage}}
    )

# --- (M) ols_regression
# OLS regression with log(deaths+1) as the dependent variable 
model <- lm(log_death ~ {{predictors}} {{covariates}}, data = df)
# get results
result <- tidy(model, conf.int = TRUE) %>%
    mutate(model = 'OLS regression')
# get predictions
pred <- predict(model) # se.fit = TRUE, interval="prediction"
disagg_pred <- df %>% 
    mutate(
        pred = pred,                         # add fitted predictions to dataframe
        pred = exp(pred) - 1                 # undo transformation of outcome variable (preprocessing)
    )
prediction <- disagg_pred %>%
    group_by(female) %>%                     # group by predictor(s) of interest
    summarize(pred = weighted.mean(pred))    # marninalize across other predictors

# --- (M) negative_binomial
# Negative binomial with deaths as the dependent variable
model <- glm.nb(death ~ {{predictors}} {{covariates}}, data = df)
# get results
result <- tidy(model, conf.int = TRUE) %>%
    mutate(model = 'Negative binomial')
# get predictions
pred <- predict(model) # type = "response", se.fit = TRUE, interval = "prediction"
disagg_pred <- df %>%
    mutate(
        pred = pred,                         # add fitted predictions to dataframe
        pred = exp(pred)                     # undo transformation of outcome variable (log link function)
    )
prediction <- disagg_pred %>%
    group_by(female) %>%                     # group by predictor(s) of interest
    summarize(pred = weighted.mean(pred))    # marninalize across other predictors

# --- (O)
# output
sink('../results/summary_{{_n}}.txt')
summary(model)
sink()
write_csv(result, '../results/table_{{_n}}.csv')
write_csv(disagg_pred, '../results/disagg_pred_{{_n}}.csv')
write_csv(prediction, '../results/prediction_{{_n}}.csv')
