#!/usr/bin/env Rscript

library(readr)
library(MASS)
library(tidyverse)
library(broom.mixed)

df <- read_csv('../data.csv') %>%
    # rename some variables
    select(
        year = Year,
        name = Name,
        dam = NDAM,
        death = alldeaths,
        female = Gender_MF,
        masfem = MasFem,
        category = Category,
        zdam = ZNDAM,
        pressure = MinPressure_before,
        zmin = ZMinPressure_A
    ) %>%
    # create new variables
    mutate(
        log_death = log(death + 1),
        log_dam = log(dam),
        post = ifelse(year>1979, 1, 0),
        zcat = scale(category),
        zmin = -zmin,
        zwin = scale(dam), # fixme: need data of maximum wind of hurricane
        z3 = (zmin + zcat + zwin) / 3
    ) %>%
    # remove outliers
    filter(!(name %in% {{outliers}})) %>%
    # operationalize feminity
    mutate(
        feminity = {{feminity}},
        damage =  {{damage}}
    )

# --- (LM)
# OLS regression with log(deaths+1) as the dependent variable 
model <- lm(log_death ~ {{predictions}} {{covariates}}, data = df)
result <- tidy(model, conf.int = TRUE) %>%
    mutate(model = 'OLS regression')

# --- (NB)
# Negative binomial with deaths as the dependent variable
model <- glm.nb(death ~ {{predictions}} {{covariates}}, data = df)
result <- tidy(model, conf.int = TRUE) %>%
    mutate(model = 'Negative binomial')

# --- (O)
# output
sink('../results/summary_{{_n}}.txt')
summary(model)
sink()
write_csv(result, '../results/table_{{_n}}.csv')
