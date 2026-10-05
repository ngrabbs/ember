"""Native GNU Radio component clipping for the optional transponder branch."""
import math

FORWARD_PEAK = .25
COMPONENT_PEAK = FORWARD_PEAK / math.sqrt(2)


def make_limiter():
    from gnuradio import analog,blocks,gr

    class ForwardLimiter(gr.hier_block2):
        def __init__(self):
            gr.hier_block2.__init__(self, 'Forwarded IQ amplitude bound',
                gr.io_signature(1,1,gr.sizeof_gr_complex),
                gr.io_signature(1,1,gr.sizeof_gr_complex))
            split=blocks.complex_to_float(1)
            real=analog.rail_ff(-COMPONENT_PEAK,COMPONENT_PEAK)
            imag=analog.rail_ff(-COMPONENT_PEAK,COMPONENT_PEAK)
            self.combine=blocks.float_to_complex(1)
            self.connect(self,split)
            self.connect((split,0),real,(self.combine,0))
            self.connect((split,1),imag,(self.combine,1))
            self.connect(self.combine,self)

        def snapshot(self):
            return dict(samples=self.combine.nitems_written(0),limit=FORWARD_PEAK,
                component_limit=COMPONENT_PEAK,
                note='Native component clipping; strong input can distort phase',error=None)

    return ForwardLimiter()
