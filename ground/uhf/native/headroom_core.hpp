// Optional opaque-IQ mix/headroom arithmetic; no radio or EMBER protocol API.
#pragma once
#include <algorithm>
#include <cmath>
#include <complex>
#include <cstdint>

namespace ember_uhf {
struct measurements {
    uint64_t samples=0, forwarded_clipped=0, telemetry_clipped=0, invalid=0;
    double forwarded_before2=0, forwarded_after2=0, telemetry_before2=0, output2=0;
};
inline double magnitude2(std::complex<float> x) {
    float n=x.real()*x.real()+x.imag()*x.imag();
    if(std::isfinite(n)) return n;
    return double(x.real())*x.real()+double(x.imag())*x.imag();
}
inline std::complex<float> bound(std::complex<float> x,float limit,
        uint64_t& clipped,uint64_t& invalid,double& before2,double& after2) {
    if(!std::isfinite(x.real()) || !std::isfinite(x.imag())) {
        ++invalid; return {};
    }
    const double power=magnitude2(x);before2=std::max(before2,power);
    if(power>double(limit)*limit) {
        ++clipped;x*=float(double(limit)/std::sqrt(power));
    }
    after2=std::max(after2,magnitude2(x));return x;
}
inline std::complex<float> mix(std::complex<float> forwarded,std::complex<float> telemetry,
        float forward_limit,float telemetry_limit,measurements& m) {
    forwarded=bound(forwarded,forward_limit,m.forwarded_clipped,m.invalid,
                    m.forwarded_before2,m.forwarded_after2);
    double telemetry_after2=0;
    telemetry=bound(telemetry,telemetry_limit,m.telemetry_clipped,m.invalid,
                    m.telemetry_before2,telemetry_after2);
    auto output=forwarded+telemetry;m.output2=std::max(m.output2,magnitude2(output));
    ++m.samples;return output;
}
}
