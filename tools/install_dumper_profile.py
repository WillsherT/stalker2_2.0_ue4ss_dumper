#!/usr/bin/env python3
"""
Install the STALKER 2 Update 2.0 dump-only UE4SS profile.

What it does:
  1. Copies UE4SS 5.5 MemberVariableLayout template if needed.
  2. Copies UE4SS 5.5 VTableLayout template if needed.
  3. Patches [FMalloc] with three extra padding entries.
     UE4SS already accounts for one inherited FExec slot internally;
     STALKER 2 Update 2.0 needs three additional entries in this file.
  4. Copies the three custom Lua signatures.
  5. Patches the relevant UE4SS-settings.ini keys for a dump-only run.

It DOES NOT edit mods.txt. Disable Lua/C++ mods manually for the cleanest dump run.
"""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path


GENERAL_VALUES = {
    "UseCache": "0",
    "bUseUObjectArrayCache": "false",
    "DefaultFNameToStringMethod": "Scan",
}

HOOK_VALUES = {
    "HookProcessInternal": "0",
    "HookProcessLocalScriptFunction": "0",
    "HookInitGameState": "0",
    "HookLoadMap": "0",
    "HookCallFunctionByNameWithArguments": "0",
    "HookBeginPlay": "0",
    "HookEndPlay": "0",
    "HookLocalPlayerExec": "0",
    "HookAActorTick": "0",
    "HookEngineTick": "0",
    "HookGameViewportClientTick": "0",
    "HookUObjectProcessEvent": "0",
    "HookProcessConsoleExec": "0",
    "HookUStructLink": "0",
}


def backup(path: Path) -> None:
    if not path.exists():
        return
    bak = path.with_suffix(path.suffix + ".bak")
    if not bak.exists():
        shutil.copy2(path, bak)


def copy_template_if_missing(src: Path, dst: Path) -> None:
    if dst.exists():
        return
    if not src.exists():
        raise FileNotFoundError(f"Template not found: {src}")
    shutil.copy2(src, dst)
    print(f"Created {dst.name} from {src.name}")


def patch_fmalloc(path: Path) -> None:
    text = path.read_text(encoding="utf-8-sig")
    if "FExecExtra1" in text:
        print("VTableLayout.ini: FMalloc padding already present")
        return

    lines = text.splitlines()
    in_fmalloc = False
    insert_after = None

    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            in_fmalloc = stripped.lower() == "[fmalloc]"
            continue
        if in_fmalloc and stripped == "__vecDelDtor":
            insert_after = i
            break

    if insert_after is None:
        raise RuntimeError("Could not locate [FMalloc] / __vecDelDtor in VTableLayout.ini")

    padding = [
        "",
        "; STALKER 2 Update 2.0: additional inherited FExec virtual slot #1",
        "FExecExtra1",
        "; STALKER 2 Update 2.0: additional inherited FExec virtual slot #2",
        "FExecExtra2",
        "; STALKER 2 Update 2.0: additional inherited FExec virtual slot #3",
        "FExecExtra3",
    ]

    lines[insert_after + 1:insert_after + 1] = padding
    backup(path)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("Patched [FMalloc] in VTableLayout.ini")


def patch_ini_section(text: str, section: str, values: dict[str, str]) -> str:
    lines = text.splitlines()
    section_header = f"[{section}]"
    start = None
    end = len(lines)

    for i, line in enumerate(lines):
        if line.strip().lower() == section_header.lower():
            start = i
            break

    if start is None:
        if lines and lines[-1].strip():
            lines.append("")
        lines.append(section_header)
        for key, value in values.items():
            lines.append(f"{key} = {value}")
        return "\n".join(lines) + "\n"

    for i in range(start + 1, len(lines)):
        s = lines[i].strip()
        if s.startswith("[") and s.endswith("]"):
            end = i
            break

    found = set()
    for i in range(start + 1, end):
        raw = lines[i]
        stripped = raw.strip()
        if not stripped or stripped.startswith(";") or stripped.startswith("#"):
            continue
        if "=" not in raw:
            continue
        lhs, _ = raw.split("=", 1)
        key = lhs.strip()
        for target, value in values.items():
            if key.lower() == target.lower():
                lines[i] = f"{target} = {value}"
                found.add(target)
                break

    missing = [k for k in values if k not in found]
    if missing:
        insertion = end
        for key in missing:
            lines.insert(insertion, f"{key} = {values[key]}")
            insertion += 1

    return "\n".join(lines) + "\n"


def patch_settings(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"UE4SS-settings.ini not found: {path}")

    text = path.read_text(encoding="utf-8-sig")
    text = patch_ini_section(text, "General", GENERAL_VALUES)
    text = patch_ini_section(text, "Hooks", HOOK_VALUES)

    backup(path)
    path.write_text(text, encoding="utf-8")
    print("Patched UE4SS-settings.ini for dump-only mode")


def install_signatures(repo_root: Path, ue4ss_dir: Path) -> None:
    src_dir = repo_root / "signatures"
    dst_dir = ue4ss_dir / "UE4SS_Signatures"
    dst_dir.mkdir(parents=True, exist_ok=True)

    for name in ("GUObjectArray.lua", "FName_ToString.lua", "GMalloc.lua"):
        src = src_dir / name
        if not src.exists():
            raise FileNotFoundError(src)
        dst = dst_dir / name
        if dst.exists():
            backup(dst)
        shutil.copy2(src, dst)
        print(f"Installed signature: {name}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("ue4ss_dir", type=Path, help="Path to the game's ue4ss directory")
    args = parser.parse_args()

    ue4ss = args.ue4ss_dir.resolve()
    if not ue4ss.exists():
        raise FileNotFoundError(ue4ss)

    repo_root = Path(__file__).resolve().parents[1]

    member_template = (
        ue4ss / "MemberVarLayoutTemplates" / "MemberVariableLayout_5_05_Template.ini"
    )
    member_target = ue4ss / "MemberVariableLayout.ini"

    vtable_template = (
        ue4ss / "VTableLayoutTemplates" / "VTableLayout_5_05_Template.ini"
    )
    vtable_target = ue4ss / "VTableLayout.ini"

    copy_template_if_missing(member_template, member_target)
    copy_template_if_missing(vtable_template, vtable_target)
    patch_fmalloc(vtable_target)
    install_signatures(repo_root, ue4ss)
    patch_settings(ue4ss / "UE4SS-settings.ini")

    print()
    print("Done.")
    print("For the cleanest run, disable all Lua/C++ mods in Mods/mods.txt.")
    print("Start the game, wait for UE4SS initialization, then use the Dumpers tab.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
