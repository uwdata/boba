#!/usr/bin/env Rscript
# --- (BOBA_CONFIG)
{
  "decisions": [
    {"var": "outliers", "options": [
        "c()",
        "c('Katrina')",
        "c('Katrina', 'Audrey')",
        "c('Katrina', 'Audrey', 'Sandy')",
        "c('Katrina', 'Audrey', 'Sandy', 'Andrew')",
        "c('Katrina', 'Audrey', 'Sandy', 'Andrew', 'Donna')"
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
    {"var": "undo_transform", "options": [
      "exp(value) - 1",
      "exp(value)",
      "exp(value) - 1"
    ]},
    {"var": "df", "options": [
        "pred$df",
        "df.residual(model)",
        "pred$df"
    ]}
  ],
  "constraints": [
    {"link": ["M", "undo_transform", "df"]}
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

# a function to undo data transformations when post-processing model predictions
untransform <- function(value) {
    return({{undo_transform}})
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
    pred <- predict(model, d_test)
    pred <- untransform(pred)

    mse = mse + sum((d_test$death - pred)^2)
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
fit = cross(df, lm, log_death ~ {{predictors}} {{covariates}}) # cross validation

# --- (M) negative_binomial
# Negative binomial with deaths as the dependent variable
model <- glm.nb(death ~ {{predictors}} {{covariates}}, data = df)
fit = cross(df, glm.nb, death ~ {{predictors}} {{covariates}}) # cross validation

# --- (M) anova
# ANOVA with log(deaths+1) as the dependent variable
model <- aov(log_death ~ {{predictors}} {{covariates}}, data = df)
fit = cross(df, aov, log_death ~ {{predictors}} {{covariates}}) # cross validation

# --- (O)
# normalize RMSE
nrmse = fit / (max(df$death) - min(df$death))

# get prediction
pred <- predict(model, se.fit = TRUE) # interval = "prediction"
disagg_pred <- df %>%
    mutate(
        fit = pred$fit,         # add fitted predictions and standard errors to dataframe
        se = pred$se.fit,
        df = {{df}}             # get degrees of freedom
    )

# aggregate predicted effect of female storm name
prediction <- disagg_pred %>%
    group_by(female) %>%                            # group by predictor(s) of interest
    summarize(
        log_pred = weighted.mean(fit),              # marninalize across other predictors
        pred = untransform(log_pred)                # undo transformation of outcome variable
    ) %>%        
    compare_levels(pred, by = female) %>%
    ungroup() %>%
    dplyr::select(pred = pred) %>%
    add_column(NRMSE = nrmse)                       # add cross validatation metric

# propagate uncertainty in fit to model predictions
uncertainty <- disagg_pred %>%
    mutate(
        .draw = list(1:1000),                       # generate list of draw numbers
        pred_t = map(df, ~rt(1000, .))              # simulate draws as t-scores
    ) %>%
    unnest(cols = c(".draw", "pred_t")) %>%
    mutate(log_pred = pred_t * se + fit) %>%        # scale and shift t-scores to create predictive distribution 
    group_by(.draw, female) %>%                     # group by predictor(s) of interest
    summarize(
        log_pred = weighted.mean(log_pred),         # marninalize across other predictors
        pred = untransform(log_pred)                # undo transformation of outcome variable
    ) %>%
    compare_levels(pred, by = female) %>%
    ungroup() %>%
    dplyr::select(pred = pred)

# only output relevant fields in disagg_pred
disagg_pred <- disagg_pred %>%
    mutate(pred = untransform(fit)) %>%             # undo transformation of outcome variable
    dplyr::select(
        observed = death,
        pred = pred
    )

# output
write_csv(disagg_pred, '../results/disagg_pred_{{_n}}.csv')
write_csv(prediction, '../results/prediction_{{_n}}.csv')
write_csv(uncertainty, '../results/uncertainty_{{_n}}.csv')
