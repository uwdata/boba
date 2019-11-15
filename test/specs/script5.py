""" Test the block-level parameter syntax """

if __name__ == '__main__':
    # --- (a:1)
    a = {{b}}

    # --- (a:2)
    a = 2

    # --- (b:1)
    b = 1

    # --- (b:2)
    b = 2

    # --- (b:3)
    b = 3

    # --- (c)
    print(a * b)
