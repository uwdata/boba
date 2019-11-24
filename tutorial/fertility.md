# A Real-World Multiverse Example

In this tutorial, we will implement the multiverse analysis of Steegen et al.
using boba. In their pioneering [paper](
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

The nested structure looks quite clumsy -- what if we have 10 decision points
and thus 10 nested levels? With boba, we hope the users could focus on the
decisions and the options, and let boba handle the rest.

Another issue with these for-loops is the inability to express
conditional branches where a downstream decision depends on an upstream one.
Steegen et al. explained a conditional branch in the paper:

> Some of the choice combinations are inconsistent: When participants are
> excluded based on reported or computed cycle
> length, we do not consider next menstrual onset based on
> computed or reported cycle length, respectively. 

To implement this, they ran 180 analyses but excluded 60 of the inconsistent
ones. We will show how you could express such dependencies in boba.

### Our implementation

We expanded the analysis of study 1 in Steegen's R script into a multiverse
specification (
[template](https://github.com/uwdata/multiverse-spec/blob/master/example/fertility_r/template.R),
[JSON](https://github.com/uwdata/multiverse-spec/blob/master/example/fertility_r/spec.json)).

Recall that in boba, we have basically two ways to specify a decision: via a
template variable ``{{var_name}}``, or via a code block. In our multiverse, we
make use of both.

For example, a decision about next menstrual onset (`NMO`) is implemented
as a code block with two variants:

```r
# --- (NMO) computed
# first nmo option: based on computed cycle length
df$NextMenstrualOnset <- df$StartDateofLastPeriod + df$ComputedCycleLength

# --- (NMO) reported
# second nmo option: based on reported cycle length
df$NextMenstrualOnset <- df$StartDateofLastPeriod + df$ReportedCycleLength
```

Another decision, assessment of relationship status, is a placeholder variable:

```r
# relationship status assessment
rel.bounds = {{relationship_bounds}}
df$RelationshipStatus[df$Relationship <= rel.bounds[1]] <- "Single"
df$RelationshipStatus[df$Relationship >= rel.bounds[2]] <- "Relationship"
```
```json
{"var": "relationship_bounds", "options": [
  "c(2, 3)", "c(1, 2)", "c(1, 3)"
]}
```

Although `relationship_bounds` has a upper bound and a lower bound, we implement this decision as
one variable instead of two, because we do not want boba to take a cross
product of the two cutoffs. Here, the two cutoffs belong to a list in a single
placeholder variable, so they are paired.

After specifying two more decisions (`ECL` and `EC`) as code blocks, we now
tell boba the relationship between the blocks:
```json
{ "graph": ["NMO->ECL->A->EC->B"] }
```

If we stop here, boba will take a cross product of all five decisions and
produce 180 universes. But as we described earlier, some paths are not reasonable.
Specifically, when we compute NMO using *computed* cycle length, we do not want
to filter data based on *reported* cycle length, and vice versa. To tell
boba that a decision depends on the choices made in another decision, we could
use `constraints` in the JSON spec:

```json
{
  "constraints": [
    {"block": "ECL", "option": "computed", "condition": "NMO == computed"},
    {"block": "ECL", "option": "reported", "condition": "NMO == reported"}
  ]
}
```

In the field `block` and `option`, we specify the dependent decision, in this
case the two options of `ECL`. Then in
the field `condition`, we specify the condition when this dependent decision
should happen. With these constraints, boba will generate only 120 universes.

### Advanced usage of the graph

There is yet another, arguably simpler and more flexible way to specify
decisions and procedural dependencies, if you are comfortable with directed
acyclic graphs (DAGs). Recall that we wrote in the JSON spec a graph
indicating the relationship between blocks. The relationship needs not be
linear, but can be any valid DAGs.

To illustrate advanced usage of the graph, we built another multiverse, this
time using a python version of the analysis (
[template](https://github.com/uwdata/multiverse-spec/blob/master/example/fertility/script_annotated.py),
[JSON](https://github.com/uwdata/multiverse-spec/blob/master/example/fertility/spec.json)).

We now describe how you might specify a decision in different ways.
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
    {"var": "filter_condition", "options": [
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
    {"var": "cycle_length", "options": ["reported_cycle_length", "computed_cycle_length"]}
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

Of course, we could also use decision blocks as we did in the previous example:
```python
# --- (ECL) ecl1
# include all cycle lengths

# --- (ECL) ecl2
# exclusion based on computed cycle length
df = df[(df.computed_cycle_length >= 25) & (df.computed_cycle_length <= 35)]

# --- (ECL) ecl3
# exclusion based on reported cycle length
df = df[(df.reported_cycle_length >= 25) & (df.reported_cycle_length <= 35)]
```

(The first option does nothing basically, but it is necessary to explicitly
write an empty block, otherwise boba wouldn't know that we intend to have an
option that filters nothing.)

All four ways are (somewhat) equivalent. But how do we specify procedural
dependencies using DAG? Recall that
filtering on reported cycle length is only applicable if next menstrual onset
is calculated using reported cycle length, and vice versa. In other words, ECL2
is present only if NMO1 is present and ECL3 is present only if NMO2 is present.
Note that our third specification above naturally supports such branching
condition and we might extend it to include the NMO code blocks:

```json
{
  "graph": ["NMO1->ECL2->A", "NMO2->ECL3->A", "NMO1->A", "NMO2->A"]
}
```

With this graph, we will only generate 120 universes, which is 
the number after excluding inconsistent analyses.

# Try it yourself!

The complete code and data are here (
[R](https://github.com/uwdata/multiverse-spec/tree/master/example/fertility_r),
[python](https://github.com/uwdata/multiverse-spec/tree/master/example/fertility)).
We do not include the output scripts because there will be 120 of them. But
you are welcome to invoke the parser, take a look at the generated scripts, 
and execute the multiverse to inspect the results.

To run the example, clone this repository and run the following commands:

```bash
pip install -e .
pip install -r requirements.txt
cd example/fertility_r
boba -s template.R
```
