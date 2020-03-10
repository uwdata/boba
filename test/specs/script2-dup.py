""" This script should fail to parse due to duplicated block id """

if __name__ == '__main__':
    a = 1
    b = 2

    # --- (A)
    b = b + 2 * a

    if b > 1:
        # --- (A)
        b = -b
    # --- (C)
    else:
        b = 2 * b
