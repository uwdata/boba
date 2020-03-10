# --- (BOBA_CONFIG)
{
  "graph": ["A->B->C", "A->"],
  "decisions": {}
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
