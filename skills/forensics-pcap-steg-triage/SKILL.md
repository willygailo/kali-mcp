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

## Scope & Host Guards
- `zsteg` NOT installed — use `exiftool`, `binwalk`, or Python `PIL`/`zlib` for PNG/BMP.
- Record `sha256sum <file>`; work on read-only copies; extract only to `/tmp/<subdir>`.
- `execute_command` uses `shell=False`: wrap pipes/chains in `bash -c "..."`.

## Tactical Decision Tree
- **`.pcap`/`.pcapng`**:
  - `timeout 30s tshark -r <cap.pcap> -q -z io,phs`
  - `timeout 30s tshark -r <cap.pcap> -Y "http.request || dns.qry.name" -T fields -e frame.number -e ip.src -e http.host -e http.request.uri -e dns.qry.name`
  - `timeout 30s tshark -r <cap.pcap> -Y "ftp || telnet || http.authorization || ntlmssp"`
  - Export HTTP: `timeout 30s tshark -r <cap.pcap> --export-objects http,/tmp/pcap_http`
- **Memory dump (`.raw`/`.vmem`)**:
  - `timeout 60s vol -f <mem.raw> windows.info`; `windows.pslist`; `windows.cmdline`; `windows.netscan`
  - `bash -c "timeout 60s vol -f <mem.raw> windows.filescan | grep -iE 'flag|user|pass|kdbx' | head -n 80"`
- **Image/firmware/archive**:
  - `exiftool <file>`; `timeout 30s binwalk <file>`
  - Safe extract: `binwalk -e -C /tmp/bw <file>` or `foremost -i <file> -o /tmp/carved`
  - JPEG/WAV: `steghide info <file>`; `steghide extract -sf <file> -p "" -xf /tmp/steg.out`
- **Office/PDF**: `oleid <doc>` + `olevba -a <doc>` (read-only); `exiftool <file.pdf>` + `binwalk <file.pdf>`.
- **Hashes/creds/ELF carved** -> pivot to `crypto-hash-jwt-triage`, `secrets-vcs-config-audit`, or `binary-re-pwn-triage`.

## Timeout & False-Positive Guards
- Use `tcpdump -nn -r`, `timeout 30s-90s` on tshark/vol; never execute macros.
- `binwalk` FPs: verify carved files with `file` and valid magic headers before trusting.
- Never modify original evidence files.

## Severity & Evidence Criteria
- **Critical**: Cleartext creds/cookies in PCAP/memory, confirmed C2/malicious macro, backdoored firmware.
- **High**: Crackable NTLMv2/Krb5 handshake, hidden executable carved, unauthorized exfil stream.
- **Medium**: Internal hostnames/users leaked via EXIF, DNS, or metadata.
- **Info**: Benign protocol hierarchy, baseline process list, clean metadata.
- **Redaction**: Mask passwords, cookies, NTLM hashes, and API keys to `<prefix>...<last4>`.
