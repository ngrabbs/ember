#include <assert.h>
#include <deque>
#include <vector>
#include <string>
#include <algorithm>
#include "../src/engine.h"
struct Fake:bench::IO{
 std::deque<unsigned char> rx;std::vector<unsigned char> tx;std::vector<std::string> events;size_t capacity=4096;bool held=true;
 int read()override{if(rx.empty())return -1;int c=rx.front();rx.pop_front();return c;}
 size_t space()override{return capacity;}
 void write(const uint8_t *p,size_t n)override{assert(n<=capacity);tx.insert(tx.end(),p,p+n);}
 void reset(bool h)override{held=h;}
 void event(const char *s)override{events.emplace_back(s);}
 void feed(const char *s){while(*s)rx.push_back(*s++);}
 bool saw(const char *s){return std::any_of(events.begin(),events.end(),[&](const std::string &e){return e.find(s)!=std::string::npos;});}
};
static void ready(Fake &f,bench::Engine &e,uint32_t base=0){
 e.begin();assert(f.held);assert(e.on(base,120));e.tick(base+12000);
 for(unsigned i=0;i<10;++i){f.feed("\r\nOK\r\n");e.tick(base+12001+i);}
 assert(e.state==bench::Engine::REGISTER);f.feed("\r\n+CEREG: 2,1\r\nOK\r\n");e.tick(base+12020);
 for(unsigned i=0;i<6;++i){f.feed("\r\nOK\r\n");e.tick(base+12021+i);}
 assert(e.state==bench::Engine::READY&&e.registered);
}
int main(){
 assert(bench::crc32((const uint8_t *)"123456789",9)==0xcbf43926u);
 {Fake f;bench::Engine e(f,7);ready(f,e);assert(!e.on(13000,120));assert(!e.run(13000,0,128,1,1));
  assert(e.run(13000,123,128,10,1));e.tick(13000);size_t command_end=f.tx.size();assert(f.tx.back()=='\r');
  assert(command_end<2||f.tx[command_end-2]!='\n');
  f.feed("> ");e.tick(13001);assert(f.tx.size()==command_end+128);assert(!memcmp(f.tx.data()+command_end,"ELTB",4));
  f.feed("\r\nOK\r\n");e.tick(13002);assert(e.accepted==1&&e.offered==1);
  // Long transactions cause skipped slots; they are not packet losses or resubmissions.
  e.tick(13500);assert(e.offered==2&&e.skipped==4);f.feed("> ");e.tick(13501);f.feed("\r\nOK\r\n");e.tick(13502);
  e.tick(14000);assert(!e.running&&e.skipped==8&&e.offered==2&&e.accepted==2);
  assert(f.saw("\"unreached\":0"));e.off("test");assert(f.held);
 }
 {Fake f;bench::Engine e(f,7);ready(f,e);assert(e.run(13000,1,128,1,1));e.tick(13000);f.capacity=0;f.feed(">");e.tick(13001);
  size_t n=f.tx.size();e.tick(28000);assert(e.state==bench::Engine::OFF&&f.held&&e.unknown==1&&e.offered==1&&f.tx.size()==n);
  e.tick(29000);assert(e.offered==1); // An unknown transaction is never retried.
 }
 {Fake f;bench::Engine e(f,7);ready(f,e);assert(e.run(13000,2,128,1,1));e.tick(13000);f.feed("\r\nERROR\r\n");e.tick(13001);
  assert(e.rejected==1&&e.unknown==0&&e.state==bench::Engine::OFF);
 }
 {Fake f;bench::Engine e(f,7);ready(f,e);assert(e.run(13000,3,1024,1,1));e.tick(13000);f.capacity=7;f.feed(">");e.tick(13001);
  f.feed("\r\nOK\r\n");e.tick(13002);assert(e.unknown==1&&e.accepted==0&&f.held);
 }
 {Fake f;bench::Engine e(f,7);ready(f,e);assert(e.run(13000,4,128,1,1));e.tick(13000);f.feed("\r\n+CEREG: 0\r\n");e.tick(13001);
  assert(e.state==bench::Engine::OFF&&e.unknown==1&&f.held);
 }
 {Fake f;bench::Engine e(f,7);uint32_t base=0xffffe000u;ready(f,e,base);e.tick(base+120000);assert(e.state==bench::Engine::OFF&&f.held);
  f.feed("\r\n+CEREG: 1\r\n");e.tick(base+120001);assert(!e.registered);
 }
 {Fake f;bench::Engine e(f,7);e.begin();f.capacity=0;assert(e.on(0,1));e.tick(1000);assert(e.state==bench::Engine::OFF&&f.held);}
 {Fake f;bench::Engine e(f,7);ready(f,e);assert(e.query(13000,"operator"));e.tick(13000);f.feed("\r\n+COPS: 0,2,\"00101\",7\r\nOK\r\n");e.tick(13001);
  assert(e.state==bench::Engine::READY&&f.saw("00101"));assert(!e.query(13002,"arbitrary"));}
 {uint8_t packet[1024];assert(bench::make_packet(packet,128,0x12345678,5,99,7));
  FILE *out=fopen("/tmp/ember-bench-golden.bin","wb");assert(out);assert(fwrite(packet,1,128,out)==128);fclose(out);}
 puts("engine deadline, pacing, prompt/payload, no-retry, registration and query checks passed");
}
