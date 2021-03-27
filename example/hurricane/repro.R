#!/usr/bin/env Rscript
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
    {"var": "back_transform", "options": [
      "exp(mu + sigma^2/2) - 1",
      "mu"
    ]}
  ],
  "constraints": [
    {"link": ["Model", "back_transform"]}
  ],
  "before_execute": "cp ../data.csv ./ && rm -rf results && mkdir results",
  "after_execute": "cp ../stacking_weights.R ./",
  "visualizer": "visualizer_config.json"
}
# --- (END)

suppressPackageStartupMessages(library(readr))
suppressPackageStartupMessages(library(MASS))
suppressPackageStartupMessages(library(modelr))
suppressPackageStartupMessages(library(tidyverse))
suppressPackageStartupMessages(library(broom.mixed))
suppressPackageStartupMessages(library(tidybayes))
source('../../boba_util.R') #fixme

# a function for post-processing predicted means and standard deviations into expected number of deaths
pred2expectation <- function(mu, sigma) {
  return({{back_transform}})
}

# get expectation per data point
compute_exp <- function (model, df) {
  disagg_fit <- pointwise_predict(model, df) %>%
    mutate(expected = pred2expectation(fit, sigma))
  return(disagg_fit)
}

# read and process data
full <- read_csv('../data.csv',
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
    id = row_number(),
    log_death = log(death + 1),
    log_dam = log(dam),
    post = ifelse(year>1979, 1, 0),
    zdam = scale(dam),
    zcat = as.numeric(scale(category)),
    zmin = -scale(pressure),
    zwin = as.numeric(scale(wind)),
    z3 = as.numeric((zmin + zcat + zwin) / 3)
  ) %>%
  # operationalize feminity
  mutate(
    feminity = {{feminity}},
    damage =  {{damage}}
  )

df <- full %>%
  # remove outliers
  filter(!(name %in% {{outliers}})) %>%
  filter(!(name %in% {{leverage_points}}))

# --- (Model) ols_regression
# OLS regression with log(deaths+1) as the dependent variable 
model <- lm(log_death ~ {{predictors}} {{covariates}}, data = df)

# --- (Model) negative_binomial
# Negative binomial with deaths as the dependent variable
model <- glm.nb(death ~ {{predictors}} {{covariates}}, data = df)

# --- (O)
# cross validation
fit <- cross_validation(df, model, "death",
  func = function (m, d) compute_exp(m, d)$expected)
nrmse = fit / (max(df$death) - min(df$death))

# stacking
loglik <- df %>%
  add_column(loglik = stacking(df, model)) %>%
  dplyr::select(id, loglik) %>%
  right_join(full, by='id')
# add missing log likelihood
if (nrow(loglik) != nrow(df)) {
  idx <- filter(loglik, is.na(loglik))
  loglik$loglik[idx$id] <- compute_loglik(model, idx)
}
loglik <- dplyr::select(loglik, loglik)

# permutation test
null.dist <- permutation_test(df, model, c("female", "masfem", "feminity"), N = 100,
  func = function (m, d) margins(compute_exp(m, d), "female", "expected")$expected) %>%
  dplyr::select(expected_diff = value)

# get prediction
disagg_fit <- compute_exp(model, df)

# aggregate fitted effect of female storm name
expectation <- margins(disagg_fit, "female", "expected") %>%
  dplyr::select(expected_diff = expected) %>%
  add_column(NRMSE = nrmse)  # add cross validation metric

# propagate uncertainty in fit to model predictions
uncertainty <- disagg_fit %>%
    mutate(
        .draw = list(1:200),                               # generate list of draw numbers
        t = map(df, ~rt(200, .)),                          # simulate draws from t distribution to transform into means
        x = map(df, ~rchisq(200, .))                       # simulate draws from chi-squared distribution to transform into sigmas
    ) %>%
    unnest(cols = c(".draw", "t", "x")) %>%
    mutate(
        mu = t * se.fit + fit,                              # scale and shift t to get a sampling distribution of means
        sigma = sqrt(df * se.residual^2 / x),               # scale and take inverse of x to get a sampling distribution of sigmas
        expected_deaths = pred2expectation(mu, sigma)
    ) %>%
    group_by(.draw, female) %>%                             # group by predictor(s) of interest
    summarize(expected_deaths = mean(expected_deaths)) %>%  # marninalize across other predictors
    compare_levels(expected_deaths, by = female) %>%
    ungroup() %>%
    dplyr::select(expected_diff = expected_deaths)

# only output relevant fields in disagg_fit
disagg_fit <- disagg_fit %>%
  dplyr::select(
    observed = death,
    expected = expected
  )

# output
write_csv(expectation, '../results/estimate_{{_n}}.csv')
write_csv(disagg_fit, '../results/disagg_fit_{{_n}}.csv')
write_csv(uncertainty, '../results/uncertainty_{{_n}}.csv')
write_csv(null.dist, '../results/null_{{_n}}.csv')
write_csv(loglik, '../results/loglik_{{_n}}.csv')
