""" Test inline constraints """

if __name__ == '__main__':
    # --- (A) a1
    a = 1

    # --- (A) a2
    a = 2

    # --- (B) b1 @if A == a1
    b = 1

    # --- (B) b2 @if A == a2
    b = 2

    # --- (C)
    print(a * b)
