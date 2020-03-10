""" This script will fail to parse due to invalid block definition syntax """

if __name__ == '__main__':
    a = 1
    b = 2

    # --- A
    b = b + 2 * a

    if b > 1:
        # --- B
        b = -b
    # --- C
    else:
        b = 2 * b
