""" Test the block-level parameter syntax """

# --- (BOBA_CONFIG)
{"decisions": [
    {"var": "b", "options": [1, 2]}
]}
# --- (END)

if __name__ == '__main__':
    # --- (A) a1
    a = {{b}}

    # --- (A) a2
    a = 2

    # --- (B) b1
    b = 1

    # --- (B) b2
    b = 2

    # --- (B) b3
    b = 3

    # --- (C)
    print(a * b)
