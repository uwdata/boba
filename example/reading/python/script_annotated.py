#!/usr/bin/env python3

import pandas as pd
import numpy as np
import statsmodels.formula.api as smf

if __name__ == '__main__':
    # read data
    df = pd.read_csv('./data.csv')

    # take the first N participants to simulate stopping condition
    df = df[:{{sample_size}}]

    # calculate reading speed in WPM
    df['speed'] = df.apply(lambda row: row.num_words / row['{{rt}}'] * 60000,
                           axis=1)

    # convert education level into an ordinal variable
    edu_order = ['pre-high school', 'high school', 'professional school',
                 'college', 'graduate school', 'PhD', 'postdoctoral']
    tp = pd.CategoricalDtype(categories=edu_order, ordered=True)
    df['edu_level'] = df.education.astype(tp).cat.codes

    # remove retake participants
    df = df[df.retake != 1]

    # remove smart phone users
    df = df[~df.device.isin({{bad_device}})]

    # remove outliers based on reading speed
    # --- (B1)
    # remove reading speed outside median + 3 x iqr
    iqr = np.subtract(*np.percentile(df.speed, [75, 25]))
    cutoff_high = np.median(df.speed) + 3 * iqr

    # --- (B2)
    # remove reading speed outside mean + 2 x std
    cutoff_high = np.mean(df.speed) + 2 * np.std(df.speed)

    # --- (C)
    cutoff_low = {{min_wpm}}
    df = df[df.speed <= cutoff_high]
    df = df[df.speed >= cutoff_low]

    # drop NA rows
    df = df.dropna()

    # log-normalize speed
    df['log_speed'] = np.log(df.speed)

    # decision: whether to bin dyslexia or not
    df.dyslexia = df['{{dyslexia}}']

    # make dyslexia a categorical variable
    df.dyslexia = df.dyslexia.astype('category')

    # remove trials based on comprehension < 2/3
    # --- (D1)
    # just remove trials
    df = df[df.correct_rate > 0.6]

    # --- (D2)
    # drop entire participants
    bad_uuid = set()
    for i, row in df.iterrows():
        if row.correct_rate < 0.6:
            bad_uuid.add(str(row.uuid))
    df = df[~df.uuid.isin(bad_uuid)]

    # --- (F1)
    # fit a linear mixed effects model
    fml = '{{formula}}'
    model = smf.mixedlm(fml, df, groups=df.uuid).fit()
    print(model.summary())

    # --- (F2)
    # fit a multinomial logit model to accuracy
    df['acc'] = 3 - pd.Categorical(df.correct_rate).codes
    fml = 'acc ~ page_condition*dyslexia_bin'
    model = smf.mnlogit(fml, df).fit()
    print(model.summary())
