#include <assert.h>
#include <stdio.h>
#include "../auto_reply.h"
int main(void){
 ar_lease s={0};assert(!ar_take(&s,0,true,true,false));
 ar_start(&s,100);assert(ar_take(&s,10000000,true,true,false));assert(!ar_take(&s,10000001,true,true,false));
 /* A first post-reboot payload reply observed at 17.7s must retain TX margin. */
 ar_start(&s,100);assert(ar_take(&s,17700000,true,true,false));
 ar_start(&s,100);assert(!ar_take(&s,22000101,true,true,false));
 ar_start(&s,100);assert(!ar_take(&s,25000100,true,true,false));
 ar_start(&s,100);assert(!ar_take(&s,200,true,true,true));assert(!ar_take(&s,201,true,true,false));
 ar_start(&s,100);assert(!ar_take(&s,200,false,true,false));
 ar_start(&s,100);assert(!ar_take(&s,200,true,false,false));
 puts("PASS: one-shot reply, no boot authorization, cancellation, stale/missing response, deadline and failure");
}
