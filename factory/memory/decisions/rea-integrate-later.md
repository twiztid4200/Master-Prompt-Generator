# REA integration evaluation

Status: INTEGRATE LATER. Not installed. Not imported. Not required for Phase 1.

## Identity

The owner pointed at https://github.com/webdebug/reverse-engineering-mcp.

That repository exists. Inspected tree SHA: `7b18c581409848077de7a9cb6d7d1a0b91a02e12`.

Its `package.json` does not name that repository as upstream:

- package name: `rea-agents`
- version: `5.0.0`
- license field: `MIT`
- repository URL: `git+https://github.com/morluto/rea.git`
- homepage: `https://github.com/morluto/rea#readme`
- mcpName: `io.github.morluto/rea`

`LICENSE` in the inspected tree is the MIT license, copyright (c) 2026 morluto.

A screenshot badge is not enough to settle provenance. The canonical project, as declared by the package metadata in the inspected tree, is morluto/rea. webdebug/reverse-engineering-mcp must be treated as an unverified mirror or fork until the owner confirms which remote is authoritative.

Star counts in secondary writeups were not used. This evaluation did not call the GitHub stargazers API.

## What the inspected tree actually supports

From `package.json` engines, scripts, and the README fetched from the same repository:

- CLI bin: `rea` and `rea-agents` via `scripts/rea.mjs`
- MCP server start script: `npm start` runs `node scripts/rea.mjs mcp`
- Node.js: `^22.19.0 || ^24.11.0 || >=26.0.0`
- npm package manager pinned to `11.16.0`
- README describes local analysis, not a hosted upload service
- Documented platforms in the README summary: macOS 12+, Ubuntu 24.04+, Fedora 41+, 64-bit Arch Linux, CachyOS. Windows x64 is described as experimental Ghidra P0.
- Documented providers: Ghidra, IDA Pro through an external MCP, Hopper. Android path mentions JADX. Firmware path mentions Binwalk and Unblob.
- Documented file types include Mach-O, ELF, PE, Mac app bundles, ZIP, APK, IPA, ASAR, plists, Interface Builder, asset catalogs, DMG, firmware regions, .NET assemblies, JavaScript/Electron, and websites.
- CLI names present in the README include `rea setup`, `rea doctor`, `rea analyze`, `rea decompile`, `rea evidence-import`, `rea evidence-export`, `rea compare`, and `rea mcp`.
- Static JavaScript analysis is described as not executing modules. Runtime capture is a separate command (`rea capture-process`, browser capture). That is a documented default, not a guarantee for every provider.

`.gitmodules` and `third_party/` exist. Their dependency licenses were not fully audited. That is a reason to wait.

## Adapter fit

A future tool declaration can wrap `rea` as a local command or MCP server. Phase 1 only registers native Python functions. The registry already rejects a tool whose declaration says `executes_code` is true.

Findings could map into the Scout report only if each item keeps the tool version, command, evidence quote, and an explicit unknown list. Decompiler pseudocode must be labeled inference, not recovered original source. Static analysis must not be labeled as proof of runtime behavior.

## Security

- Analyzing untrusted binaries can be unsafe if a provider launches the sample or a helper.
- `install.sh` piped to a shell and `npx rea-agents setup` change local agent configuration. Both require explicit approval.
- Ghidra, IDA, and Hopper have their own licenses. IDA Pro is not MIT.
- Do not bypass access controls, DRM, or authentication. Do not copy proprietary software into this repository.

## Cost

Integration would add Node 22.19+, a large TypeScript toolchain, optional JDK/Ghidra, and provider-specific installers. It does not help the Phase 1 mission, which only needs public GitHub metadata.

## Recommendation

INTEGRATE LATER, as an optional tool behind the adapter, after:

1. The owner confirms the canonical remote.
2. Third-party and provider licenses are listed.
3. A sandbox policy exists for any execution mode.
4. A fixture proves REA output can be converted into a Scout finding without dropping provenance.

Do not make REA a mandatory dependency. MASTER AWAKENING keeps the contracts, verification, memory, and cost log.
