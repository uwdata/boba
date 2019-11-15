# Getting started

In this tutorial, we will walk you through a simple analysis scenario to
demonstrate how you might write and execute multiverse using our tool.

### A simple analysis script

Let's say we have the following analysis script that reads a data file, removes
 outliers, and fits a linear model.

```python
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
```

### Placeholder variable

Suppose the threshold for removing outliers is pretty subjective; you can
justify removing data points outside 2, 2.5 or 3 standard deviations of the
mean. Would the linear model change if you adopt a different threshold? To test
this, you might insert a decision point and ask the tool to output a
separate script for each possible threshold configuration. To insert a decision,
first insert a placeholder variable `{{var_name}}` in the above code:

```python
df = df[np.abs(df.y - df.y.mean()) <= ({{cutoff}} * df.y.std())]
```

Then, in a separate JSON file, you could list the possible options this
placeholder variable can take up:

```json
{
  "decisions": [
    {"var": "cutoff", "options": [2, 2.5, 3] }
  ]
}
```

Now, calling the tool with the file path to your script and JSON will output 3
python scripts. Each script is a universe where you choose a different cutoff
value for removing outliers; for example, one of the universes is exactly the
same as the analysis script we started with. The tool also outputs a summary
table to let you know what parameter value is taken up by which file:

|Filename     |Code Path|cutoff|
|-------------|---------|------|
|universe_1.py|_start   |2     |
|universe_2.py|_start   |2.5   |
|universe_3.py|_start   |3     |

(The table contains an unfamiliar column "Code Path", which we will explain in
a minute!)

If you specify multiple decisions, we will output **all combinations** of
possible alternatives. Namely, the number of output scripts will be the
cross-product of the number of options for each decision.

### Code blocks

Your decision point can be more complex than replacing values of a variable.
For example, instead of removing data points outside some standard deviations
of the mean, it is also reasonable to remove data points outside some IQRs of
the median. 

```python
iqr = np.subtract(*np.percentile(df.y, [75, 25]))
median = np.median(df.y)
df = df[abs(df.y - median) <= 3 * iqr]
```
As you can see, this alternative requires a few lines to implement; it is no
longer a straightforward value substitution. You can of course write the entire
block of code as a string into the decision array, but it will be really
cumbersome.

You might instead consider using code blocks. Instead of a
linear flow from start to end, your code can consist of blocks, similar to
cells in Jupyter notebook or R markdown. To specify a code block, simply insert
a comment line that looks like `# --- (ID) option` immediately
before the starting line of the block. The lines of code between this
declaration and the next (or the end of file) is a block
named `ID`. We will go ahead and insert three such comments into
our script:

```python
import pandas as pd
import numpy as np
import statsmodels.api as sm

if __name__ == '__main__':
    # read data file
    df = pd.read_csv('../data.csv')

    # --- (A) std
    # remove outliers based on std
    df = df[np.abs(df.y - df.y.mean()) <= ({{cutoff}} * df.y.std())]

    # --- (A) iqr
    # remove outliers based on iqr
    iqr = np.subtract(*np.percentile(df.y, [75, 25]))
    median = np.median(df.y)
    df = df[abs(df.y - median) <= 3 * iqr]

    # --- (B)
    # fit a simple ordinary least squares model
    x = sm.add_constant(df.x)
    lm = sm.OLS(df.y, x).fit()

    # display results
    print('y = {:.2f} + {:.2f} * x'.format(lm.params.const, lm.params.x))
    print('AIC: {:.2f}'.format(lm.aic))
    print('Coehn\'s F2: {:.3f}'.format(lm.rsquared_adj))
```

These three comments break the code into **four** blocks. All lines before
`# --- (A) std` belong to the first, unnamed block. All lines between `# --- (A) std`
and `# --- (A) iqr` belong to block "A" with option "std". All lines between
`# --- (B)` and the end of the file belong to block "B".

Note that we have two types of blocks: some blocks, such as `(A) std` and
`(A) iqr`, specify an *option* after the parenthesis.
Such blocks are called *decision blocks*; the same ID can take up different
options, not unlike a placeholder variable. Other blocks, such as `(B)`, are
normal blocks that do not act like a decision point.

We now need to tell boba the relationship between the blocks. 
We want to remove outliers before fitting the model, so the order of the blocks
should be A followed by B. Note that while A has two options `std` and `iqr`,
we only use `A` in the graph and boba will choose different options in
different universes. Let's specify the relationship of the blocks as a directed
graph in the JSON file:

```json
{
  "graph": ["A->B"],
  "decisions": [
    {"var": "cutoff", "options": [2, 2.5, 3] }
  ]
}
```
Now, calling the program with our updated script and JSON will generate 4
universes where the following value and code path is chosen:

|Filename     |Code Path   |cutoff|(A)|
|-------------|------------|------|---|
|universe_1.py|_start->A->B|2     |std|
|universe_2.py|_start->A->B|2.5   |std|
|universe_3.py|_start->A->B|3     |std|
|universe_4.py|_start->A->B|      |iqr|

Note that the cell of row "universe_4.py" and column "cutoff" is empty, because
we did not use the parameter `cutoff` in our outlier removal code involving IQR.
If we change the line to:
```python
df = df[abs(df.y - median) <= {{cutoff}} * iqr]
```

We will get 6 universes:

|Filename     |Code Path   |cutoff|(A)|
|-------------|------------|------|---|
|universe_1.py|_start->A->B|2     |iqr|
|universe_2.py|_start->A->B|2.5   |iqr|
|universe_3.py|_start->A->B|3     |iqr|
|universe_4.py|_start->A->B|2     |std|
|universe_5.py|_start->A->B|2.5   |std|
|universe_6.py|_start->A->B|3     |std|

Take a look at the generated python scripts
[here](https://github.com/uwdata/multiverse-spec/tree/master/example/simple/output/code).

(You may notice that all code paths in the above table are the same. In a more
complex analysis, we might produce differing code paths, by creating
branches in the directed graph. We will cover
advanced usage of the graph in a later tutorial.)

### Executing the multiverse
After you are happy with the generated scripts, you might want to execute them
all to compute the results. We generate a helper script `execute.sh` for you.
To invoke the script, simply run the following commands in a terminal:

```bash
cd your_output_dir/multiverse
sh execute.sh
```
It will run **all** the scripts for you! Before you do this, you might want
to run one script manually (or simply look at a few scripts) to ensure that
the generated code does not have syntax errors, etc.

### Try it yourself!

The code and data of this example is available [here](https://github.com/uwdata/multiverse-spec/tree/master/example/simple).
To run the example, clone this repository and run the following commands:

```bash
pip install -e .
pip install -r requirements.txt
cd example/simple
boba
```
