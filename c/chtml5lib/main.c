#include "charset.h"

int main(int argc, char* argv[]) {
    FILE *fp;
    struct vstr *encoding;
    
    //Take the filename to read from argv[0] for now
    
    if (argc > 1) {
        char* fn = argv[1];
        fp = fopen(fn, "r");
    } else {
        printf("No file specfied\n");
        return 1;
    }
    
    encoding = get_encoding(fp);
    printf("%s\n", encoding->str);
    vstr_free(encoding);    
    
    return 0;
};