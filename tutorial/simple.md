In this tutorial, we will walk you through how to generate multiverse for a
simple analysis scenario.

### A simple analysis script

Let's say we have the following analysis script that reads a data file, removes
some outliers, and fits a linear model.

```python
import pandas as pd
import numpy as np
import statsmodels.api as sm

if __name__ == '__main__':
    # (A) read data file
    df = pd.read_csv('data.csv')
    
    # (B) remove outliers
    # discard rows outside 2 x std
    df = df[np.abs(df.y - df.y.mean()) <= (2 * df.y.std())]
    
    # (C) fit a simple ordinary least squares model
    x = sm.add_constant(df.x)
    lm = sm.OLS(df.y, x).fit()
```

### Decision points

Suppose the threshold for removing outliers is pretty subjective; you can
justify removing data points outside 2, 2.5 or 3 standard deviations of the
mean. Would the linear model change if you adopt a different threshold? To test
this, you might insert a decision point and ask the tool to output a
separate script for each possible threshold configuration. To insert a decision,
first insert a placeholder variable `{{var_name}}` in the above code:

```python
df = df[np.abs(df.y - df.y.mean()) <= ('{{a}}' * df.y.std())]
```

Then, in a separate JSON file, you could list the possible values this decision
variable can take up:

```json
{
  "decisions": [
    {"var": "a", "type": "discrete", "value": [2, 2.5, 3] }
  ]
}
```

Now, calling the tool with the file path to your script and JSON will output 3
python scripts. Each script is a universe where you choose a different cutoff
value for removing outliers; for example, one of the universes is exactly the
same as the simple analysis script we started with. 

If you specify multiple decisions, we will output **all combinations** of
possible alternatives (i.e. the number of output scripts will be the
cross-product of the number of options for each decision!).

### Code branches

Your decision point can be more complex than replacing values of a variable.
For example, you might want to fit a different model which requires a few more
lines of code:

```python
from sklearn import linear_model

# (C2) fit a linear regression model using sklearn
X = np.asarray(df.x).reshape((-1, 1))
lm = linear_model.LinearRegression().fit(X, df.y)
```
(This is not a good example because you can put both models in the same file ...
but let's say you want the output file to contain either one of the two models.)
You can do it by specifying code branches. Instead of a linear flow from start
to end, your code can be consisting of blocks that have non-linear relationship
between blocks. To indicate blocks, simply insert a comment line that looks like
`# --- (block_name) description`:

```python
# --- (A)
import pandas as pd
import numpy as np
import statsmodels.api as sm
from sklearn import linear_model

if __name__ == '__main__':
    # read data file
    df = pd.read_csv('data.csv')

    # --- (B) remove outliers
    # discard rows outside multiples of std
    df = df[np.abs(df.y - df.y.mean()) <= ('{{a}}' * df.y.std())]

    # --- (C1) fit a simple ordinary least squares model
    x = sm.add_constant(df.x)
    lm = sm.OLS(df.y, x).fit()

    # display results
    print('Fitted using statsmodels')
    print('y = {:.2f} + {:.2f} * x'.format(lm.params.const, lm.params.x))
    print('R squared: {:.2f}'.format(lm.rsquared))

    # --- (C2) fit a linear regression model using sklearn
    X = np.asarray(df.x).reshape((-1, 1))
    lm = linear_model.LinearRegression().fit(X, df.y)
    print('Fitted using sklearn')
    print('y = {:.2f} + {:.2f} * x'.format(lm.intercept_, lm.coef_[0]))
    print('R squared: {:.2f}'.format(lm.score(X, df.y)))
```

We want the final output to be either `A->B->C1` or `A->B->C2`.
Let's specify the relationship of the blocks as a directed graph in the
JSON file:

```json
{
  "graph": [
    "A->B->C1",
    "B->C2"
  ],
  "decisions": [
    {"var": "a", "type": "discrete", "value": [2, 2.5, 3] }
  ]
}
```
Now, calling the program with our updated script and JSON will generate 6
universes where the following value and code path is chosen:
 - a = 2, A->B->C1
 - a = 2.5, A->B->C1
 - a = 3, A->B->C1
 - a = 2, A->B->C2
 - a = 2.5, A->B->C2
 - a = 3, A->B->C2

For example, `universe_1.py` will look like:
```python
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

    x = sm.add_constant(df.x)
    lm = sm.OLS(df.y, x).fit()

    # display results
    print('Fitted using statsmodels')
    print('y = {:.2f} + {:.2f} * x'.format(lm.params.const, lm.params.x))
    print('R squared: {:.2f}'.format(lm.rsquared))
```

### Try it yourself!

The code and data of this example is available [here](https://github.com/uwdata/multiverse-spec/tree/master/example/simple).
I haven't written installation / execution script yet, but if you really
want to run the parser, you'll have to write something like:

```python
# python version 3.7.4
from src.parser import Parser
base = '../example/simple/'
Parser(base+'script_annotated.py', base+'spec.json', base).main()
```
(This snippet is taken from `test_parser.py` which is how I currently run
the parser.)
