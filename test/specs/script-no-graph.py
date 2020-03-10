# --- (BOBA_CONFIG)
{
  "decisions": [
    {"var": "a", "options": [1]}
  ]
}
# --- (END)
if __name__ == '__main__':
    a = {{a}}
    b = a * 2
    print(b)
