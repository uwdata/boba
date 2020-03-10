# --- (BOBA_CONFIG)
{
  "graph": ["A->B->C"],
  "decisions": [
    {"var": "a", "options": [2, 2.5, 3], "desc": "outlier" },
    {"var": "b", "options": [0, 1] }
  ]
}

# --- (A)
if __name__ == '__main__':
    a = 1
    b = 2

    # --- (B)
    b = b + 2 * a

    if b > 1:
        # --- (C)
        b = -b
    else:
        b = 2 * b
