#pragma once
#include <stdbool.h>
#include <stdint.h>
/* One-shot authorization scoped to this console invocation; never boot-resumed. */
typedef struct {bool armed;uint64_t deadline;} ar_lease;
static inline void ar_start(ar_lease *s,uint64_t now){s->armed=true;s->deadline=now+20000000;}
static inline bool ar_take(ar_lease *s,uint64_t now,bool fresh,bool healthy,bool cancelled){
 bool allow=s->armed && fresh && healthy && !cancelled && now<s->deadline && s->deadline-now>=3000000;
 s->armed=false;return allow;
}
