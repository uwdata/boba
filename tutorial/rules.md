# Specification Rules

This document outlines the rules for available syntax in our multiverse
specification tool.

## Script Template
Script template is an annotated script that will be used as the template to
derive executable universes. It can contain two types of annotations: template
variables and code blocks.

### Template Variable
A template variable is a decision point, where the variable will be substituted
by one of the possible alternative values. The template variable declaration is
in a script template via the following syntax:

```
{{variable_name}}
```

It requires exactly two pairs of curly braces enclosing a `variable_name`.
A variable name must start with a letter and can contain an arbitrary number 
of letter, number and the special character `_`. Between the curly braces and
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
# --- (ID) optional description
```

It starts with `# ---` which is followed by a block identifier inside a pair of
`()`. A block identifier must start with a letter and can contain an arbitrary
number of letter, number and the special character `_`. After the identifier,
you might write an arbitrary description like a regular comment, but note that 
the comment will not appear in the generated universe code.

The block identifier will be used to denote a node in the graph in JSON spec.
If the JSON spec cannot find a corresponding block in the script template, an
error will be raised. However, if the script template contains a block that
does not appear in the graph, only a warning will be raised and the block will
not appear in any generated universes.

## JSON Spec
JSON spec is a JSON file containing a specification for the graph and the
values of decision points.

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

### Decision Point Values

Another top-level array, `decisions`, contains possible values of template
variables. It is also optional, as long as you do not use any template
variables in your script template. The syntax is:

```json
{
  "decisions": [
    {"var":  "decision_1", "type": "discrete", "values": [1, 2, 3]},
    {"var":  "decision_2", "type": "discrete", "values": ["1", "2", "3"]}
  ]
}
```
`decisions` is an array of individual decision. Each decision is a dictionary
that contains a `var`, a `type` and a `values` array. `var` must match the
corresponding template variable name in the script template. `type` indicates
the variable type, but currently we only support "discrete" type, which means
the values are categorical and each time one element will be used to replace
the template variable. `values` is an array of all possible values the template
variable can take. An item in the `values` array can be any valid JSON type, as
long as the entire `values` array can be successfully cast into a python list.

Note that if the item is a string, for example "1", the quotes will not appear
in the generated script. For example, if the script template is 
`a={{decision_2}}` and the JSON spec is as above, one generated universe will
be `a=1` instead of `a="1"`.
