/*
 *  auto_string.c
 *  chtml5lib
 *
 *  Created by James Graham on 28/12/2007.
 *  Copyright 2007 __MyCompanyName__. All rights reserved.
 *
 */

#include "var_string.h"

struct vstr *vstr_new() {
    struct vstr *rv; 
    
    rv = (struct vstr *)malloc(sizeof(struct vstr));
    if (rv == NULL) {
        abort();
    }
    rv->str = (char *)malloc(DEFAULT_LENGTH * sizeof(char));
    if (rv->str == NULL) {
        abort();
    }
    rv->memsize = DEFAULT_LENGTH-1;
    vstr_clear(rv);
    return rv;
};

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
    new_size = pow(2, log(n + strlen(str->str)+1)/log(2));
    if (new_size >= str->memsize) {
        vstr_setsize(str, 2*str->memsize);
    }
    strncat(str->str, append_str, n);
}

void vstr_setsize(struct vstr *str, int size) {
    str->str = realloc(str->str, size);
    if (str->str == NULL) {
        abort();
    }
    str->memsize = size;
};

int vstr_cmp(struct vstr *str, char *cmp_str) {
    return strcmp(str->str, cmp_str);
};

struct vstr *vstr_duplicate(struct vstr *str) {
    //Duplicate an existing vstr
    struct vstr *new_str;
    new_str = vstr_new();
    vstr_setsize(new_str, str->memsize);
    strcpy(new_str->str, str->str);
    return new_str;
};

void vstr_clear(struct vstr *vstr) {
    *(vstr->str) = '\0';
}