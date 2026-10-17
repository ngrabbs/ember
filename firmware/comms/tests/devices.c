#include <assert.h>
#include "device_registry.h"
int main(void) {
    cf_frame query,response,bad;
    assert(!dr_request(0,1,1,&query));assert(!dr_request(5,1,1,&query));
    assert(!dr_request(2,0,1,&query));assert(!dr_request(2,1,0,&query));
    assert(dr_request(2,17,123,&query));
    assert(!dr_respond(&query,1,456,&response));
    assert(dr_respond(&query,2,456,&response));
    assert(dr_matches(&response,2,17));assert(ul_u32(response.data+4)==456);
    assert(!dr_matches(&response,2,18));assert(!dr_matches(&response,3,17));
    bad=response;bad.id++;assert(!dr_matches(&bad,2,17));
    bad=response;bad.size--;assert(!dr_matches(&bad,2,17));
    bad=response;bad.data[0]++;assert(!dr_matches(&bad,2,17));
    bad=response;ul_p32(bad.data+4,0);assert(!dr_matches(&bad,2,17));
    bad=query;bad.id=CF_IHU_ID;assert(!dr_respond(&bad,2,456,&response));
    dr_status s={0};dr_age(&s,50000);assert(s.state==DR_NOT_SEEN);
    dr_seen(&s,UINT32_MAX-999,456);dr_age(&s,1000);assert(s.state==DR_ONLINE);
    dr_age(&s,29000);assert(s.state==DR_STALE);
    dr_seen(&s,30000,789);assert(s.state==DR_ONLINE && s.boot==789);
    s.state=DR_FAULT;dr_age(&s,90000);assert(s.state==DR_FAULT);
    assert(dr_devices[DR_COMMS_INDEX].node==DR_COMMS_NODE);
    assert(dr_devices[DR_EPS_I2C_INDEX].interface==DR_I2C);
    return 0;
}
