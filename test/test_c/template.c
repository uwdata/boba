# --- (BOBA_CONFIG)
{
  "lang": "lang.json"
}
# --- (END)

#include <stdio.h>
int main() {
    printf("hello from universe ");
    printf("%d", {{id=1,2,3}});
    printf("\n");
    return 0;
}