#include "utils.h"

#define BUF_SIZE 512 //preparse buffer size

struct attr {
    struct vstr *name;
    struct vstr *value;
};

struct vstr *get_encoding(FILE *stream);
void detect_encoding(char* buf, struct vstr *encoding;);
char *jump_to(char *str, char* target);
char *get_attr(char *buf, struct attr *attr_value);
char *handle_tag(char *buf);
int is_encoding(struct vstr *encoding);
char *skip_space(char *buf);
char *handle_meta(char *buf, struct vstr *encoding);
struct vstr *handle_content_type(struct vstr *attr_value);
struct attr *attr_new();