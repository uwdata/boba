""" Test the block-level parameter syntax """

if __name__ == '__main__':
    # --- (a) a1
    a = {{b}}

    # --- (a) a2
    a = 2

    # --- (b) b1
    b = 1

    # --- (b) b2
    b = 2

    # --- (b) b3
    b = 3

    # --- (c)
    print(a * b)
