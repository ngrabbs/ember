# ---------------------------------------------------------------------------
# EMBER experimental S-band payload - FPGA build and simulation
#
# Milestone M0: symbol timing, pattern selection, PRBS-7, registered output.
# Run every target from this directory.
#
#   make golden     PRBS-7 golden model self-test and checker model (Python only)
#   make sim        both testbenches
#   make sim-long   the M0 gate: 1,000,000 symbols with zero errors
#   make lint       Verilator lint pass
#   make synth      Yosys resource estimate for iCE40
#   make check      golden + sim + lint
#   make waves      simulate with VCD output for GTKWave
#   make tools      how to install what is missing
# ---------------------------------------------------------------------------

RTL     := rtl/prbs7_gen.sv rtl/prbs7_check.sv rtl/tx_pattern_source.sv
BUILD   := build
VECTORS := sim/vectors/prbs7_expected.txt

PYTHON   ?= python3
IVERILOG ?= iverilog
VVP      ?= vvp
VERILATOR?= verilator
YOSYS    ?= yosys

IVFLAGS  ?= -g2012 -Wall
SYMBOLS  ?= 1000000
TOP_SYNTH?= tx_pattern_source

.PHONY: help golden vectors sim sim-prbs sim-tx sim-long lint synth check waves clean tools

help:
	@sed -n '2,$$ { /^# ----/q; s/^# \{0,1\}//; p; }' Makefile

# ---------------------------------------------------------------------------
# Python model. Needs no HDL toolchain, so it is the first thing to run on a
# new machine and the fastest way to confirm the PRBS-7 convention.
# ---------------------------------------------------------------------------
golden:
	@$(PYTHON) sim/prbs7_golden.py --self-test
	@echo ""
	@$(PYTHON) sim/prbs7_golden.py --checker-model

$(VECTORS): sim/prbs7_golden.py
	@mkdir -p $(dir $@)
	@$(PYTHON) sim/prbs7_golden.py --write $@

vectors: $(VECTORS)

# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------
$(BUILD):
	@mkdir -p $(BUILD)

define need
	@command -v $(1) >/dev/null 2>&1 || { \
	  echo ""; \
	  echo "  $(1) not found. Run 'make tools' for install notes."; \
	  echo ""; \
	  exit 1; }
endef

$(BUILD)/tb_prbs7.vvp: $(RTL) sim/tb_prbs7.sv | $(BUILD)
	$(call need,$(IVERILOG))
	$(IVERILOG) $(IVFLAGS) $(IVEXTRA) -o $@ -s tb_prbs7 $(RTL) sim/tb_prbs7.sv

$(BUILD)/tb_tx_pattern_source.vvp: $(RTL) sim/tb_tx_pattern_source.sv | $(BUILD)
	$(call need,$(IVERILOG))
	$(IVERILOG) $(IVFLAGS) $(IVEXTRA) -o $@ -s tb_tx_pattern_source $(RTL) sim/tb_tx_pattern_source.sv

sim-prbs: $(VECTORS) $(BUILD)/tb_prbs7.vvp
	$(call need,$(VVP))
	@$(VVP) $(BUILD)/tb_prbs7.vvp

sim-tx: $(BUILD)/tb_tx_pattern_source.vvp
	$(call need,$(VVP))
	@$(VVP) $(BUILD)/tb_tx_pattern_source.vvp +symbols=200000

# The M0 acceptance run: at least 1,000,000 symbols with zero errors.
sim-long: $(BUILD)/tb_tx_pattern_source.vvp
	$(call need,$(VVP))
	@$(VVP) $(BUILD)/tb_tx_pattern_source.vvp +symbols=$(SYMBOLS)

sim: sim-prbs sim-tx

waves:
	@$(MAKE) IVEXTRA=-DWAVES sim
	@echo "VCD written to $(BUILD)/"

# ---------------------------------------------------------------------------
# Static checks and resource estimate
# ---------------------------------------------------------------------------
lint:
	$(call need,$(VERILATOR))
	$(VERILATOR) --lint-only -sv -Wall -Wno-fatal --top-module $(TOP_SYNTH) $(RTL)

# Synthesis only, to see how much of the iCE40 the symbol engine costs.
# Place-and-route and a bitstream wait on a verified .pcf - see
# constraints/README.md.
synth: | $(BUILD)
	$(call need,$(YOSYS))
	$(YOSYS) -p "read_verilog -sv -DSYNTHESIS $(RTL); \
	             synth_ice40 -top $(TOP_SYNTH) -json $(BUILD)/$(TOP_SYNTH).json"

check: golden sim lint

clean:
	rm -rf $(BUILD) sim/vectors

tools:
	@echo ""
	@echo "  Toolchain for this directory:"
	@echo ""
	@echo "    Debian / Ubuntu:"
	@echo "      sudo apt-get install iverilog verilator gtkwave"
	@echo "      sudo apt-get install yosys nextpnr-ice40 fpga-icestorm"
	@echo ""
	@echo "    macOS (Homebrew):"
	@echo "      brew install icarus-verilog verilator gtkwave"
	@echo "      brew install --cask oss-cad-suite   # yosys + nextpnr + icestorm"
	@echo ""
	@echo "    Any platform, everything at once:"
	@echo "      YosysHQ oss-cad-suite - https://github.com/YosysHQ/oss-cad-suite-build"
	@echo ""
	@echo "  'make golden' needs only Python 3 and is worth running first."
	@echo ""
