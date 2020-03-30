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
    ]},
    {"var": "df", "options": [
        "pred$df",
        "df.residual(model)"
    ]}
  ],
  "constraints": [
    {"link": ["M", "back_transform", "df"]}
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

# a custom function for cross validation
cross <- function (df, func, fml, folds = 5) {
  l = nrow(df) %/% folds
  mse = 0
  for (i in c(1:folds)) {
    # properly splitting train/test
    i1 = l*(i-1)+1
    i2 = l*i
    d_test = df[i1:i2, ]
    if (i1 > 1) {
      if (i2+1 < nrow(df)) {
        d_train = rbind(df[1:(i1-1), ], df[(i2+1):nrow(df), ])
      } else {
        d_train = df[1:(i1-1), ]
      }
    } else {
      d_train = df[(i2+1):nrow(df), ]
    }

    model <- func(fml, data = d_train)
    mu <- predict(model, d_test, type = "response")
    sigma <- sigma(model)
    expected_deaths <- pred2expectation(mu, sigma)

    mse = mse + sum((d_test$death - expected_deaths)^2)
  }

  mse = sqrt(mse / nrow(df))
  return(mse)
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
fit = cross(df, lm, log_death ~ {{predictors}} {{covariates}}) # cross validation

# --- (M) negative_binomial
# Negative binomial with deaths as the dependent variable
model <- glm.nb(death ~ {{predictors}} {{covariates}}, data = df)
fit = cross(df, glm.nb, death ~ {{predictors}} {{covariates}}) # cross validation

# --- (O)
# normalize RMSE
nrmse = fit / (max(df$death) - min(df$death))

# get prediction
pred <- predict(model, se.fit = TRUE, type = "response")
disagg_fit <- df  %>%
    mutate(
        fit = pred$fit,                            # add inferential fits and standard errors to dataframe
        se.fit = pred$se.fit,
        df = {{df}},                                        # get degrees of freedom
        sigma = sigma(model),                               # get residual standard deviation
        se.residual = sqrt(sum(residuals(model)^2) / df)    # get residual standard errors
    )

# aggregate fitted effect of female storm name
expectation <- disagg_fit %>%
    mutate(expected_deaths = pred2expectation(fit, sigma)) %>%
    group_by(female) %>%                                            # group by predictor(s) of interest
    summarize(expected_deaths = weighted.mean(expected_deaths)) %>% # marninalize across other predictors
    compare_levels(expected_deaths, by = female) %>%
    ungroup() %>%
    dplyr::select(expected_diff = expected_deaths) %>%
    add_column(NRMSE = nrmse)                                       # add cross validatation metric

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
    mutate(expected_deaths = pred2expectation(fit, sigma)) %>%
    dplyr::select(
        observed = death,
        expected = expected_deaths
    )

# output
write_csv(expectation, '../results/estimate_{{_n}}.csv')
write_csv(disagg_fit, '../results/disagg_fit_{{_n}}.csv')
write_csv(uncertainty, '../results/uncertainty_{{_n}}.csv')
