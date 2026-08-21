# STALKER 2 Update 2.0 — UE4SS Dump Profile

A tested **dump-only** UE4SS profile for S.T.A.L.K.E.R. 2 Update 2.0.

The goal is to make **UE4SS Dumpers / CXX Header Dump** usable on the new
engine build. This is not a claim of full gameplay-hook compatibility.

## Tested

- STALKER 2 Update 2.0
- Windows / Steam
- `Stalker2-Win64-Shipping.exe`: 174,726,192 bytes
- UE4SS zDEV `v3.0.1-1028-gd7e7826d`
- UE4SS detects engine version 5.5
- UE4SS Dumpers GUI works in the dump-only profile

## Fixes required on the tested build

- new `GUObjectArray` override
- new `FName::ToString` override
- real `GMalloc` override (PatternSleuth false-positive workaround)
- STALKER 2-specific `FMalloc` vtable padding
- gameplay hooks disabled for the stable dumping profile


## Install

```powershell
python tools\install_dumper_profile.py "...\Stalker2\Binaries\Win64\ue4ss"
```

Then disable Lua/C++ gameplay mods for the cleanest first run, start the game,
wait for UE4SS initialization, and use the **Dumpers** tab.

## Expected critical log lines

```text
GMalloc address: ... <- Lua Script
FName::ToString address: ... <- Lua Script
GUObjectArray address: ... <- Lua Script
```

Expected FMalloc slots include:

```text
FMalloc::Malloc = 0x28
FMalloc::Realloc = 0x38
FMalloc::Free = 0x48
FMalloc::GetDescriptiveName = 0xC8
```

## Limitations

The tested build still reports `GNatives not found` and
`ProcessLocalScriptFunction is not available`.

`HookLoadMap=1` was unstable, so the supplied dump profile disables gameplay hooks.

