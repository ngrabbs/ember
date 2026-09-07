# ---------------------------------------------------------------------------
# EMBER experimental S-band payload - FPGA build and simulation
#
# Milestone M0: symbol timing, pattern selection, PRBS-7, registered output.
# Run every target from this directory.
#
#   make golden     PRBS-7 golden model and checker model (Python only)
#   make lint       Verilator lint, RTL and testbenches
#   make sim        both testbenches
#   make sim-long   the M0 gate: 1,000,000 symbols with zero errors
#   make waves      simulate with FST traces for GTKWave
#   make gtkwave    open the traces in GTKWave
#   make ascii      render the symbol stream in the terminal, no display needed
#   make check      golden + lint + sim
#   make bitstream  build the Arty Z7-20 bitstream (Vivado, on the m75q host)
#   make program    load the bitstream over USB-JTAG
#   make tools      how to install what is missing
#
# Target board is the Digilent Arty Z7 (Zynq-7000) as of 2026-09-07; synthesis
# and programming run under Vivado 2024.2 in the m75q container. The count and
# synth targets below are iCE40 legacy and no longer describe the target.
#
# Every simulation target lints with Verilator before compiling with Icarus.
# Verilator's diagnostics are far better, so it should be the first thing to
# see a change; Icarus then runs the event-driven testbench.
# ---------------------------------------------------------------------------

# So a failure survives a pipe into tee or grep.
SHELL := /bin/bash -o pipefail

RTLDIR := rtl
SIMDIR := sim
BUILD  := build
LOGS   := logs

SRC     := $(wildcard $(RTLDIR)/*.sv)
TOP     := tx_pattern_source
VECTORS := $(SIMDIR)/vectors/prbs7_expected.txt

PYTHON       ?= python3
IVERILOG     ?= iverilog
VVP          ?= vvp
VERILATOR    ?= verilator
YOSYS        ?= yosys
YOSYS_CONFIG ?= yosys-config

# iCE40 primitive simulation library, so a design that instantiates SB_* cells
# still simulates. M0 does not need it; M1 will, as soon as the DAC bus uses
# SB_IO registers. Resolved only when yosys is on the path.
TECH_LIB := $(shell command -v $(YOSYS_CONFIG) >/dev/null 2>&1 && $(YOSYS_CONFIG) --datdir/ice40/cells_sim.v)
ifneq ($(TECH_LIB),)
  IV_TECH := -l$(TECH_LIB)
  DEFINES += -DNO_ICE40_DEFAULT_ASSIGNMENTS
endif

# IceZero carries an iCE40 HX part. Confirm the density and package against the
# board before this matters - see constraints/README.md.
DEVICE  ?= hx
SYMBOLS      ?= 1000000
WAVE_SYMBOLS ?= 400

# The oss-cad-suite wrappers write a fontconfig file under $HOME/.config, which
# fails when that directory is not writable. Pointing HOME at the build tree
# sidesteps it without needing root.
GUI_HOME := $(CURDIR)/$(BUILD)/.home

# Vivado runs in a container on a separate host; only the bitstream comes back.
VIVADO_HOST ?= ngrabbs@192.168.1.252
VIVADO_DIR  ?= vivado-work/ember-payload-fpga

IVERILOG_OPTS := -g2012 -Wall -I$(RTLDIR) $(IV_TECH)

# The RTL is held to a clean -Wall. The two suppressions on the testbench line
# are ordinary testbench idioms, not code smells: PROCASSINIT is `logic clk =
# 0` driven by an always block, BLKSEQ is a blocking assignment inside a
# monitor, and STMTDLY is the # delay that makes the clock.
VERILATOR_OPTS    := -sv --language 1800-2012 -Wall -Wno-DECLFILENAME
VERILATOR_TB_OPTS := $(VERILATOR_OPTS) -Wno-STMTDLY -Wno-PROCASSINIT -Wno-BLKSEQ

YOSYS_OPTS       := -e "no driver"
YOSYS_SYNTH_OPTS := -device $(DEVICE) -abc9

.PHONY: help golden vectors lint sim sim-prbs sim-tx sim-uart sim-long waves gtkwave ascii count synth push bitstream program check clean tools

help:
	@sed -n '2,$$ { /^# ----/q; s/^# \{0,1\}//; p; }' Makefile

# ---------------------------------------------------------------------------
# Python model. Needs no HDL toolchain, so it is the first thing to run on a
# new machine and it checks the part of the design most likely to be wrong.
# ---------------------------------------------------------------------------
golden:
	@$(PYTHON) $(SIMDIR)/prbs7_golden.py --self-test
	@echo ""
	@$(PYTHON) $(SIMDIR)/prbs7_golden.py --checker-model

$(VECTORS): $(SIMDIR)/prbs7_golden.py
	@mkdir -p $(dir $@)
	@$(PYTHON) $(SIMDIR)/prbs7_golden.py --write $@

vectors: $(VECTORS)

$(BUILD) $(LOGS):
	@mkdir -p $@

define need
	@command -v $(1) >/dev/null 2>&1 || { \
	  echo ""; \
	  echo "  $(1) not found. Run 'make tools' for install notes."; \
	  echo ""; \
	  exit 1; }
endef

# ---------------------------------------------------------------------------
# Lint
# ---------------------------------------------------------------------------
lint:
	$(call need,$(VERILATOR))
	@echo "=== lint: RTL ==="
	$(VERILATOR) --lint-only $(VERILATOR_OPTS) $(DEFINES) --top-module $(TOP) $(SRC)
	@echo "=== lint: tb_prbs7 ==="
	$(VERILATOR) --lint-only $(VERILATOR_TB_OPTS) $(DEFINES) --top-module tb_prbs7 $(SRC) $(SIMDIR)/tb_prbs7.sv
	@echo "=== lint: tb_tx_pattern_source ==="
	$(VERILATOR) --lint-only $(VERILATOR_TB_OPTS) $(DEFINES) --top-module tb_tx_pattern_source $(SRC) $(SIMDIR)/tb_tx_pattern_source.sv
	@echo "=== lint: tb_uart_console ==="
	$(VERILATOR) --lint-only $(VERILATOR_TB_OPTS) $(DEFINES) --top-module tb_uart_console $(SRC) $(SIMDIR)/tb_uart_console.sv
	@echo "=== lint: top_arty_z7 ==="
	$(VERILATOR) --lint-only $(VERILATOR_OPTS) $(DEFINES) --top-module top_arty_z7 $(SRC)
	@echo "=== lint clean ==="

# ---------------------------------------------------------------------------
# Simulation - Verilator lints first, then Icarus builds and runs
# ---------------------------------------------------------------------------
$(BUILD)/tb_prbs7.vvp: $(SRC) $(SIMDIR)/tb_prbs7.sv $(MAKEFILE_LIST) | $(BUILD)
	$(call need,$(VERILATOR))
	$(call need,$(IVERILOG))
	@$(VERILATOR) --lint-only $(VERILATOR_TB_OPTS) $(DEFINES) --top-module tb_prbs7 $(SRC) $(SIMDIR)/tb_prbs7.sv
	$(IVERILOG) $(IVERILOG_OPTS) $(DEFINES) $(IVEXTRA) -o $@ -s tb_prbs7 $(SRC) $(SIMDIR)/tb_prbs7.sv

$(BUILD)/tb_tx_pattern_source.vvp: $(SRC) $(SIMDIR)/tb_tx_pattern_source.sv $(MAKEFILE_LIST) | $(BUILD)
	$(call need,$(VERILATOR))
	$(call need,$(IVERILOG))
	@$(VERILATOR) --lint-only $(VERILATOR_TB_OPTS) $(DEFINES) --top-module tb_tx_pattern_source $(SRC) $(SIMDIR)/tb_tx_pattern_source.sv
	$(IVERILOG) $(IVERILOG_OPTS) $(DEFINES) $(IVEXTRA) -o $@ -s tb_tx_pattern_source $(SRC) $(SIMDIR)/tb_tx_pattern_source.sv

sim-prbs: $(VECTORS) $(BUILD)/tb_prbs7.vvp
	$(call need,$(VVP))
	@$(VVP) $(BUILD)/tb_prbs7.vvp $(VVP_OPTS)

sim-tx: $(BUILD)/tb_tx_pattern_source.vvp
	$(call need,$(VVP))
	@$(VVP) $(BUILD)/tb_tx_pattern_source.vvp $(VVP_OPTS) +symbols=200000

# The M0 acceptance run: at least 1,000,000 symbols with zero errors.
sim-long: $(BUILD)/tb_tx_pattern_source.vvp
	$(call need,$(VVP))
	@$(VVP) $(BUILD)/tb_tx_pattern_source.vvp $(VVP_OPTS) +symbols=$(SYMBOLS)

$(BUILD)/tb_uart_console.vvp: $(SRC) $(SIMDIR)/tb_uart_console.sv $(MAKEFILE_LIST) | $(BUILD)
	$(call need,$(VERILATOR))
	$(call need,$(IVERILOG))
	@$(VERILATOR) --lint-only $(VERILATOR_TB_OPTS) $(DEFINES) --top-module tb_uart_console $(SRC) $(SIMDIR)/tb_uart_console.sv
	$(IVERILOG) $(IVERILOG_OPTS) $(DEFINES) $(IVEXTRA) -o $@ -s tb_uart_console $(SRC) $(SIMDIR)/tb_uart_console.sv

sim-uart: $(BUILD)/tb_uart_console.vvp
	$(call need,$(VVP))
	@$(VVP) $(BUILD)/tb_uart_console.vvp $(VVP_OPTS)

sim: sim-prbs sim-tx sim-uart

# The .vvp files are removed on both sides so that a wave build is never
# silently reused by a later plain `make sim`, and vice versa - IVEXTRA is not
# a prerequisite, so make cannot see the difference on its own.
waves:
	@rm -f $(BUILD)/*.vvp
	@$(MAKE) IVEXTRA=-DWAVES VVP_OPTS=-fst sim
	@rm -f $(BUILD)/*.vvp
	@echo ""
	@echo "  FST traces in $(BUILD)/ - view with: gtkwave $(BUILD)/tb_tx_pattern_source.fst"

# ---------------------------------------------------------------------------
# Waveform viewing
# ---------------------------------------------------------------------------
$(BUILD)/wave.fst: $(SRC) $(SIMDIR)/tb_tx_pattern_source.sv $(MAKEFILE_LIST) | $(BUILD)
	$(call need,$(IVERILOG))
	@$(IVERILOG) $(IVERILOG_OPTS) $(DEFINES) -DWAVES -o $(BUILD)/wave.vvp \
	   -s tb_tx_pattern_source $(SRC) $(SIMDIR)/tb_tx_pattern_source.sv
	@$(VVP) $(BUILD)/wave.vvp -fst +symbols=$(WAVE_SYMBOLS) > /dev/null
	@mv -f $(BUILD)/tb_tx_pattern_source.fst $@

$(BUILD)/wave.vcd: $(BUILD)/wave.fst
	@fst2vcd $< -o $@ 2>/dev/null

# Sample tx_symbol on every symbol_tick, draw it, and check the captured bits
# against the golden PRBS-7 at all 127 phases. Needs no display.
ascii: $(BUILD)/wave.vcd
	@$(PYTHON) $(SIMDIR)/ascii_wave.py $< --last 56

gtkwave: $(BUILD)/wave.fst
	@mkdir -p $(GUI_HOME)
	@HOME=$(GUI_HOME) gtkwave $(BUILD)/wave.fst

# ---------------------------------------------------------------------------
# Synthesis - iCE40 LEGACY.
#
# Kept for reference only. The target board is now the Arty Z7 and synthesis
# runs under Vivado 2024.2 in the m75q container; see constraints/README.md.
# ---------------------------------------------------------------------------
count: $(SRC) $(MAKEFILE_LIST) | $(LOGS)
	$(call need,$(YOSYS))
	@$(YOSYS) $(YOSYS_OPTS) -q -l $(LOGS)/$(TOP)_count.log \
	  -p 'read_verilog -DSYNTHESIS $(DEFINES) -I$(RTLDIR) -sv $(SRC); synth_ice40 $(YOSYS_SYNTH_OPTS) -top $(TOP) -noflatten'
	@sed -n '/Printing statistics/,/Executing CHECK pass/p' $(LOGS)/$(TOP)_count.log | sed '$$d'
	@echo "=== full log in $(LOGS)/$(TOP)_count.log ==="

synth: $(SRC) $(MAKEFILE_LIST) | $(BUILD) $(LOGS)
	$(call need,$(YOSYS))
	$(YOSYS) $(YOSYS_OPTS) -q -l $(LOGS)/$(TOP)_synth.log \
	  -p 'read_verilog -DSYNTHESIS $(DEFINES) -I$(RTLDIR) -sv $(SRC); synth_ice40 $(YOSYS_SYNTH_OPTS) -top $(TOP) -json $(BUILD)/$(TOP).json'
	@echo "=== netlist: $(BUILD)/$(TOP).json ==="

# ---------------------------------------------------------------------------
# Hardware: Arty Z7-20 via Vivado 2024.2 in the container on $(VIVADO_HOST).
# Sources are pushed, the build runs there, and the bitstream and reports come
# back into build/vivado/. Nothing about the simulation flow depends on this.
# ---------------------------------------------------------------------------
push:
	@ssh $(VIVADO_HOST) 'mkdir -p $(VIVADO_DIR)'
	@rsync -az --delete \
	   --exclude 'build/' --exclude 'logs/' --exclude '__pycache__/' \
	   ./ $(VIVADO_HOST):$(VIVADO_DIR)/

bitstream: push
	@ssh $(VIVADO_HOST) 'cd $(VIVADO_DIR) && ./vivado/build.sh'
	@mkdir -p $(BUILD)/vivado
	@rsync -az $(VIVADO_HOST):$(VIVADO_DIR)/build/vivado/ $(BUILD)/vivado/
	@echo ""
	@grep -E 'WNS|Slack' $(BUILD)/vivado/timing_summary.rpt 2>/dev/null | head -3 || true
	@echo "  bitstream: $(BUILD)/vivado/top_arty_z7.bit"

program: push
	@ssh $(VIVADO_HOST) 'cd $(VIVADO_DIR) && ./vivado/build.sh program'

check: golden lint sim

clean:
	rm -rf $(BUILD) $(LOGS) $(SIMDIR)/vectors

tools:
	@echo ""
	@echo "  Everything at once, no root needed - this is the recommended route:"
	@echo ""
	@echo "    https://github.com/YosysHQ/oss-cad-suite-build/releases/latest"
	@echo "    tar xzf oss-cad-suite-linux-x64-*.tgz -C ~/opt"
	@echo "    source ~/opt/oss-cad-suite/environment"
	@echo ""
	@echo "  One tarball with iverilog, verilator, yosys, nextpnr-ice40,"
	@echo "  icestorm and gtkwave at consistent versions. Add the source line"
	@echo "  to your shell profile."
	@echo ""
	@echo "  Distribution packages work too, but mix versions and need root:"
	@echo "    Debian/Ubuntu:  sudo apt-get install iverilog verilator yosys \\"
	@echo "                         nextpnr-ice40 fpga-icestorm gtkwave"
	@echo "    macOS:          brew install icarus-verilog verilator gtkwave"
	@echo "                    brew install --cask oss-cad-suite"
	@echo ""
	@echo "  'make golden' needs only Python 3 and is worth running first."
	@echo ""
