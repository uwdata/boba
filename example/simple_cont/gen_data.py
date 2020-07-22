#!/usr/bin/env python3

import numpy as np
import pandas as pd

# create a synthetic dataset and save to data.csv
if __name__ == '__main__':
    # create a linear series y= 10 + 0.5 * x plus random gaussian noise
    n = 100
    x = np.random.uniform(0, 5, n)
    y = 10 + 0.5 * x + np.random.normal(0, 0.2, n)

    # make outliers
    mean = np.mean(y)
    sd = np.std(y)
    cutoff = [2.4, 2.9, 3.4]
    for i in range(len(cutoff)):
        y[i * 2] = mean + cutoff[i] * sd
        y[i * 2 + 1] = mean - cutoff[i] * sd

    # save file
    df = pd.DataFrame(np.column_stack((x, y)), columns=['x', 'y'])
    df.to_csv('data.csv', index=False)
