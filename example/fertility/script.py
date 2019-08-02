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

    # first nmo option: based on computed cycle length
    computed = df.last_period_start - df.period_before_last_start
    next_onset = df.last_period_start + computed

    # second nmo option: based on reported cycle length
    df = df.dropna(subset=['reported_cycle_length'])
    next_onset2 = df.last_period_start + df.reported_cycle_length.apply(
        lambda a: pd.Timedelta(days=a))

    # compute cycle day
    df['cycle_day'] = pd.Timedelta('28 days') - (next_onset - df.date_testing)
    df.cycle_day = (df.cycle_day / np.timedelta64(1, 'D')).astype(int)
    df.cycle_day = np.clip(df.cycle_day, 1, 28)

    # fertility assessment
    high_bounds = [6, 14]
    low_bounds = [17, 27]
    df.loc[(high_bounds[0] <= df.cycle_day) & (df.cycle_day <= high_bounds[1]),
           'fertility'] = 'High'
    df.loc[(low_bounds[0] <= df.cycle_day) & (df.cycle_day <= low_bounds[1]),
           'fertility'] = 'Low'

    # relationship status assessment
    # single = response options 1 and 2; relationship = response options 3 and 4
    df.loc[df.relationship <= 2, 'relationship_status'] = 'Single'
    df.loc[df.relationship > 2, 'relationship_status'] = 'Relationship'

    # exclusion based on cycle length
    df = df[(df.reported_cycle_length >= 25) &
            (df.reported_cycle_length <= 35)]

    # exclusion based on certainty ratings
    df = df[(df.sure1 >= 6) & (df.sure2 >= 6)]

    # perform an ANOVA on the processed data set
    lm = smf.ols('rel_comp ~ relationship_status * fertility', data=df).fit()
    print(lm.summary(), '\n')
    table = sm.stats.anova_lm(lm, typ=2)
    print(table)
