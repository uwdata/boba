""" This script should fail to parse due to duplicated block id """

if __name__ == '__main__':
    a = 1
    b = 2

    # --- (a)
    b = b + 2 * a

    if b > 1:
        # --- (a)
        b = -b
    # --- (c)
    else:
        b = 2 * b
