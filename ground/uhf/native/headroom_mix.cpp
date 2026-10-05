// Optional application block: one native worker replaces Add; no UHD dependency.
#include "headroom_core.hpp"
#include <gnuradio/io_signature.h>
#include <gnuradio/sync_block.h>
#include <gnuradio/sptr_magic.h>
#include <pybind11/pybind11.h>
#include <mutex>
#include <stdexcept>
namespace py=pybind11;

class headroom_mix : public gr::sync_block {
    float forward_limit_,telemetry_limit_;
    std::mutex mutex_;
    ember_uhf::measurements totals_;
public:
    headroom_mix(float forward_limit,float telemetry_limit)
        :gr::sync_block("Opaque IQ headroom mix",gr::io_signature::make(2,2,sizeof(gr_complex)),
                         gr::io_signature::make(1,1,sizeof(gr_complex))),
         forward_limit_(forward_limit),telemetry_limit_(telemetry_limit) {
        if(!std::isfinite(forward_limit) || !std::isfinite(telemetry_limit) ||
           forward_limit<.01f || forward_limit>.25f ||
           telemetry_limit<.01f || telemetry_limit>.15f)
            throw std::invalid_argument("Forward limit must be .01..25%, telemetry .01..15%");
    }
    static std::shared_ptr<headroom_mix> make(float f,float t) {
        return gnuradio::make_block_sptr<headroom_mix>(f,t);
    }
    int work(int count,gr_vector_const_void_star& inputs,gr_vector_void_star& outputs) override {
        const auto* forwarded=static_cast<const gr_complex*>(inputs[0]);
        const auto* telemetry=static_cast<const gr_complex*>(inputs[1]);
        auto* output=static_cast<gr_complex*>(outputs[0]);
        ember_uhf::measurements m;
        for(int i=0;i<count;++i)
            output[i]=ember_uhf::mix(forwarded[i],telemetry[i],forward_limit_,telemetry_limit_,m);
        std::lock_guard<std::mutex> lock(mutex_);
        totals_.samples+=m.samples;totals_.forwarded_clipped+=m.forwarded_clipped;
        totals_.telemetry_clipped+=m.telemetry_clipped;totals_.invalid+=m.invalid;
        totals_.forwarded_before2=std::max(totals_.forwarded_before2,m.forwarded_before2);
        totals_.forwarded_after2=std::max(totals_.forwarded_after2,m.forwarded_after2);
        totals_.telemetry_before2=std::max(totals_.telemetry_before2,m.telemetry_before2);
        totals_.output2=std::max(totals_.output2,m.output2);
        return count;
    }
    py::dict snapshot() {
        std::lock_guard<std::mutex> lock(mutex_);
        py::dict d;d["samples"]=totals_.samples;
        d["forwarded_clipped"]=totals_.forwarded_clipped;d["telemetry_clipped"]=totals_.telemetry_clipped;
        d["invalid"]=totals_.invalid;d["forward_peak_before"]=std::sqrt(totals_.forwarded_before2);
        d["forward_peak_after"]=std::sqrt(totals_.forwarded_after2);
        d["telemetry_peak_before"]=std::sqrt(totals_.telemetry_before2);
        d["output_peak"]=std::sqrt(totals_.output2);
        d["forward_limit"]=forward_limit_;d["telemetry_limit"]=telemetry_limit_;return d;
    }
};
PYBIND11_MODULE(headroom_mix,m) {
    py::module_::import("gnuradio.gr");
    py::class_<headroom_mix,gr::sync_block,gr::block,gr::basic_block,std::shared_ptr<headroom_mix>>(m,"headroom_mix")
        .def(py::init(&headroom_mix::make),py::arg("forward_limit")=.25f,py::arg("telemetry_limit")=.15f)
        .def("snapshot",&headroom_mix::snapshot);
}
