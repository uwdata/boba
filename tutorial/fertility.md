# A Real-World Multiverse Example

In this tutorial, we will implement the multiverse analysis of Steegen et al.
using our tool. In their pioneering [paper](
https://journals.sagepub.com/doi/full/10.1177/1745691616658637
) , Steegen et al. reanalyzed the [datasets](https://osf.io/zj68b/)
collected by Durante et al. to study the effect of fertility on religiosity
and political attitudes. For data collection, Durante's original analysis
procedure and results, decision points, and multiverse analysis
results, please refer to Steegen's paper. Here, we will focus on the
implementation of multiverse analysis.

### Their implementation

In their R script implementing the multiverse analysis, Steegen et al. relied
on nested for-loops to enumerate all combinations of alternatives of decision
points:

```r
  for (i in 1:no.nmo){  # for each nmo option
    for (j in 1:no.f){  # for each f option
      for (k in 1:no.r){  # for each r option
        for (l in 1:no.ecl){  # for each ecl option
          for (m in 1:no.ec){  # for each ec option
            # process data and store results in an in-memory array
          }
        }
      }
    }
  }
```
Using for-loops have multiple issues, for instance the nested structure looks
bloated (what if we have 20 decision points and thus 20 nested levels?).
But a more important issue is the inability to express
conditional branches where a downstream decision depends on an upstream one.
Steegen et al. explained a conditional branch in the paper:

> Some of the choice combinations are inconsistent: When participants are
> excluded based on reported or computed cycle
> length, we do not consider next menstrual onset based on
> computed or reported cycle length, respectively. 

To implement this, they ran 180 analyses but excluded 60 of the inconsistent
ones. It will be much better if we do not run these 60 analyses in the first
place.

### Our implementation

We converted the analysis of study 1 in Steegen's R script into
[python](https://github.com/uwdata/multiverse-spec/blob/master/example/fertility/script.py)
and expanded it to a multiverse specification (
[template](https://github.com/uwdata/multiverse-spec/blob/master/example/fertility/script_annotated.py),
[JSON](https://github.com/uwdata/multiverse-spec/blob/master/example/fertility/spec.json)).

Recall that in our tool, we have basically 
two ways to specify a decision point: via a template variable `{{var_name}}`
which chooses from one of the available options, or via nodes in
a directed acyclic graph (DAG) which dictates non-linear flow of code blocks.
The first approach is simpler, but the second approach is far more flexible 
and powerful. Now, we will illustrate how we used DAG to meet our needs.

One of the decision point, ECL, has the following options:

> Exclusion of women based on cycle length (ECL)  
> (a) ECL1: no exclusion based on cycle length  
> (b) ECL2: exclusion of participants with computed cycle
length greater than 25 or less than 35 days  
> (c) ECL3: exclusion of participants with reported cycle
length greater than 25 or less than 35 days

The decision point is essentially a filtering operation that removes nothing
or removes rows outside certain range of either `reported_cycle_length` or
`computed_cycle_length` . We could specify all three options using a template
variable by placing filtering condition into variable value:

``` python
# template script
df = df[{{filter_condition}}]

# JSON
{
  "decisions": [
    {"var": "filter_condition", "value": [
      "[True]*df.shape[0]",
      "(df.computed_cycle_length >= 25) & (df.computed_cycle_length <= 35)",
      "(df.reported_cycle_length >= 25) & (df.reported_cycle_length <= 35)"
    ]}
  ]
}
```
Alternatively, we can create a code block for the filtering code and make it
an optional node in the graph. We still use a template variable to indicate
which column to filter, but the value will be much simpler:

```python
# template script
# --- (A)
# ... some stuff

# --- (ECL)
df = df[(df.{{cycle_length}} >= 25) & (df.{{cycle_length}} <= 35)]

# --- (B)
# ... some other stuff

# JSON
{
  "graph": ["A->B", "A->ECL->B"],
  "decisions": [
    {"var": "cycle_length", "value": ["reported_cycle_length", "computed_cycle_length"]}
  ]
}
```

Yet another way is to create two nodes, one for each filtering condition. It
will look like this:

```python
# template script
# --- (A)
# ... some stuff

# --- (ECL2)
# exclusion based on computed cycle length
df = df[(df.computed_cycle_length >= 25) & (df.computed_cycle_length <= 35)]

# --- (ECL3)
# exclusion based on reported cycle length
df = df[(df.reported_cycle_length >= 25) & (df.reported_cycle_length <= 35)]

# --- (B)
# ... some other stuff

# JSON
{
  "graph": ["A->B", "A->ECL2->B", "A->ELC3->B"]
}
```
All three ways are (somewhat) equivalent. But it turns out that the decision
point ECL is conditioned on a previous decision point NMO:

> Next menstrual onset (NMO)  
> (a) NMO1: reported start date previous menstrual onset +
computed cycle length  
> (b) NMO2: reported start date previous menstrual onset +
reported cycle length

Filtering on reported cycle length is only applicable if next menstrual onset
is calculated using reported cycle length, and vice versa. In other words, ECL2
is present only if NMO1 is present and ECL3 is present only if NMO2 is present.
Note that our third specification above naturally supports such branching
condition and we might extend it to include the NMO code blocks:

```python
# template
# --- (NMO1)
# first nmo option: based on computed cycle length
cl = df.last_period_start - df.period_before_last_start
next_onset = df.last_period_start + cl
df['computed_cycle_length'] = (cl / np.timedelta64(1, 'D')).astype(int)

# --- (NMO2)
# second nmo option: based on reported cycle length
df = df.dropna(subset=['reported_cycle_length'])
next_onset = df.last_period_start + df.reported_cycle_length.apply(
    lambda a: pd.Timedelta(days=a))

# --- (ECL2)
# exclusion based on computed cycle length
df = df[(df.computed_cycle_length >= 25) & (df.computed_cycle_length <= 35)]

# --- (ECL3)
# exclusion based on reported cycle length
df = df[(df.reported_cycle_length >= 25) & (df.reported_cycle_length <= 35)]

# --- (A)
# ... some other stuff

# JSON
{
  "graph": ["NMO1->ECL2->A", "NMO2->ECL3->A", "NMO1->A", "NMO2->A"]
}
```

With the complete specification, we will only generate 120 universes, which is 
the number after excluding inconsistent analyses.

# Try it yourself!

The complete code and data are [here](
https://github.com/uwdata/multiverse-spec/tree/master/example/fertility).
We do not include the output scripts because there will be 120 of them. But
you are welcome to invoke the parser, take a look at the generated scripts, 
and execute the multiverse to inspect the results.

To run the example, clone this repository and run the following commands:

```bash
pip install -e .
cd example/fertility
boba
```
