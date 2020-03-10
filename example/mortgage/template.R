#!/usr/bin/env Rscript

library(readr)
library(tidyverse)
library(broom.mixed)
library(caret)

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
cv <- train(accept_scaled ~ female {{black}} {{housing_expense_ratio}}
    {{self_employed}} {{married}} {{bad_history}} {{PI_ratio}}
    {{loan_to_value}} {{denied_PMI}}, data = df, method='lm',
    trControl=trainControl(method='cv', number=5))
# normalize using max - min, because IQR is zero
nrmse = cv$results$RMSE / (max(df$accept_scaled) - min(df$accept_scaled))

# wrangle results
result <- tidy(model, conf.int = TRUE) %>%
    filter(term == 'female') %>%
    add_column(NRMSE = nrmse)

# output
write_csv(result, '../results/estimate_{{_n}}.csv')
