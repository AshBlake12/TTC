
# Satellite Packetizer

This repository provides a C application for preparing data for satellite communication in a single in-memory pipeline. The program combines AX.25 framing, FX.25 error correction and KISS protocol formatting without writing intermediate files, which makes it suitable for embedded environments such as a BeagleBone.

---

## Features

The application generates AX.25 UI frames with CRC-16 error detection, applies FX.25 encoding with a Reed–Solomon (255, 223) scheme, and produces output wrapped in the KISS protocol for transmission over serial links to radios. The design avoids reliance on temporary files and runs directly in memory, while still being modular and command-line driven.

---

## Dependencies

The program requires a GCC toolchain and the `libfec` library. On Debian or Ubuntu the library can be installed with:

```

sudo apt install libfec-dev

```

---

## Build

The application can be compiled using:

```

gcc -Wall satellite_packetizer.c -o packetizer -lfec

```

---

## Usage

The program is invoked with a source callsign, a destination callsign, an input file and an output file. The input file is read in binary mode and segmented into payloads of at most 150 bytes. Each payload is framed, encoded and wrapped in KISS before being written to the output file.

```

./packetizer <source_call> <dest_call> <input_file> <output_kiss_file>

```

Example:

```

./packetizer N0CALL-1 CQ big_data.bin radio_output.kiss

```

---

## Output

The output file contains KISS frames that encapsulate FX.25 encoded AX.25 frames. Each frame carries the original input data payload, a CRC for error detection, additional Reed–Solomon parity for error correction, and framing markers suitable for transmission through standard amateur radio equipment.

---

## Usage

The payload size is capped at 150 bytes so that the complete AX.25 frame including addressing, control, PID and FCS fits within the 223 data bytes of the Reed–Solomon encoder. This design ensures that every generated frame can be reliably encoded and transmitted during short low-earth-orbit satellite passes without excessive bandwidth or power consumption.
