#include "utils.h"

int vstr_in_char_array(struct vstr *search_item, char *array[], int array_length) {
/*Is an vstr a member of a character array. The array must be sorted

 Returns 1 if the vstr is in the array, 0 otherwise*/
    char *match = NULL;

    //I think the following should work but it doesn't seem to...
    /*qsort(array, array_length, sizeof(char *), (int(*)(const void*,const void*))strcmp);
    match = (char *)bsearch(search_item->str, *array, array_length, sizeof(char *), (int(*)(const void*,const void*))strcmp);*/
    
    int i;
    for (i = 0; i < array_length; i++) {
        if (*array[i] == *(search_item->str)) {
            match = array[i];
            break;
        }
    }
    
    if (match == NULL) {
        return 0;
    } else {
        return 1;
    };
}