""" Test constraints """

# --- (BOBA_CONFIG)
{
  "decisions": [
    {"var": "a", "options": [2, 2.5, 3], "desc": "outlier" },
    {"var": "b", "options": [0, 1] },
    {"var": "c", "options": [[1, 2], [3, 4]]}
  ],
  "constraints": [
    {"block": "B", "option": "b1", "condition": "A == a1"},
    {"block": "B", "option": "b2", "condition": "A == a2"}
  ]
}
# --- (END)

if __name__ == '__main__':
    # --- (A) a1
    a = {{b}}

    # --- (A) a2
    a = 1

    # --- (B) b1
    b = 1

    # --- (B) b2
    b = 2

    # --- (B) b3
    b = 3

    # --- (C)
    print(a * {{b}})
