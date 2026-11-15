#pragma once
#include <stdbool.h>
#define BOOT_CW_TEXT "KI5YNG - EMBER BOOT"
#define BOOT_CW_WPM 15u
#define BOOT_CW_UNIT_US (1200000u/BOOT_CW_WPM)
static inline const char *boot_morse_symbol(char ch) {
    switch(ch){
    case 'K':return "-.-"; case 'I':return ".."; case '5':return ".....";
    case 'Y':return "-.--"; case 'N':return "-."; case 'G':return "--.";
    case '-':return "-....-"; case 'E':return "."; case 'M':return "--";
    case 'B':return "-..."; case 'R':return ".-."; case 'O':return "---";
    case 'T':return "-"; default:return 0;
    }
}
static inline bool boot_morse(bool (*segment)(bool,unsigned)) {
    const char *p=BOOT_CW_TEXT;
    while(*p){
        const char *s=boot_morse_symbol(*p++);
        if(!s)return false;
        while(*s){
            if(!segment(true,*s++=='-'?3:1))return false;
            if(*s && !segment(false,1))return false;
        }
        if(*p){
            unsigned gap=3;
            if(*p==' '){gap=7;++p;}
            if(!segment(false,gap))return false;
        }
    }
    return true;
}
