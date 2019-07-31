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
    df = df[~df.device.isin(['smartphone'])]

    # drop NA rows
    df = df.dropna()

    # log-normalize speed
    df['log_speed'] = np.log(df.speed)

    # make dyslexia a categorical variable
    df.dyslexia = df.dyslexia.astype('category')

    # wrangle education level
    edu_order = ['pre-high school', 'high school', 'professional school',
                 'college', 'graduate school', 'PhD', 'postdoctoral']
    tp = pd.CategoricalDtype(categories=edu_order, ordered=True)
    df['edu_level'] = df.education.astype(tp).cat.codes

    # check correlation between IVs
    ivs = df[['img_width', 'num_words', 'page_condition', 'age']]
    print(ivs.corr(), '\n')
    print(pd.crosstab(df.english_native, df.dyslexia, normalize='columns'), '\n')
    print(pd.crosstab(df.device, df.dyslexia, normalize='columns'), '\n')

    # fit a multinomial logit model to accuracy
    df['acc'] = 3 - pd.Categorical(df.correct_rate).codes
    print(df.groupby('acc').size(), '\n')
    fml = 'acc ~ page_condition*dyslexia_bin'
    model = smf.mnlogit(fml, df, groups=df.uuid).fit()
    print(model.summary(), '\n')

    # remove trials based on comprehension < 2/3
    df = df[df.correct_rate > 0.6]

    # fit a linear mixed effects model
    fml = 'log_speed ~ img_width + num_words + page_condition*dyslexia' \
          '+ age + english_native'
    model = smf.mixedlm(fml, df, groups=df.uuid).fit()
    print(model.summary())
