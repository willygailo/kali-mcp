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

## Environment Notes
- Standalone `checksec`, `pwntools`, `pwninit`, `ROPgadget`, `one_gadget`, `patchelf`, `gdb-peda`, and `pwndbg` are **NOT installed**.
- Use **`gdb` with `gef`** for `checksec`, **`ropper`** for gadgets, **`r2`** (`radare2`), **`ghidra-mcp`** / `ghidra_triage`, and **`frida` / `aapt` / `apksigner`** for Android APKs.

## Step 1: Fast Static Metadata & Protections
- Identify format, architecture, linkage, and symbols:
  - `file <bin>`
  - `readelf -h -S -s <bin>` (ELF headers, sections, imports/exports)
  - `strings -n 6 <bin> | grep -iE "flag|http|pass|secret|key|/bin/|sql"`
- Check binary mitigations (NX, PIE, Canary, RELRO) via GEF:
  - `gdb -q -ex "file <bin>" -ex "checksec" -ex "quit"`
- Disassemble key functions / PLT calls:
  - `objdump -d -M intel <bin> | less` or `r2 -q -c "aaa; afl; pdf @main" <bin>`

## Step 2: Headless Decompilation & Gadget Discovery
- **Ghidra MCP (`ghidra_triage` tool or headless CLI)**:
  - Run `ghidra_triage` on the local binary path, or `ghidra-mcp --headless --binary <bin>` to inspect functions, decompiled C pseudocode, cross-references, and string refs.
- **ROP / Gadget Inventory (Read-Only)**:
  - `ropper --file <bin> --search "pop rdi"` (or `--nocolor` for clean capture).

## Step 3: Local Dynamic Inspection (GDB + GEF)
- Inspect crash state, registers, and memory layout locally in an isolated lab binary:
  - `gdb -q <bin>` -> `b main` -> `r` -> `vmmap` / `got` / `pattern create` (GEF commands).
- Never send crash/exploit payloads to remote hosts without explicit operator confirmation.

## Step 4: Android APK Triage
- Inspect manifest, permissions, activities, and exported components:
  - `aapt dump badging <app.apk>` and `aapt dump xmltree <app.apk> AndroidManifest.xml`
- Verify APK signature & certs:
  - `apksigner verify --verbose --print-certs <app.apk>`
- Inspect/hook lab app runtime (authorized device/emulator):
  - `frida -U -n <package>` or `frida-trace -U -i "open*" <package>`
- Use `unzip -l <app.apk>` + `strings`/`ghidra_triage` on `lib/*.so` native libraries.
