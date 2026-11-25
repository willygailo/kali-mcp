---
name: binary-re-pwn-triage
description: Perform read-only static and dynamic triage on ELF, PE, and APK binaries using binutils, radare2, GDB/GEF, ropper, Ghidra MCP, and Frida/APK tools. Use when ELF, PE, binary reversing, ROP, pwn, APK, Ghidra, or crash analysis tasks appear.
category: binary
triggers:
  ports: []
  services: []
  keywords: [elf, binary, pwn, rop, reversing, reverse, apk, ghidra, frida, buffer, bof, crash]
recommended_tools: [ghidra_triage, execute_command]
allowed_mode: read_only
---

# Binary, Reversing & Mobile Triage (Read-Only)

## Scope & Host Guards
- NOT installed: `checksec`, `pwntools`, `ROPgadget`, `one_gadget`, `patchelf`, `gdb-peda`, `pwndbg`.
- Use: `gdb` + `gef`, `ropper`, `r2`, `ghidra_triage` / `ghidra-mcp`, `frida` / `aapt` / `apksigner`.
- `execute_command` uses `shell=False`: wrap pipes/chains in `bash -c "..."`.
- Never send exploit payloads to remote hosts without operator approval.

## Tactical Decision Tree
- **Unknown binary** -> `file <bin>` + `sha256sum <bin>` -> branch ELF/PE vs APK.
- **ELF/PE**:
  - `readelf -h -S -s <bin>`; `timeout 20s gdb -batch -ex "file <bin>" -ex "checksec" -ex "quit"`
  - `bash -c "strings -n 6 <bin> | grep -iE 'flag|http|pass|secret|key|/bin/' | head -n 80"`
- **Stripped/complex** -> `ghidra_triage` MCP + `timeout 30s r2 -q -c "aaa; afl; pdf @main" <bin>` (fall back to `aa` if `aaa` stalls).
- **NX on + ROP needed** -> `timeout 30s ropper --file <bin> --nocolor --search "pop rdi"`
- **Local crash triage** -> `timeout 20s gdb -batch -ex "file <bin>" -ex "r < /tmp/in.bin" -ex "info registers" -ex "bt"`
- **Android `.apk`**:
  - `aapt dump badging <app.apk>`; `aapt dump xmltree <app.apk> AndroidManifest.xml`
  - `apksigner verify --verbose --print-certs <app.apk>`
  - `unzip -l <app.apk>` + `ghidra_triage` on `lib/*.so`; `frida -U -n <pkg>` on authorized device.
- **Hardcoded keys/JWTs/hashes** -> pivot to `secrets-vcs-config-audit` or `crypto-hash-jwt-triage`.

## Timeout & False-Positive Guards
- Always `gdb -batch` and `r2 -q -c "..."` with `timeout 20s-120s`; `--nocolor` on `ropper`.
- Bound `strings`/`objdump` via `bash -c "... | head -n 80"`.
- `strcpy`/`gets` alone are not exploitable—verify reachability from untrusted input first.

## Severity & Evidence Criteria
- **Critical**: Reachable memory corruption (BOF/UAF/format-string) + missing `NX`/`Canary`/`PIE`; APK unauthenticated exported exec/auth leak.
- **High**: Reachable unsafe sink (`system`, `strcpy`), hardcoded signing/API secrets, release `debuggable="true"`.
- **Medium**: Missing mitigations without proven reachable sink, cleartext HTTP endpoints.
- **Info**: Architecture, mitigation summary, non-sensitive imports.
- **Redaction**: Mask embedded keys, tokens, passwords to `<prefix>...<last4>`.
