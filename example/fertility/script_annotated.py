#!/usr/bin/env python3

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf

if __name__ == '__main__':
    # read data file
    df = pd.read_csv('durante_etal_2013_study1.txt', delimiter='\t')

    # remove NA
    df = df.dropna(subset=['rel1', 'rel2', 'rel3'])

    # create religiosity score
    df['rel_comp'] = np.around((df.rel1 + df.rel2 + df.rel3) / 3, decimals=2)

    # next menstrual onset (nmo) assessment
    df.last_period_start = pd.to_datetime(df.last_period_start)
    df.period_before_last_start = pd.to_datetime(df.period_before_last_start)
    df.date_testing = pd.to_datetime(df.date_testing)

    # --- (NMO1)
    # first nmo option: based on computed cycle length
    cl = df.last_period_start - df.period_before_last_start
    next_onset = df.last_period_start + cl
    df['computed_cycle_length'] = (cl / np.timedelta64(1, 'D')).astype(int)

    # --- (NMO2)
    # second nmo option: based on reported cycle length
    df = df.dropna(subset=['reported_cycle_length'])
    next_onset = df.last_period_start + df.reported_cycle_length.apply(
        lambda a: pd.Timedelta(days=a))

    # --- (ECL1)
    # exclusion based on computed cycle length
    df = df[(df.computed_cycle_length >= 25) & (df.computed_cycle_length <= 35)]

    # --- (ECL2)
    # exclusion based on reported cycle length
    df = df[(df.reported_cycle_length >= 25) & (df.reported_cycle_length <= 35)]

    # --- (A)
    # compute cycle day
    df['cycle_day'] = pd.Timedelta('28 days') - (next_onset - df.date_testing)
    df.cycle_day = (df.cycle_day / np.timedelta64(1, 'D')).astype(int)
    df.cycle_day = np.clip(df.cycle_day, 1, 28)

    # fertility assessment
    high_bounds = {{fertility_bounds}}[0]
    low_bounds1 = {{fertility_bounds}}[1]
    low_bounds2 = {{fertility_bounds}}[2]
    df.loc[(high_bounds[0] <= df.cycle_day) & (df.cycle_day <= high_bounds[1]),
           'fertility'] = 'High'
    df.loc[(low_bounds1[0] <= df.cycle_day) & (df.cycle_day <= low_bounds1[1]),
           'fertility'] = 'Low'
    df.loc[(low_bounds2[0] <= df.cycle_day) & (df.cycle_day <= low_bounds2[1]),
           'fertility'] = 'Low'

    # relationship status assessment
    # single = response options 1 and 2; relationship = response options 3 and 4
    df.loc[df.relationship <= {{relationship_bounds}}[0],
           'relationship_status'] = 'Single'
    df.loc[df.relationship >= {{relationship_bounds}}[1],
           'relationship_status'] = 'Relationship'

    # --- (EC)
    # exclusion based on certainty ratings
    df = df[(df.sure1 >= 6) & (df.sure2 >= 6)]

    # --- (B)
    # perform an ANOVA on the processed data set
    lm = smf.ols('rel_comp ~ relationship_status * fertility', data=df).fit()
    table = sm.stats.anova_lm(lm, typ=2)
    print(table)
