#include "charset.h"

struct vstr *get_encoding(FILE *stream, num_bytes_meta) {
    
    //Read the first 512 bytes of the stream into an array
    char buf[num_bytes_meta+1];
    int n;
    struct vstr *encoding;
    
    encoding = vstr_new(8);
    
    n = fread(buf, 1, BUF_SIZE, stream);
    //Reset the buffer position
    fseek(stream, -n, SEEK_CUR);
    buf[n] = '\0';
    
    //Check for byte order marks
    if (strncmp(buf, "\xfe\xff", 2) == 0) {
        vstr_append(encoding, "UTF-16BE");
    } else if(strncmp(buf, "\xff\xfe", 2) == 0) {
        vstr_append(encoding, "UTF-16LE");
    } else if(strncmp(buf, "\xef\xbb\xbf", 3) == 0) {
        vstr_append(encoding, "UTF-8");
    } else {
        //Run autodetect algorithm
        detect_encoding(&buf[0], encoding);
    }
    
    return encoding;
};

void detect_encoding(char *buf, struct vstr *encoding) {
    while (*buf != '\0') {
        if (strncmp(buf, "<!--", 4) == 0) {
            buf = jump_to(buf, "-->");
        } else if(strncmp(buf, "<meta", 4) == 0) {
            buf = handle_meta(buf, encoding);
            if (*(encoding->str) != '\0') {
                break;
            }
        } else if (*buf == '<' && isalpha((int)*(buf+1))) {
            buf = handle_tag(buf);
        } else if (*buf == '<' && *(buf+1) == '/' && isalpha((int)*(buf+2))) {
            buf = handle_tag(buf);
        } else if (strncmp(buf, "<!", 2) == 0 || strncmp(buf, "</", 2) == 0 || strncmp(buf, "<?", 2) == 0) {
            buf = jump_to(buf, ">");
            if (buf == NULL) {
                break;
            }
        }
        buf++;
    }
};

struct attr *attr_new() {
    struct attr *new_attr;
    new_attr = (struct attr *)malloc(sizeof(struct attr));
    return new_attr;
};

char *handle_meta(char *buf, struct vstr *encoding) {
    struct attr *attr_value;
    buf += 5; //Point to the character after the a
    if (isspace((int)*buf) == 0) {
        //The next character is not a space so treat it as an ordinary tag
        buf -= 5;
        buf = handle_tag(buf);
    } else {
        attr_value = attr_new();
        buf = get_attr(buf, attr_value);
        while (*(attr_value->name->str) != '\0') {
            if (vstr_cmp(attr_value->name, "charset") == 0) {
                if (is_encoding(attr_value->value)) {
                    vstr_append(encoding, attr_value->value->str);
                    break;
                }
            } else if (vstr_cmp(attr_value->name, "content")) {
            //Parse the content value
                struct vstr *content_encoding = handle_content_type(attr_value->value);
                if (*(content_encoding->str) != '\0' && is_encoding(content_encoding)) {
                    vstr_append(encoding, content_encoding->str);
                    break;
                }
                vstr_free(content_encoding);
            }
            buf = get_attr(buf, attr_value);
        }
        free(attr_value);
    }
    return buf;
};

char *jump_to(char *str, char* target) {
    //Return  pointer to the last byte in the first match of target in str or null if is not present; 
    while (1) {
        //Find a matching first character
        while (*str != '\0' && *str != *target) {
             str++;
        }
        if (*str == '\0') {
            str = NULL;
            break;
        } else if(strncmp(str, target, strlen(target)) == 0) { 
            str += strlen(target)-1;
            break;
        }
    }
    return str;
};

char *handle_tag(char *buf) {
    int skip_chars;
    struct attr *attr_value;
    buf++;

    skip_chars = strcspn(buf, "\t\n\f\v\f\r /><");
    buf += skip_chars;
    
    if (*buf == '<') {
        buf -= 1; // This will be added back on in the caller
        return buf;
    };

    attr_value = attr_new();
    buf = get_attr(buf, attr_value);
    while (*(attr_value->name->str) != '\0' && buf != '\0') {
        buf = get_attr(buf, attr_value);
    };
    free(attr_value);
    
    return buf;
};

char *get_attr(char *buf, struct attr *attr_value) {
    int skip_chars;
    char quote[1];
    char lcase_letter[1];
    
    int spaces = 0; //Do the spaces step
    
    attr_value->name = vstr_new(8);
    attr_value->value = vstr_new(8);
    
    *(attr_value->name->str) = '\0';
    *(attr_value->value->str) = '\0';
    skip_chars = strspn(buf, "\t\n\f\v\f\r /");
    buf += skip_chars;
    if (*buf == '\0' || *buf == '<' || *buf == '>') {
        if (*buf == '<') {
            buf -=1;
        }
        return buf;
    }
    
    while (1) {
        if (*buf == '\0') {
            return buf;
        } else if (*buf == '=' && strlen(attr_value->name->str) != 0) {
            buf++;
            break;
        } else if (isspace((int)(*buf))){
            spaces = 1;
            break;
        } else if (*buf == '/' || *buf == '<' || *buf == '>') {
            return buf;
        } else if(isupper((int)(*buf))) {
            lcase_letter[0] = (char)tolower((int)(*buf));
            vstr_append_n(attr_value->name, lcase_letter, 1);
        } else {
            vstr_append_n(attr_value->name, buf, 1);
        }
        buf++;
    }
    
    if (spaces) {
        buf = skip_space(buf);
        if (*buf != '=') {
            buf -= 1;
            return buf;
        } else {
            buf++;
        }
    }
    
    buf = skip_space(buf);
    if (*buf == '\'' || *buf == '"') {
        quote[0] = *buf;
        buf++;
        while (*buf != quote[0] && *buf != '\0') {
            if (isupper((int)(*buf))) {
                vstr_append_n(attr_value->value, (char *)tolower((int)(*buf)), 1);
            } else {
                vstr_append_n(attr_value->value, buf, 1);
            }
            buf++;
        }
        //XXX need to advance position here
        if (*buf == quote[0]) {
            buf++;
        }
        return buf;
    } else if  (*buf == '<' || *buf == '>' || *buf == '\0'){
        return buf;
    } else if (isupper((int)(*buf))) {
        lcase_letter[0] = (char)tolower((int)(*buf));
        vstr_append_n(attr_value->value, lcase_letter, 1);
    } else {
        vstr_append_n(attr_value->value, buf, 1);
    };
    buf++;
    while (buf != '\0') {
        if (isspace((int)(*buf)) || *buf == '<' || *buf == '>') {
            return buf;
        } else if (isupper((int)(*buf))) {
            lcase_letter[0] = (char)tolower((int)(*buf));
            vstr_append_n(attr_value->value, lcase_letter, 1);
        } else {
            vstr_append_n(attr_value->value, buf, 1);
        };
        buf++;
    }
    return buf;
};

struct vstr *handle_content_type(struct vstr *attr_value) {
    struct vstr *encoding;
    char *value;
    char *quote;
    
    encoding = vstr_new(8);
    value = attr_value->str;
    //Skip characters up to and including the first ;
    value = jump_to(value, ";");
    value++;
    
    if (*value == '\0') {
        return encoding;
    }
    
    skip_space(value);
    
    if (strncmp(value, "charset", 7) != 0) {
        return encoding;
    }
    value += 7;
    
    skip_space(value);

    if (*value != '=') {
        return encoding;
    }
    
    value++;
    
    skip_space(value);
    
    if (*value == '\'' || *value == '"') {
        quote = value;
        value++;
        if (strstr(value, quote) != NULL) {
            while(value != quote) {
                vstr_append_n(encoding, value, 1);
                value++;
            }
            return encoding;
        } else {
            return encoding;
        }
    } else  {
        while(*value != '\0' && isspace((int)(*value)) == 0) {
            vstr_append_n(encoding, value, 1);
            value++;
        }
    return encoding;
    }
};

int is_encoding(struct vstr *encoding) {
    //Is the string a valid encoding?
    //return 1;
    return vstr_in_char_array(encoding, valid_encodings, sizeof(valid_encodings)/sizeof(char*));
};

char *skip_space(char *buf) {
    int skip_chars=0;
    skip_chars = strspn(buf, "\t\n\f\v\f\r ");
    buf += skip_chars;
    return buf;
};