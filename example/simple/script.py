#!/usr/bin/env python3

import pandas as pd
import numpy as np
import statsmodels.api as sm

if __name__ == '__main__':
    # read data file
    df = pd.read_csv('data.csv')

    # remove outliers
    # discard rows outside 2 x std
    df = df[np.abs(df.y - df.y.mean()) <= (2 * df.y.std())]

    # fit a simple ordinary least squares model
    x = sm.add_constant(df.x)
    lm = sm.OLS(df.y, x).fit()

    # display results
    print('y = {:.2f} + {:.2f} * x'.format(lm.params.const, lm.params.x))
    print('AIC: {:.2f}'.format(lm.aic))
    print('Coehn\'s F2: {:.3f}'.format(lm.rsquared_adj))
