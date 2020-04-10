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
  "visualizer": "visualizer_config.json"
}
# --- (END)

library(readr)
library(MASS)
library(modelr)
library(tidyverse)
library(broom.mixed)
library(tidybayes)
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

# get the pointwise log likelihood for stacking
# df is the dataset without outliers, full is the original dataset
stacking <- function (model, df, full) {
  indices = cv_split(nrow(df), folds = 5)
  pointwise_density <- c()

  for (i in c(1:nrow(indices))) {
    d_train = df[indices$train[[i]], ]
    d_test = df[indices$test[[i]], ]

    m1 <- update(model, . ~ ., data = d_train)
    mu <- predict(m1, d_test, type = "response")
    sigma <- sigma(m1)
    pointwise_density <- append(pointwise_density,
      log(dnorm(d_test$death, mu, sigma)+1e-307))
  }

  if (nrow(df) != nrow(full)) {
    # todo
  }

  return(pointwise_density)
}

# permutation test to get the null distribution
permutation_test <- function (df, model, N=200) {
  # ensure we have the same random samples across universe runs
  set.seed(3040)

  res = lapply(1:N, function (i) {
    # shuffle
    pm <- df[sample(nrow(df)), ]
    df2 = df %>% dplyr::select(-c(female, feminity, masfem)) %>%
      add_column(female=pm$female, feminity=pm$feminity, masfem=pm$masfem)

    # fit the model
    m1 <- update(model, . ~ ., data = df2)
    exp <- margins(compute_exp(m1, df2), "female", "expected")
    return(exp$expected)
  })

  # remove seed because set seed is global
  rm(.Random.seed, envir=.GlobalEnv)

  return(enframe(unlist(res)))
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

# permutation test
null.dist <- permutation_test(df, model, 100) %>%
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
    expected = expected_deaths
  )

# output
write_csv(expectation, '../results/estimate_{{_n}}.csv')
write_csv(disagg_fit, '../results/disagg_fit_{{_n}}.csv')
write_csv(uncertainty, '../results/uncertainty_{{_n}}.csv')
write_csv(null.dist, '../results/null_{{_n}}.csv')
