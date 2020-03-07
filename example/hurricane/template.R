#!/usr/bin/env Rscript

library(readr)
library(MASS)
library(modelr)
library(tidyverse)
library(broom.mixed)
library(tidybayes)

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

# --- (M) negative_binomial
# Negative binomial with deaths as the dependent variable
model <- glm.nb(death ~ {{predictors}} {{covariates}}, data = df)
# get results
result <- tidy(model, conf.int = TRUE) %>%
    mutate(model = 'Negative binomial')

# --- (M) anova
# ANOVA with log(deaths+1) as the dependent variable
model <- aov(log_death ~ {{predictors}} {{covariates}}, data = df)
# get results
result <- tidy(model, conf.int = TRUE) %>%
    mutate(model = 'ANOVA')

# --- (O)
# get predictions
pred <- predict(model) # se.fit = TRUE, interval="prediction"
disagg_pred <- df %>%
    mutate(
        pred = pred,                                # add fitted predictions to dataframe
        pred = {{undo_transform}}                   # undo transformation of outcome variable (preprocessing)
    )

prediction <- disagg_pred %>%
    group_by(female) %>%                            # group by predictor(s) of interest
    summarize(pred = weighted.mean(pred))           # marninalize across other predictors

# uncertainty
uncertainty <- df %>%
    group_by({{predictor_list}} {{covariate_list}}) %>%
    data_grid(female) %>%
    augment(model, newdata = .) %>%
    mutate(
        df = df.residual(model),                    # calculate degrees of freedom
        .draw = list(1:200),                        # generate list of draw numbers
        pred_t = map(df, ~rt(200, .))               # simulate draws as t-scores
    ) %>%
    unnest(cols = c(".draw", "pred_t")) %>%
    mutate(
        pred = pred_t * .se.fit + .fitted,          # scale and shift t-scores to create predictive distribution
        pred = {{undo_transform}}                   # undo transformation of outcome variable (preprocessing)
    ) %>%
    group_by(.draw, female) %>%                     # group by predictor(s) of interest
    summarize(pred = weighted.mean(pred)) %>%       # marginalize across other predictors
    compare_levels(pred, by = female)

# only output relevant fields in disagg_pred
disagg_pred <- disagg_pred %>%
    dplyr::select(
        observed = death,
        pred = pred
    )

# output
sink('../results/summary_{{_n}}.txt')
summary(model)
sink()
write_csv(result, '../results/table_{{_n}}.csv')
write_csv(disagg_pred, '../results/disagg_pred_{{_n}}.csv')
write_csv(prediction, '../results/prediction_{{_n}}.csv')
write_csv(uncertainty, '../results/uncertainty_{{_n}}.csv')
