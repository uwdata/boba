# --- (a)
if __name__ == '__main__':
    a = 1
    b = 2

    # --- (b)
    b = b + 2 * a

    if b > 1:
        # --- (c)
        b = -b
    else:
        b = 2 * b
