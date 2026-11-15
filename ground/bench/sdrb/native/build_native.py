"""Build optional ARM module against existing, read-only PetaLinux staging."""
import argparse,hashlib,json,os,subprocess
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--runtime-build',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
a.output.mkdir(parents=True,exist_ok=True)
staging=a.runtime_build/'build/tmp/sysroots-components'
sysroot=a.output/'sysroot';sysroot.mkdir(exist_ok=True)
packages=('linux-libc-headers','glibc','libgcc','gcc-runtime','boost','fmt','spdlog','volk','gmp','python3','gnuradio')
for package in packages:
 src=staging/'cortexa9t2hf-neon'/package
 assert src.is_dir(),src
 for folder,dirs,files in os.walk(src):
  for name in files:
   original=Path(folder)/name;target=sysroot/original.relative_to(src)
   target.parent.mkdir(parents=True,exist_ok=True)
   if not target.is_symlink() and not target.exists():
    target.symlink_to(os.readlink(original) if original.is_symlink() else original)
# An out-of-sysroot symlink to glibc's linker script loses ld's prefix
# resolution. Copy only this text into our private sysroot with explicit =paths.
libc_script=sysroot/'usr/lib/libc.so'
script=libc_script.read_text()
assert script.startswith('/* GNU ld script')
libc_script.unlink();libc_script.write_text(script.replace(' /usr/lib/',' =/usr/lib/'))
compiler=staging/'x86_64/gcc-cross-arm/usr/bin/arm-xilinx-linux-gnueabi/arm-xilinx-linux-gnueabi-g++'
binutils=staging/'x86_64/binutils-cross-arm/usr/bin/arm-xilinx-linux-gnueabi'
toolbin=a.output/'toolbin';toolbin.mkdir(exist_ok=True)
for name in ('as','ld','strip'):
 target=toolbin/name
 if not target.exists():target.symlink_to(binutils/('arm-xilinx-linux-gnueabi-'+name))
pybind=staging/'x86_64/python3-pybind11-native/usr/lib/python3.12/site-packages/pybind11/include'
source=Path(__file__).resolve().parent
# Definitions exported by the installed GNU Radio, spdlog, and fmt targets.
flags=['-B'+str(toolbin)+'/', '-DGR_MPLIB_GMP','-DGR_PERFORMANCE_COUNTERS','-DSPDLOG_SHARED_LIB','-DSPDLOG_COMPILED_LIB','-DSPDLOG_FMT_EXTERNAL','-DFMT_SHARED','-std=c++17','-O3','-fPIC','-pthread','-mthumb','-mcpu=cortex-a9','-mfpu=neon','-mfloat-abi=hard','--sysroot='+str(sysroot),
 '-I'+str(sysroot/'usr/include/c++/13.3.0'),'-I'+str(sysroot/'usr/include/c++/13.3.0/arm-xilinx-linux-gnueabi'),
 '-I'+str(sysroot/'usr/include/python3.12'),'-I'+str(pybind)]
command=[str(compiler),*flags,'-shared',str(source/'headroom_mix.cpp'),'-L'+str(sysroot/'usr/lib'),
 '-Wl,-rpath-link,'+str(sysroot/'usr/lib'),'-lgnuradio-runtime','-lgnuradio-pmt','-lspdlog','-lfmt','-o',str(a.output/'headroom_mix.so')]
version=subprocess.run([str(compiler),'--version'],capture_output=True,text=True,check=True).stdout
subprocess.run(command,check=True)
strip=binutils/'arm-xilinx-linux-gnueabi-strip'
subprocess.run([str(strip),'--strip-unneeded',str(a.output/'headroom_mix.so')],check=True)
subprocess.run(['g++','-std=c++17','-O2',str(source/'test_headroom_core.cpp'),'-o',str(a.output/'test-core')],check=True)
core=subprocess.run([str(a.output/'test-core')],capture_output=True,text=True,check=True)
result=dict(compiler=version,command=command,packages=packages,core_test=core.stdout,
 sources={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in source.glob('*') if f.is_file()},
 module_sha256=hashlib.sha256((a.output/'headroom_mix.so').read_bytes()).hexdigest())
(a.output/'build.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
