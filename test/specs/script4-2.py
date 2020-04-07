""" Test ADG and code graph """

# --- (BOBA_CONFIG)
{
  "graph": ["A->B->C", "B->D"],
  "decisions": [
    {"var": "a", "options": [2, 2.5, 3], "desc": "outlier" },
    {"var": "b", "options": [0, 1] },
    {"var": "c", "options": [[1, 2], [3, 4]]}
  ]
}
# --- (END)

if __name__ == '__main__':
    # --- (A) a1
    a = {{a}}

    # --- (A) a2
    a = {{a}}

    # --- (B) b1
    b = {{b}}

    # --- (B) b2
    b = 2

    # --- (B) b3
    b = 3

    # --- (C)
    print(a * b)

    # --- (D)
