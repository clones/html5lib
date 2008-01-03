#include <stdlib.h>
#include <string.h>
#include <math.h>

struct vstr {
    char *str;
    size_t memsize;
};

#define DEFAULT_LENGTH 16

struct vstr *vstr_new();
void vstr_setsize(struct vstr *str, int size);
void vstr_free(struct vstr *str);
void vstr_append(struct vstr *str, char *append_str);
void vstr_append_n(struct vstr *str, char *append_str, size_t n);
struct vstr *vstr_duplicate(struct vstr *str);
void vstr_clear(struct vstr *vstr);