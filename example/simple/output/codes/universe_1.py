#!/usr/bin/env python3

import pandas as pd
import numpy as np
import statsmodels.api as sm
from sklearn import linear_model

if __name__ == '__main__':
    # read data file
    df = pd.read_csv('data.csv')

    # discard rows outside multiples of std
    df = df[np.abs(df.y - df.y.mean()) <= (2 * df.y.std())]

    X = np.asarray(df.x).reshape((-1, 1))
    lm = linear_model.LinearRegression().fit(X, df.y)
    print('Fitted using sklearn')
    print('y = {:.2f} + {:.2f} * x'.format(lm.intercept_, lm.coef_[0]))
    print('R squared: {:.2f}'.format(lm.score(X, df.y)))
