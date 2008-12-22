#include "var_string.h"

struct vstr *vstr_new(size_t size) {
    struct vstr *rv; 
    
    rv = (struct vstr *)malloc(sizeof(struct vstr));
    if (rv == NULL) {
        abort();
    }
    
    rv->str = (char *)malloc(size * sizeof(char));
    if (rv->str == NULL) {
        abort();
    }
    
    rv->size = size-1;
    rv->pos = 0;
    vstr_clear(rv);
    return rv;
};

struct vstr *vstr_from_char(char *str) {
    /*Create a new vstr that contains the same characters as an existing char 
     buffer. This copies the characters rather than creating a reference*/
    
    struct vstr *rv;
    int size;
    size = strlen(str) + 1;
    rv = vstr_new(size);
    strcpy(rv->str, str);
    return rv;
}

void vstr_free(struct vstr *str) {
    free(str->str);
    free(str);
};


void vstr_append(struct vstr *str, char *append_str) {
    vstr_append_n(str, append_str, strlen(append_str));
}

void vstr_append_n(struct vstr *str, char *append_str, size_t n) {
    int new_size;
    //Check if we have enough space to allocate the string
    new_size = n + strlen(str->str) + 1;
    if (new_size >= str->size) {
        vstr_setsize(str, 2*str->size);
    }
    strncat(str->str, append_str, n);
}

void vstr_setsize(struct vstr *str, int size) {
    str->str = realloc(str->str, size);
    if (str->str == NULL) {
        abort();
    }
    str->size = size;
};

int vstr_cmp(struct vstr *str, char *cmp_str) {
    return strcmp(str->str, cmp_str);
};

size_t vstr_strlen(struct vstr *str) {
    return strlen(str->str);
}

struct vstr *vstr_duplicate(struct vstr *str) {
    //Duplicate an existing vstr
    struct vstr *new_str;
    new_str = vstr_new(str->size);
    strcpy(new_str->str, str->str);
    return new_str;
};

void vstr_clear(struct vstr *vstr) {
    *(vstr->str) = '\0';
}