#include "headroom_core.hpp"
#include <cassert>
#include <iostream>
#include <limits>
int main() {
    ember_uhf::measurements m;
    using c=std::complex<float>;
    c weak(.01f,.02f),packet(.12f,0);
    assert(ember_uhf::mix(weak,packet,.25f,.15f,m)==weak+packet);
    c strong(3,4);auto out=ember_uhf::mix(strong,packet,.25f,.15f,m);
    assert(std::abs(out-c(.27f,.2f))<1e-6f);
    assert(m.forwarded_clipped==1 && m.telemetry_clipped==0);
    for(int i=0;i<8192;++i) {
        float angle=i*.017f;
        auto r=ember_uhf::mix(std::polar(5.f,angle),std::polar(2.f,angle),.25f,.15f,m);
        assert(std::abs(r)<=.400001f);
        assert(std::abs(std::arg(r)-std::arg(std::polar(1.f,angle)))<1e-5f);
    }
    auto huge=ember_uhf::mix(c(1e30f,1e30f),{},.25f,.15f,m);
    assert(std::abs(huge)<=.250001f && std::abs(huge)>.249f);
    auto bad=ember_uhf::mix(c(std::numeric_limits<float>::infinity(),0),packet,.25f,.15f,m);
    assert(bad==packet && m.invalid==1);
    assert(m.samples==8196);
    std::cout<<"PASS_CORE_TRANSPARENCY_PHASE_BOUND_EXTREME_AND_NONFINITE\n";
}
