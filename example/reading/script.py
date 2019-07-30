#!/usr/bin/env python3

import pandas as pd
import numpy as np
import statsmodels.formula.api as smf

if __name__ == '__main__':
    # read data
    df = pd.read_csv('data.csv')

    # calculate reading speed in WPM
    df['speed'] = df.apply(lambda row: row.num_words / row.adjust_rt * 60000,
                           axis=1)

    # remove retake participants
    df = df[df.retake != 1]

    # remove outliers based on reading speed
    iqr = np.subtract(*np.percentile(df.speed, [75, 25]))
    cutoff_high = np.median(df.speed) + 3 * iqr
    df = df[df.speed <= cutoff_high]
    df = df[df.speed >= 10]

    # remove smart phone users
    df = df[df.device != 'smartphone']

    # remove trials based on comprehension < 2/3
    df = df[df.correct_rate > 0.6]

    # drop NA rows
    df = df.dropna()

    # log-normalize speed
    df['log_speed'] = np.log(df.speed)

    # make dyslexia a categorical variable
    df.dyslexia = df.dyslexia.astype('category')

    # fit a linear mixed effects model
    fml = 'log_speed ~ img_width + num_words + page_condition*dyslexia' \
          '+ age + english_native'
    model = smf.mixedlm(fml, df, groups=df.uuid).fit()
    print(model.summary())
