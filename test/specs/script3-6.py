""" Test constraints """

# --- (BOBA_CONFIG)
{
  "graph": ["A->B->C->D"],
  "decisions": [
    {"var": "a", "options": ["if", "else"]},
    {"var": "b", "options": [0, 1.5] }
  ],
  "constraints": [
    {"block": "D", "condition": "a == if and B == b1"}
  ]
}
# --- (END)

if __name__ == '__main__':
    # --- (A)
    a = {{a}}

    # --- (B) b1
    b = 1 + {{b}}

    # --- (B) b2
    b = 2 + {{b}}

    # --- (C)
    print(a * b)

    # --- (D)
    print(a + b)
