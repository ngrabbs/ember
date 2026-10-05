# Pi OAI build record

Candidate source commit: `29d5fa7d38bb1ee8935ef7ae30a396d53772ea4f`.
Checkout: `/home/ngrabbs/work/ember-lte/openairinterface5g` on ember-ground.

Installed development packages on Debian 13:

```sh
sudo apt-get install --no-install-recommends \
  git cmake ninja-build build-essential pkg-config libconfig-dev libssl-dev \
  libsctp-dev libcap-dev libuhd-dev libfftw3-dev libyaml-cpp-dev \
  autoconf automake libtool bison flex xxd libsimde-dev zlib1g-dev
```

GCC 14.2, CMake 3.31.6, UHD 4.8.0.0+ds1-2, SIMDe package 0.8.2-3.
CMake's automatic ASN.1 compiler build fetches upstream asn1c commit
`940dd5fa9f3917913fd487b13dfddfacd0ded06e` into the build tree.

Following upstream AGENTS.md, use direct CMake rather than build_oai:

```sh
cd ~/work/ember-lte/openairinterface5g
git checkout 29d5fa7d38bb1ee8935ef7ae30a396d53772ea4f
cmake -S . -B build-lte -GNinja -DCMAKE_BUILD_TYPE=Release \
  -DAUTO_DOWNLOAD_ASN1C=ON -DT_TRACER=OFF -DOAI_USRP=ON
cmake --build build-lte --target lte-softmodem oai_usrpdevif rfsimulator params_libconfig coding dfts --parallel 3
```

Configuration succeeded. Early compilation attempts identified missing `xxd`,
SIMDe headers, and `zlib.h`; the package list above includes those fixes.
Final build/startup status is recorded in the ground-radio results document.

No OAI source modifications were made. Full source and generated objects stay
outside the EMBER repository. Runtime hardware support and Walter attach still
need validation even if compilation succeeds.

## EPC on the Pi

A clean Git archive of the previous srsRAN source (`ec29b0c1f`) was staged under
`/home/ngrabbs/work/ember-lte/srsRAN_4G`; the existing x1c working tree was not
changed. The archive excludes its untracked private subscriber database.

```sh
sudo apt-get install --no-install-recommends \
  libmbedtls-dev libboost-program-options-dev rapidjson-dev libconfig++-dev
cd ~/work/ember-lte/srsRAN_4G
cmake -S . -B build-epc -GNinja -DCMAKE_BUILD_TYPE=Release \
  -DENABLE_SRSUE=OFF -DENABLE_SRSENB=OFF -DENABLE_RF_PLUGINS=OFF \
  -DENABLE_UHD=OFF -DENABLE_SOAPYSDR=OFF -DENABLE_BLADERF=OFF \
  -DCMAKE_CXX_FLAGS=-Wno-error=array-bounds
cmake --build build-epc --target srsepc --parallel 1
```

Pi runtime directory: `/home/ngrabbs/work/ember-lte/configs`. It contains
`epc.conf`, `enb.band13.emtc.conf`, and a privately copied `user_db.csv` with
mode 0600; the directory is mode 0700. No keys were copied into EMBER Git.

The initial same-host topology uses distinct loopback addresses for eNB and EPC.
EPC startup requires privileges to create its SGi TUN interface. Startup/attach
status is recorded separately from compilation status in the results document.

GCC 14 emitted array-bounds warnings in the old srsEPC ASN.1 dyn_array
implementation, promoted by upstream Werror. The build keeps those warnings
visible but does not treat that diagnostic as fatal. This is a build workaround,
not a demonstrated fix of the warned code. No srsRAN source was changed.
