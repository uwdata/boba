""" Should fail to parse because of a block and a variable
 have the same name."""

if __name__ == '__main__':
    # --- (a)
    a = {{a}}

    # --- (b) b1
    b = 1

    # --- (b) b2
    b = 2

    # --- (c)
    print(a * b)
