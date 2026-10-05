#pragma once
#include <stdio.h>
#include <stdint.h>
/* Handle solicited <n>,<stat> and unsolicited <stat>[,"tac",...].
 * sscanf whitespace is optional; accept only a whole matching CEREG prefix. */
static inline bool parse_cereg(const char *line,uint8_t *status) {
    unsigned first,second;const char *p=line;
    while(*p==' ' || *p=='\r' || *p=='\n')++p;
    int fields=sscanf(p,"+CEREG: %u , %u",&first,&second);
    if(fields==2 && first<=5 && second<=10) {*status=(uint8_t)second;return true;}
    if(fields==1 && first<=10) {*status=(uint8_t)first;return true;}
    return false;
}
