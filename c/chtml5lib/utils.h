#include <stdlib.h>
#include <stdio.h>
#include <errno.h>
#include <string.h>
#include <ctype.h>

#include "var_string.h"
#include "consts.h"

int vstr_in_char_array(struct vstr *search_item, char **array, int array_length);