/*
 *  utils.h
 *  chtml5lib
 *
 *  Created by James Graham on 02/01/2008.
 *  Copyright 2008 __MyCompanyName__. All rights reserved.
 *
 */

#include <stdlib.h>
#include <stdio.h>
#include <errno.h>
#include <string.h>
#include <ctype.h>

#include "var_string.h"
#include "consts.h"

int vstr_in_char_array(struct vstr *search_item, char **array, int array_length);