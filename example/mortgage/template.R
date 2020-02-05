#!/usr/bin/env Rscript

library(readr)
library(tidyverse)
library(broom.mixed)

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

# get results
result <- tidy(model, conf.int = TRUE)

# get predictions
pred <- predict(model)
disagg_pred <- df %>% mutate(pred = pred)
prediction <- disagg_pred %>%
    group_by(female) %>%
    summarize(pred = weighted.mean(pred))

# only output relevant fields in disagg_pred
disagg_pred <- disagg_pred %>%
    select(
        observed = accept_scaled,
        pred = pred
    )

# output
sink('../results/summary_{{_n}}.txt')
summary(model)
sink()
write_csv(result, '../results/table_{{_n}}.csv')
write_csv(prediction, '../results/prediction_{{_n}}.csv')
write_csv(disagg_pred, '../results/disagg_pred_{{_n}}.csv')
