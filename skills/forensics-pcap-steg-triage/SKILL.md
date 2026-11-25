---
name: forensics-pcap-steg-triage
description: Analyze packet captures, memory dumps, firmware/carved blobs, document macros, and image metadata or steganography in read-only mode. Use when pcap, pcapng, Wireshark, memory dumps, Volatility, EXIF, stego, PDF, or Office macro artifacts appear.
category: forensics
triggers:
  ports: []
  services: []
  keywords: [pcap, pcapng, wireshark, memory, dump, volatility, exif, steg, stego, pdf, office, macro]
recommended_tools: [execute_command]
allowed_mode: read_only
---

# Forensics, PCAP, Memory & Steg Triage

## Environment Notes
- `zsteg` is **NOT installed** on this host — for PNG/BMP LSB inspection use `exiftool`, `binwalk`, or Python `PIL`/`zlib` bitplane checks.
- Work on read-only copies of evidence files; verify SHA256 hashes (`sha256sum <file>`) before extracting artifacts.

## Step 1: Packet Captures (`.pcap` / `.pcapng`)
- Protocol hierarchy, conversations, and HTTP/DNS summary:
  - `tshark -r <cap.pcap> -q -z io,phs`
  - `tshark -r <cap.pcap> -q -z conv,tcp`
  - `tshark -r <cap.pcap> -Y "http.request || dns.qry.name" -T fields -e frame.number -e ip.src -e http.host -e http.request.uri -e dns.qry.name`
- Extract credentials, cleartext streams, or exported objects:
  - `tshark -r <cap.pcap> -Y "ftp || telnet || http.authorization || ntlmssp"`
  - `tshark -r <cap.pcap> --export-objects http,/tmp/pcap_http`
- Quick raw filter fallback: `tcpdump -nn -A -r <cap.pcap> | grep -iE "user|pass|flag|token"`.

## Step 2: Memory Forensics (Volatility 3: `vol` / `volshell`)
- Identify OS/kernel banner and processes:
  - `vol -f <mem.raw> windows.info` (or `linux.banners` / `banners.Banners`)
  - `vol -f <mem.raw> windows.pslist` and `windows.pstree`
  - `vol -f <mem.raw> windows.cmdline` and `windows.netscan`
- Inspect suspicious memory regions, registry, or files read-only:
  - `vol -f <mem.raw> windows.filescan | grep -iE "flag|user|pass|kdbx|txt"`
  - `vol -f <mem.raw> windows.dumpfiles --virtaddr <addr>` (save to `/tmp/vol_out/`).

## Step 3: Files, Firmware, Images & Steganography
- Metadata & embedded payload inspection:
  - `exiftool <file>`
  - `binwalk <file>` (extract only if safe: `binwalk -e -C /tmp/bw <file>`)
  - `foremost -i <file> -o /tmp/carved`
- JPEG/WAV/AU stego check:
  - `steghide info <file>` (try empty passphrase first: `steghide extract -sf <file> -p "" -xf /tmp/steg.out`)

## Step 4: Office & PDF Document Analysis
- Detect and decode VBA macros safely without executing:
  - `oleid <doc>`
  - `olevba -a <doc>` (deobfuscates macro strings/IOCs read-only).
- For PDFs: inspect metadata with `exiftool <file.pdf>`, embedded streams with `binwalk`, and strings with `strings <file.pdf>`.
