#pragma once
#include <stdbool.h>
#include <stdint.h>
#include <string.h>
/* Commands are numbered without wrap; overflow fails closed until reset. */
enum {IHU_COMMAND_SIZE=40,IHU_COMMAND_QUEUE=4,IHU_CAN_RX_QUEUE=64,
      IHU_RECORD_SIZE=1024,IHU_REPLY_QUEUE=8,IHU_LOG_QUEUE=16};
enum {IHU_SUPERVISOR,IHU_CAN,IHU_APP,IHU_SENSOR,IHU_SCHEDULE,IHU_USB,IHU_TASKS};
/* Task IDs are separate from queue constants. */
typedef struct {uint32_t sequence;char line[IHU_COMMAND_SIZE];} ihu_command;
typedef struct {uint32_t sequence[7],next;uint8_t pending;} ihu_controls;
static inline int ihu_urgent_index(const char *s){
    static const char *const names[]={"cli_debug","cli_telem","umb_debug","umb_telem","uhf_telem","lte_telem"};
    if(!strcmp(s,"uhf stop"))return 6;
    for(int i=0;i<6;i++){
        char line[IHU_COMMAND_SIZE];
        /* Avoid printf in this shared control contract. */
        strcpy(line,"output ");strcat(line,names[i]);strcat(line," off");
        if(!strcmp(s,line))return i;
    }
    return -1;
}
static inline bool ihu_number_command(ihu_controls *c,ihu_command *command){
    if(c->next==UINT32_MAX)return false;
    command->sequence=++c->next;
    int index=ihu_urgent_index(command->line);
    if(index>=0){c->sequence[index]=command->sequence;c->pending|=(uint8_t)(1u<<index);}
    return true;
}
static inline bool ihu_progress_ok(uint32_t now,const uint32_t *progress,unsigned count,uint32_t limit){
    for(unsigned i=0;i<count;i++)if((uint32_t)(now-progress[i])>limit)return false;
    return true;
}
