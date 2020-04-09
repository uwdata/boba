#!/usr/bin/env Rscript
# --- (BOBA_CONFIG)
{
  "decisions": [
    {"var": "black", "options": ["+ black", ""]},
    {"var": "housing_expense_ratio", "options": ["+ housing_expense_ratio", ""]},
    {"var": "self_employed", "options": ["+ self_employed", ""]},
    {"var": "married", "options": ["+ married", ""]},
    {"var": "bad_history", "options": ["+ bad_history", ""]},
    {"var": "PI_ratio", "options": ["+ PI_ratio", ""]},
    {"var": "loan_to_value", "options": ["+ loan_to_value", ""]},
    {"var": "denied_PMI", "options": ["+ denied_PMI", ""]}
  ],
  "before_execute": "cp ../mortgage.csv ./ && rm -rf results && mkdir results",
  "visualizer": "visualizer_config.json"
}
# --- (END)

library(readr)
library(tidyverse)
library(broom.mixed)
source('../../../hurricane/boba_util.R') #fixme

# read data
df <- read_csv('../mortgage.csv', 
    col_types = cols(.default = col_double())) %>%
    mutate(
        accept_scaled = accept * 100
    ) %>%
    # here we drop all NAs for simplicity, but we will drop up to 7 more data
    # points in some models, which may cause discrepancy with Young et al.
    drop_na()

# linear regression
model <- lm(accept_scaled ~ female {{black}} {{housing_expense_ratio}}
    {{self_employed}} {{married}} {{bad_history}} {{PI_ratio}}
    {{loan_to_value}} {{denied_PMI}}, data = df)

# cross validation
fit <- cross_validation(df, model, 'accept_scaled')
# normalize using max - min, because IQR is zero
nrmse = fit / (max(df$accept_scaled) - min(df$accept_scaled))

# wrangle results
result <- tidy(model, conf.int = TRUE) %>%
    filter(term == 'female') %>%
    add_column(NRMSE = nrmse)

# get predictions
disagg_fit <- pointwise_predict(model, df) %>%
    select(
        observed = accept_scaled,
        expected = fit
    )

# get uncertainty in coefficient for female as draws from sampling distribution 
uncertainty <- sampling_distribution(model, 'female') %>%
    dplyr::select(estimate = coef)

# output
write_csv(result, '../results/estimate_{{_n}}.csv')
write_csv(disagg_fit, '../results/disagg_fit_{{_n}}.csv')
write_csv(uncertainty, '../results/uncertainty_{{_n}}.csv')
