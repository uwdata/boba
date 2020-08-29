# We augmented the hurricane dataset by Jung et al. via the following steps:
# (1) Add entries for two hurricanes, Katrina and Audrey
# (2) Update normalized damage for all hurricanes, as adjusted to 2019 dollar values
# (3) Retrieve the highest wind speed for all hurricanes
# (4) Replace the femeninity ratings for all hurricanes
# Normalized damage was retrived at: http://www.icatdamageestimator.com/commonsearch
# The ratings for (4) is provided by Uri Simonson


import pandas as pd
import numpy as np
from scipy.stats.stats import pearsonr

# read csv
jung = pd.read_csv('data_jung.csv')
df = pd.read_csv('data_updated.csv')
ratings = pd.read_csv('MTurk_ratings_femeninity_of_hurricanes.csv')

# take the average of ratings and store in a dictionary keyed by name
rs = dict()
for c in ratings:
    if c.startswith('Q1'):
        # the first row is also a header, extract name from the question
        name = ratings[c][0].split('-')[-1]
        # take the average of ratings, excluding the first row
        rs[name] = np.mean(ratings[c][1:].astype('int32'))

# fill in the ratings to our updated dataset
for i in df.index:
    name = df.at[i, 'Name']
    df.at[i, 'MasFem'] = rs[name]
    df.at[i, 'Gender_MF'] = 1 if rs[name] > 6 else 0
df.Gender_MF = df.Gender_MF.astype('int32')

# check the correlation between original and updated damage
dff = df[(df.Name != 'Audrey') & (df.Name != 'Katrina')]
r = pearsonr(jung.NDAM, dff.NDAM)
print('Correlation of normalized damage: {}'.format(r[0]))

# check the correlation between original and updated gender ratings
r = pearsonr(jung.MasFem, dff.MasFem)
print('Correlation of gender ratings: {}'.format(r[0]))
r = pearsonr(jung.Gender_MF, dff.Gender_MF)
print('Correlation of binary gender flag: {}'.format(r[0]))

# results:
# Correlation of normalized damage: 0.942
# Correlation of gender ratings: 0.981
# Correlation of binary gender flag: 0.951

# save
df.to_csv('./data.csv', index=False)
