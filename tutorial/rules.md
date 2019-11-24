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
    {"var":  "decision_1", "options": [1, 2, 3]},
    {"var":  "decision_2", "options": ["1", "2", "3"]}
  ]
}
```
`decisions` is an array of individual decision. Each decision is a dictionary
that contains a `var` and a `options` array. `var` must match the
corresponding placeholder variable name in the script template.
`options` is an array of all possible values the placeholder
variable can take. An item in the `options` array can be any valid JSON type, as
long as the entire `options` array can be successfully cast into a python list.

Note that if the item is a string, for example "1", the quotes will not appear
in the generated script. For example, if the script template is 
`a={{decision_2}}` and the JSON spec is as above, one generated universe will
be `a=1` instead of `a="1"`.

### Constraints

The third type of top-level array, `constraints`, indicates procedural
dependencies (when a later decision only happens if a subset of options in an
earlier decision is chosen). It is optional. The array contains individual
constraint as objects, with the following fields:
```json
{"block": "block_ID", "variable": "placeholder_var", "option": "option", "skip": false, "condition": "A == a1"}
```

`block`, `variable` and/or `option` specify the dependent decision. `condition`
indicates the condition when the dependent decision should happen. `skip` is a
flag, only applicable to blocks, to indicate whether boba should skip the block
when the condition is not met (rather than removing the entire path).

There are three forms to identify a dependent decision. It can be a `block`
(either a normal block or a decision block). It can be a `block` with a
specific `option`. It can be a placeholder `variable` with a specific
`option`. Both `block` and `variable` refers to the identifier, whereas
`option` refers to the name of the block option or the actual value of the
placeholder option.

`skip` is optional, with the default value `false`. In other words, if the
condition evaluates to false, all universes containing the block
will not be created by default.

`condition` must be valid python syntax that can evaluate to a boolean. Only
a subset of python operators are allowed: `and`, `or`, `not`, and these
symbols `( ) < > ! =`. To say that a block/variable decision `A` takes up
the option `a1`, use the syntax `A == a1`. Alternatively for placeholder
variable `A`, you might refer to its options by the index of the option in
 the array, using
this syntax `A.index == 0`. The index starts from 0. 

More caveats:
1. For placeholder variables, the decision is NOT made at the beginning, but
until the placeholder variable first appears in the code. Any unmade decision
will have option `None` and index `-1`.

2. For security reasons, an option in a `condition` can only be a single word
or a single number. Use the index for anything more complex.

### Other Top-Level Fields

1. `before_execute`: is a string of a single-line bash script, which will be
executed every time prior to executing any universe, if you invoke `execute.sh`.
This field is optional.

2. `after_execute`: is a string of a single-line bash script, which will be 
executed every time after executing all universes, if you invoke `execute.sh`.
This field is optional.
