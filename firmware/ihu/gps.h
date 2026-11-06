#pragma once
#include <stdbool.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

enum gps_status {GPS_NO_DATA, GPS_BUS_ERROR, GPS_NO_FIX, GPS_FIX};
typedef struct {
    enum gps_status status;
    unsigned satellites;
    double latitude, longitude, altitude;
    bool altitude_valid;
} gps_result;

typedef struct {
    char line[83];
    unsigned used;
} gps_reader;

static inline int gps_hex(char c){
    if(c>='0' && c<='9')return c-'0';
    if(c>='A' && c<='F')return c-'A'+10;
    return -1;
}

static inline bool gps_coordinate(const char *s,const char *hemi,bool latitude,double *out){
    unsigned digits=latitude?4:5;
    if(strspn(s,"0123456789")!=digits || s[digits]!='.' ||
       !s[digits+1] || s[digits+1+strspn(s+digits+1,"0123456789")])return false;
    char positive=latitude?'N':'E',negative=latitude?'S':'W';
    if((hemi[0]!=positive && hemi[0]!=negative) || hemi[1])return false;
    unsigned degrees=0;
    for(unsigned i=0;i<digits-2;++i)degrees=degrees*10+(unsigned)(s[i]-'0');
    double minutes=strtod(s+digits-2,NULL);
    unsigned limit=latitude?90:180;
    if(minutes>=60 || degrees>limit || (degrees==limit && minutes>0))return false;
    *out=(degrees+minutes/60)*(hemi[0]==negative?-1:1);
    return true;
}

static inline bool gps_gga(char *line,gps_result *result){
    char *checksum=strchr(line,'*');
    if(!checksum || strlen(checksum)!=3)return false;
    int high=gps_hex(checksum[1]),low=gps_hex(checksum[2]);
    if(high<0 || low<0)return false;
    unsigned actual=0;
    for(const char *p=line+1;p<checksum;++p)actual^=(unsigned char)*p;
    if(actual!=(unsigned)(high*16+low) || checksum-line<7 || strncmp(line+3,"GGA,",4))return false;
    *checksum=0;
    char *fields[10];
    char *field=line+7;
    for(unsigned i=0;i<10;++i){
        fields[i]=field;
        char *comma=strchr(field,',');
        if(!comma)return false;
        *comma=0;
        field=comma+1;
    }
    /* UTC, latitude, N/S, longitude, E/W, quality, satellites. */
    if(strlen(fields[5])!=1 || fields[5][0]<'0' || fields[5][0]>'8')return false;
    size_t digits=strspn(fields[6],"0123456789");
    if(digits<1 || digits>2 || fields[6][digits])return false;
    gps_result next={.status=GPS_NO_FIX,.satellites=(unsigned)atoi(fields[6])};
    char quality=fields[5][0];
    if(quality=='1' || quality=='2' || quality=='3' || quality=='4' || quality=='5'){
        if(!gps_coordinate(fields[1],fields[2],true,&next.latitude) ||
           !gps_coordinate(fields[3],fields[4],false,&next.longitude))return false;
        next.status=GPS_FIX;
        char *end;
        double altitude=strtod(fields[8],&end);
        if(end!=fields[8] && !*end && !strcmp(fields[9],"M") &&
           altitude>-2147483.0 && altitude<2147483.0){
            next.altitude=altitude;
            next.altitude_valid=true;
        }
    }
    *result=next;
    return true;
}

static inline bool gps_feed(gps_reader *reader,uint8_t byte,gps_result *result){
    if(byte=='$')reader->used=0;
    else if(!reader->used || byte=='\n')return false; /* I2C idle filler is LF. */
    else if(byte=='\r'){
        reader->line[reader->used]=0;
        reader->used=0;
        return gps_gga(reader->line,result);
    }
    if(byte<' ' || byte>'~' || reader->used>=sizeof(reader->line)-1){
        reader->used=0;
        return false;
    }
    reader->line[reader->used++]=(char)byte;
    return false;
}
