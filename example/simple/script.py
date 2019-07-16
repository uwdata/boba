#!/usr/bin/env python3

import pandas as pd
import numpy as np
import statsmodels.api as sm
from sklearn import linear_model

if __name__ == '__main__':
    # (A) read data file
    df = pd.read_csv('data.csv')

    # (B) remove outliers
    # discard rows outside 2 x std
    df = df[np.abs(df.y - df.y.mean()) <= (2 * df.y.std())]

    # (C1) fit a simple ordinary least squares model
    x = sm.add_constant(df.x)
    lm = sm.OLS(df.y, x).fit()

    # display results
    print('Fitted using statsmodels')
    print('y = {:.2f} + {:.2f} * x'.format(lm.params.const, lm.params.x))
    print('R squared: {:.2f}'.format(lm.rsquared))

    # (C2) fit a linear regression model using sklearn
    X = np.asarray(df.x).reshape((-1, 1))
    lm = linear_model.LinearRegression().fit(X, df.y)
    print('Fitted using sklearn')
    print('y = {:.2f} + {:.2f} * x'.format(lm.intercept_, lm.coef_[0]))
    print('R squared: {:.2f}'.format(lm.score(X, df.y)))
