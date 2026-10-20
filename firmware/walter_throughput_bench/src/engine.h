#pragma once
#include <stdint.h>
#include <stdio.h>
#include <stdarg.h>
#include <string.h>
#include "packet.h"
#include "../../walter/src/cereg.h"
namespace bench {
struct IO {
 virtual ~IO()=default;
 virtual int read()=0;
 virtual size_t space()=0;
 virtual void write(const uint8_t *,size_t)=0; // Must not block; caller bounds size by space().
 virtual void reset(bool held)=0;
 virtual void event(const char *)=0; // Nonblocking; adapter counts queue overflows.
};
inline bool due(uint32_t a,uint32_t b){return (int32_t)(a-b)>=0;}
class Engine {
public:
 enum State {OFF,BOOT_WAIT,CONFIGURE,REGISTER,SOCKET,READY,SEND,QUERY};
 State state=OFF;uint8_t cereg=255;bool registered=false,running=false,inflight=false;
 uint32_t offered=0,accepted=0,rejected=0,unknown=0,skipped=0,boot,window_end=0;
 explicit Engine(IO &port,uint32_t id):boot(id?id:1),io(port){}
 void begin(){io.reset(true);}
 void status(uint32_t now){
  emit("{\"event\":\"status\",\"state\":%u,\"cereg\":%u,\"registered\":%u,\"remaining_ms\":%lu,\"running\":%u,\"offered\":%lu,\"accepted\":%lu,\"rejected\":%lu,\"unknown\":%lu,\"skipped\":%lu}",
       state,cereg,registered,(unsigned long)(state==OFF||due(now,window_end)?0:window_end-now),running,
       (unsigned long)offered,(unsigned long)accepted,(unsigned long)rejected,(unsigned long)unknown,(unsigned long)skipped);
 }
 void off(const char *reason){
  if(inflight){++unknown;emit_attempt("unknown");inflight=false;}
  io.reset(true);state=OFF;busy=false;registered=false;cereg=255;tx_n=tx_pos=0;line_n=0;discard=false;
  if(running)finish(reason);
  emit("{\"event\":\"off\",\"reason\":\"%s\"}",reason);
 }
 bool on(uint32_t now,unsigned seconds){
  if(state!=OFF||seconds<1||seconds>120){error("on_rejected");return false;}
  window_end=now+seconds*1000;wake=now+12000;state=BOOT_WAIT;step=0;registered=false;cereg=255;
  line_n=0;discard=false;io.reset(false);emit("{\"event\":\"window\",\"seconds\":%u}",seconds);return true;
 }
 bool run(uint32_t now,uint32_t id,unsigned bytes,unsigned pps,unsigned seconds){
  if(state!=READY||busy||running||!registered||!id||(bytes!=128&&bytes!=512&&bytes!=1024)||
     pps<1||pps>100||seconds<1||seconds>30||(int32_t)(window_end-now)<(int32_t)(seconds*1000+16000)){
   error("run_rejected");return false;
  }
  run_id=id;size=bytes;rate=pps;start=now;end=now+seconds*1000;slots=pps*seconds;next=0;
  offered=accepted=rejected=unknown=skipped=0;running=true;
  emit("{\"event\":\"run_start\",\"run\":%lu,\"bytes\":%u,\"pps\":%u,\"seconds\":%u,\"slots\":%lu,\"boot\":%lu,\"sender_ms\":%lu}",
       (unsigned long)id,bytes,pps,seconds,(unsigned long)slots,(unsigned long)boot,(unsigned long)now);return true;
 }
 bool query(uint32_t now,const char *name){
  if(state!=READY||busy||running||window_end-now<7000){error("query_not_ready");return false;}
  const char *cmd=nullptr;
  if(!strcmp(name,"operator"))cmd="AT+COPS?";
  else if(!strcmp(name,"signal"))cmd="AT+CSQ";
  else if(!strcmp(name,"firmware"))cmd="AT+CGMR";
  else if(!strcmp(name,"registration"))cmd="AT+CEREG?";
  else if(!strcmp(name,"pdp"))cmd="AT+CGACT?";
  if(!cmd){error("unknown_query");return false;}
  state=QUERY;at(cmd,now);return true;
 }
 void tick(uint32_t now){
  if(state==OFF){for(unsigned i=0;i<512&&io.read()>=0;++i){}return;}
  if(due(now,window_end)){off("window_deadline");return;}
  if(state==BOOT_WAIT&&due(now,wake)){state=CONFIGURE;configure(now);}
  for(unsigned i=0;i<512;++i){int ch=io.read();if(ch<0)break;receive((char)ch,now);if(state==OFF)return;}
  if(busy&&due(now,at_end)){off("at_timeout");return;}
  if(state==REGISTER&&!busy){if(registered){state=SOCKET;step=0;socket(now);}else if(due(now,wake))at("AT+CEREG?",now);}
  if(state==READY&&!registered&&!busy&&due(now,wake)&&!running)at("AT+CEREG?",now);
  if(running){
   if(!registered){off("registration_lost");return;}
   if(due(now,end)){skipped+=slots-next;next=slots;if(!inflight)finish("duration");}
   else {
    uint32_t current=(uint32_t)((uint64_t)(now-start)*rate/1000);
    if(current>=next&&current<slots){
     skipped+=current-next;next=current+1;
     if(inflight||busy)++skipped;
     else {
      sequence=current;++offered;inflight=true;payload=false;state=SEND;
      make_packet(packet,size,run_id,sequence,now,boot);
      char cmd[48];snprintf(cmd,sizeof(cmd),"AT+SQNSSENDEXT=1,%u,0",size);at(cmd,now,15000);
      emit_attempt("attempt");
     }
    }
   }
  }
   if(tx_pos<tx_n){size_t n=io.space();if(n>tx_n-tx_pos)n=tx_n-tx_pos;if(n){io.write(tx+tx_pos,n);tx_pos+=n;}}
 }
 void error(const char *reason){emit("{\"event\":\"error\",\"reason\":\"%s\"}",reason);}
private:
 IO &io;bool busy=false,payload=false,discard=false;unsigned step=0,size=128,rate=1;
 uint32_t wake=0,at_end=0,run_id=0,sequence=0,start=0,end=0,slots=0,next=0;
 uint8_t packet[MAX_PACKET],tx[MAX_PACKET+64];size_t tx_n=0,tx_pos=0,line_n=0;char line[512];
 void emit(const char *format,...){char out[640];va_list args;va_start(args,format);int n=vsnprintf(out,sizeof(out),format,args);va_end(args);if(n>=0&&(size_t)n<sizeof(out))io.event(out);}
 void emit_attempt(const char *type){emit("{\"event\":\"%s\",\"run\":%lu,\"seq\":%lu,\"bytes\":%u}",type,(unsigned long)run_id,(unsigned long)sequence,size);}
 void finish(const char *reason){
  running=false;emit("{\"event\":\"run_done\",\"run\":%lu,\"reason\":\"%s\",\"slots\":%lu,\"offered\":%lu,\"accepted\":%lu,\"rejected\":%lu,\"unknown\":%lu,\"skipped\":%lu,\"unreached\":%lu}",
   (unsigned long)run_id,reason,(unsigned long)slots,(unsigned long)offered,(unsigned long)accepted,
   (unsigned long)rejected,(unsigned long)unknown,(unsigned long)skipped,(unsigned long)(slots-next));
 }
 void at(const char *cmd,uint32_t now,uint32_t timeout=6000){
  // Only one transaction at a time. Terminate commands with CR, never CRLF.
  tx_n=strlen(cmd);memcpy(tx,cmd,tx_n);tx[tx_n++]='\r';tx_pos=0;busy=true;at_end=now+timeout;line_n=0;discard=false;
  text_event("at",cmd);
 }
 void configure(uint32_t now){
  static const char *const cmds[]={"AT","ATE0","AT+CMEE=2","AT+CFUN=0","AT+SQNBANDSEL=0,\"standard\",\"13\"",
   "AT+CGDCONT=1,\"IP\",\"srsapn\"","AT+CEREG=2","AT+COPS?","AT+CGMR","AT+CFUN=1"};
  if(step<sizeof(cmds)/sizeof(cmds[0]))at(cmds[step++],now);else{state=REGISTER;wake=now;}
 }
 void socket(uint32_t now){
  static const char *const cmds[]={"AT+COPS?","AT+CSQ","AT+CGPADDR=1","AT+CGACT?","AT+SQNSCFG=1,1,300,90,100,1",
   "AT+SQNSD=1,1,51002,\"172.16.0.1\",0,51003,1,0,0"};
  if(step<sizeof(cmds)/sizeof(cmds[0])){unsigned i=step++;at(cmds[i],now,i==5?15000:6000);}
  else{state=READY;emit("{\"event\":\"ready\",\"sender_ms\":%lu}",(unsigned long)now);}
 }
 void text_event(const char *kind,const char *text){
  char escaped[512];size_t j=0,i=0;
  for(;text[i]&&i<80;++i){unsigned char ch=(unsigned char)text[i];
   if(ch=='"'||ch=='\\'){escaped[j++]='\\';escaped[j++]=(char)ch;}
   else if(ch>=32&&ch<127)escaped[j++]=(char)ch;
   else{int n=snprintf(escaped+j,sizeof(escaped)-j,"\\u%04x",ch);j+=(size_t)n;}
  }
  escaped[j]=0;
  emit("{\"event\":\"%s\",\"line\":\"%s\",\"truncated\":%u}",kind,escaped,text[i]!=0);
 }
 void complete(bool ok,uint32_t now){
  busy=false;tx_n=tx_pos=0;
  if(state==SEND){
   if(ok&&!payload){off("ok_before_prompt");return;}
   if(ok&&payload){++accepted;emit_attempt("accepted");inflight=false;state=READY;}
   else{++rejected;emit_attempt("rejected");inflight=false;off("modem_rejected");}
   return;
  }
  if(!ok){off("configuration_or_query_error");return;}
  if(state==CONFIGURE)configure(now);
  else if(state==SOCKET)socket(now);
  else if(state==REGISTER)wake=now+3000;
  else if(state==QUERY){state=READY;emit("{\"event\":\"query_done\"}");}
  else if(state==READY)wake=now+3000;
 }
 void receive(char ch,uint32_t now){
  if(state==SEND&&busy&&!payload&&ch=='>'){
   if(tx_pos!=tx_n){off("prompt_before_command_sent");return;}
   memcpy(tx,packet,size);tx_n=size;tx_pos=0;payload=true;line_n=0;discard=false;return;
  }
  if(ch=='\r'||ch=='\n'){
   if(!discard&&line_n){
    line[line_n]=0;uint8_t parsed;
    if(parse_cereg(line,&parsed)){cereg=parsed;registered=(parsed==1||parsed==5);}
    text_event("modem",line);
    if(busy&&!strcmp(line,"OK")){
     if(tx_pos<tx_n){off("terminal_before_tx_complete");return;}
     complete(true,now);
    }else if(busy&&(!strcmp(line,"ERROR")||!strncmp(line,"+CME ERROR:",11)))complete(false,now);
   }
   line_n=0;discard=false;
  }else if(!discard){if(ch&&line_n+1<sizeof(line))line[line_n++]=ch;else{discard=true;off("response_overflow");}}
 }
};
}
