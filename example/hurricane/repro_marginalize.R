#!/usr/bin/env Rscript
# Replicate prior work's results using their marginalization approach
# --- (BOBA_CONFIG)
{
  "decisions": [
    {"var": "outliers", "options": [
        "c()",
        "c('Katrina')",
        "c('Katrina', 'Audrey')"
    ]},
    {"var": "leverage_points", "options": [
        "c()",
        "c('Sandy')",
        "c('Sandy', 'Andrew')",
        "c('Sandy', 'Andrew', 'Donna')"
    ]},
    {"var": "feminity", "options": ["female", "masfem"]},
    {"var": "feminity_prediction_levels", "options": ["c(0, 1)", "c(2.53, 8.29)"]},
    {"var": "damage", "options": ["dam", "log_dam"]},
    {"var": "predictors", "options": [
        "feminity * damage",
        "feminity + damage + pressure + feminity:damage + feminity:pressure",
        "feminity + damage + zwin + feminity:damage + feminity:zwin",
        "feminity + damage + zcat + feminity:damage + feminity:zcat",
        "feminity + damage + z3 + feminity:damage + feminity:z3",
        "feminity + damage + z3"
    ]},
    {"var": "covariates", "options": [
        "",
        "+ year:damage",
        "+ post:damage"
    ]},
    {"var": "predictor_list", "options": [
        "damage",
        "damage, pressure",
        "damage, zwin",
        "damage, zcat",
        "damage, z3",
        "damage, z3"
    ]},
    {"var": "covariate_list", "options": [
        "",
        ", year",
        ", post"
    ]},
    {"var": "back_transform", "options": [
      "exp(mu + sigma^2/2) - 1",
      "mu"
    ]},
    {"var": "df", "options": [
        "inference$df",
        "df.residual(model)"
    ]}
  ],
  "constraints": [
    {"link": ["feminity", "feminity_prediction_levels"]},
    {"link": ["M", "back_transform", "df"]},
    {"link": ["predictors", "predictor_list"]},
    {"link": ["covariates", "covariate_list"]}
  ],
  "before_execute": "cp ../data.csv ./ && rm -rf results && mkdir results"
}
# --- (END)

library(readr)
library(MASS)
library(modelr)
library(tidyverse)
library(broom.mixed)
library(tidybayes)

# a function for post-processing predicted means and standard deviations into expected number of deaths
pred2expectation <- function(mu, sigma) {
    return({{back_transform}})
}

# read and process data
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
        zcat = as.numeric(scale(category)),
        zmin = -scale(pressure),
        zwin = as.numeric(scale(wind)),
        z3 = as.numeric((zmin + zcat + zwin) / 3)
    ) %>%
    # remove outliers
    filter(!(name %in% {{outliers}})) %>%
    filter(!(name %in% {{leverage_points}})) %>%
    # operationalize feminity
    mutate(
        feminity = {{feminity}},
        damage =  {{damage}}
    )

# --- (M) ols_regression
# OLS regression with log(deaths+1) as the dependent variable 
model <- lm(log_death ~ {{predictors}} {{covariates}}, data = df)

# --- (M) negative_binomial
# Negative binomial with deaths as the dependent variable
model <- glm.nb(death ~ {{predictors}} {{covariates}}, data = df)

# --- (O)
# create a data frame where covariates are at their means
dmeans <- df %>%
    summarise_at(vars({{predictor_list}} {{covariate_list}}), mean) %>%
    group_by({{predictor_list}} {{covariate_list}}) %>%
    data_grid(feminity = {{feminity_prediction_levels}})%>%
    ungroup()

# predict
pred <- predict(model, dmeans, se.fit = TRUE, type = "response")
expectation <- dmeans %>%
    mutate(
        fit = pred$fit,
        sigma = sigma(model),
        expected_deaths = pred2expectation(fit, sigma)
    )%>%
    compare_levels(expected_deaths, by = feminity) %>%
    ungroup() %>%
    dplyr::select(expected_diff = expected_deaths)

# get predictive check for original dataset from model
pred <- predict(model, df, type = "response")
disagg_fit <- df %>%
    mutate(
        fit = pred,                                 # get fitted predictions
        sigma = sigma(model),                       # get residual standard deviation
        pred_deaths = pred2expectation(fit, sigma)  # transform to deaths
    ) %>%
    dplyr::select(
        observed = death,
        expected = pred_deaths
    )

# output
write_csv(expectation, '../results/estimate_{{_n}}.csv')
write_csv(disagg_fit, '../results/disagg_fit_{{_n}}.csv')
