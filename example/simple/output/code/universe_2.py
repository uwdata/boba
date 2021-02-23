#!/usr/bin/env python3
import pandas as pd
import numpy as np
import statsmodels.api as sm

if __name__ == '__main__':
    # read data file
    df = pd.read_csv('data.csv')

    # remove outliers based on iqr
    iqr = np.subtract(*np.percentile(df.y, [75, 25]))
    median = np.median(df.y)
    df = df[abs(df.y - median) <= 2.5 * iqr]

    # fit a simple ordinary least squares model
    x = sm.add_constant(df.x)
    lm = sm.OLS(df.y, x).fit()

    # display results
    print('y = {:.2f} + {:.2f} * x'.format(lm.params.const, lm.params.x))
    print('AIC: {:.2f}'.format(lm.aic))
    print('Coehn\'s F2: {:.3f}'.format(lm.rsquared_adj))
