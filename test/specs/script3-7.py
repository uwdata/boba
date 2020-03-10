""" Test constraints """

# --- (BOBA_CONFIG)
{
  "decisions": [
    {"var": "a", "options": [0, 1, 2, 3, 4] },
    {"var": "b", "options": ["0", "1", "2", "3", "4"]}
  ],
  "constraints": [
    {"link": ["a", "b"]}
  ]
}
# --- (END)

if __name__ == '__main__':
    # --- (A)
    a = {{a}}

    # --- (B) b1
    b = 1 + {{b}}

    # --- (B) b2
    b = 2 + {{b}}

    # --- (C)
    print(a * b)

    # --- (D)
    print(a + b)
