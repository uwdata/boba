# Specification Rules

This document outlines the rules for the available syntax in boba.

## Script Template
Script template is an annotated script that will be used as the template to
derive executable universes. It can contain two types of annotations: placeholder
variables and code blocks.

### Placeholder Variable
A placeholder variable is a decision point, where the variable will be substituted
by one of the possible options. The placeholder variable declaration is
in the script template via the following syntax:

```
{{variable_name}}
```

It requires exactly two pairs of curly braces enclosing a `variable_name`.
A variable name must start with a letter and can contain an arbitrary number 
of letter, number and the special character `_` (we will reuse this rule
for all identifiers). Between the curly braces and
the variable name, no space is allowed.

The alternative values are defined in JSON spec. The variable name must match
one in the JSON, otherwise an error will be raised.

Any valid pattern will be recognized as a template variable, even if you do not
intend to. Any non-valid pattern will be dropped silently, even if you intend
it to be a template variable. All recognized variable will be in `summary.csv`.

Boba also has a few reserved variables, all starting with an underscore. These
variables represent predefined values and you do not need to supply options for
them in the JSON file:
1. `{{_n}}` represents the universe number, namely the number attached to the
generated universe file. It's useful for creating a separate filename for
outputting a separate file in each universe.

### Code Block
A code block declaration breaks the template script into blocks. All lines
following this declaration until the next code block declaration or the end of
file will be counted as inside this block. The syntax is:

```python
# --- (ID) option
```

It starts with `# ---` which is followed by a block identifier inside a pair of
`()`. A block identifier must satisfy the identifier naming rule. After the
block identifier, you might write an option, which also follows the
identifier naming rule. If you provide an option, the block will act like a
decision point, namely boba will substitute different options in different
universes and properly cross with other decisions.

The block identifier will be used to denote a node in the graph in JSON spec.
If the JSON spec cannot find a corresponding block in the script template, an
error will be raised. However, if the script template contains a block that
does not appear in the graph, only a warning will be raised and the block will
not appear in any generated universes.

You may also write a procedural dependency constraint when declaring a block,
using the following syntax:

```python
# --- (ID) option @if condition
```
It adds a constraint on this block and option (option is optional).
For more information on how procedural dependecy works, see 
[this section](#procedural-dependencies).

## JSON Spec
JSON spec is a JSON file containing a number of fields: a graph indicating the
relationship between code blocks, the options of all placeholder variables,
constraints for procedural dependencies, etc.

### Graph

Graph is a top-level array in the JSON. It is optional. The graph array
contains any amounts of string and each string contains nodes and edges in
the following format. An edge is represented by the syntax `->` and it is
directed, pointing from the left node to the right node. A node is a block
identifier and thus it follows the naming rule of block identifiers.

If graph is not present in the JSON and the template script contains code
blocks, boba will create a default graph, which is a linear path of all blocks.
The order of the nodes is the order that the blocks appear in the template
script.

Here is an example that denotes a circle consisting of node A, B and C:

```json
{
  "graph": ["A->B->C->A"]
}
```

The above example can also be written as:
```json
{
  "graph": ["A->B", "B->C", "C->A"]
}
```

As you can see, it does not matter how you chain up / break up the strings.
You are also free to repeat edges (i.e. specifies redundant edges):
```json
{
  "graph": ["A->B", "A->B->C", "C->A"]
}
```
and it still represents the same graph.

### Options for Placeholder Variables

Another top-level array, `decisions`, contains possible values of placeholder
variables. It is also optional, as long as you do not use any placeholder
variables in your script template. The syntax is:

```json
{
  "decisions": [
    {"var": "decision_1", "options": [1, 2, 3]},
    {"var": "decision_2", "options": ["1", "2", "3"]}
  ]
}
```
`decisions` is an array of individual decision. Each decision is a dictionary
that contains a `var` string and a `options` array. `var` must match the
corresponding placeholder variable name in the script template.
`options` is an array of all possible values the placeholder
variable can take. An item in the `options` array can be any valid JSON type, as
long as the entire `options` array can be successfully cast into a python list.

Note that if the item is a string, for example "1", the quotes will not appear
in the generated script. For example, if the script template is 
`a={{decision_2}}` and the JSON spec is as above, one generated universe will
be `a=1` instead of `a="1"`.

### Constraints

The third type of top-level array, `constraints`, indicates the relationship
between decisions, such that not all combinations of decisions are compatible.
It is optional. The array contains individual constraint as objects, and we
support two types of constraints: procedural dependencies and links.

#### Procedural dependencies
Procedural dependenciy arises when a later decision depends on the choice of
an earlier decision. The constraint object has the following fields:
```json
{
  "block": "block_ID",
  "variable": "placeholder_var",
  "option": "option",
  "skippable": false,
  "condition": "A == a1"
}
```

`block`, `variable` and/or `option` specify the dependent decision. `condition`
indicates the condition when the dependent decision should happen. `skippable`
is a flag, only applicable to blocks, to indicate whether boba should skip the
block when the condition is not met and continue with the next block (rather
than abandoning the entire universe). Next, we describe each field in detail.

There are three forms to identify a dependent decision. It can be a `block`
(either a normal block or a decision block). It can be a `block` with a
specific `option`. It can be a placeholder `variable` with a specific
`option`. Both `block` and `variable` refers to the identifier, whereas
`option` refers to the name of the block option or the actual value of the
placeholder option.

`skippable` is optional, with the default value `false`. If `skippable` is false, when
a universe does not satisfy the `condition`, the universe will be removed --
no script will be created for this universe. It is useful when some
combination of decisions are inherently not reasonable in your multiverse.
On the other hand, if `skippable` is true, boba will not
abandon the universe, but will instead skip the block with this flag and
continue from the next block in the graph. The universe still
exist, but the block will be removed from the script. This scenario is useful
when a helper block is only applicable to a certain subset of universes.

`condition` must be valid python syntax that can evaluate to a boolean. Only
a subset of python operators are allowed: `and`, `or`, and these
symbols `( ) < > ! =`. To say that a block/variable decision `A` takes up
the option `a1`, use the syntax `A == a1`. Alternatively for placeholder
variable `A`, you might refer to its option by the index of the option in
the array, using the syntax `A.index == 0`. The index starts from 0. 

Some caveats:
1. For placeholder variables, the decision is NOT made at the beginning, but
until the placeholder variable first appears in the code. Any unmade decision
will have option `None` and index `-1`.

2. For security reasons, when referring to an option by its value in the
`condition`, it only works if the option value is a single word (satisfying
the identifier naming rule) or a single number. Please use the index for
anything more complex.

#### Links
When two or more decisions are linked, they can be viewed as different 
manifestations of the same decision. The compiler will no longer take a cross
product, but assumes a one-to-one mapping between their options.
The constraint object has the following syntax:
```json
{"link": ["decision", "another_decision"]}
```
where the `link` field has a list of decision names (placeholder variable
identifiers and/or block identifiers). Linked decisions must have the same
number of options. The i-th option of all linked decisions will be chosen
at the same time.

### Other Top-Level Fields

1. `before_execute` is a string of a single-line bash script. It will be
executed every time prior to executing any universe, when `execute.sh` is
invoked. This field is optional.

2. `after_execute` is a string of a single-line bash script. it will be 
executed every time after executing all universes, when `execute.sh` is invoked.
This field is optional.
