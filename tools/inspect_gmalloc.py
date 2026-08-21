#!/usr/bin/env python3
"""
Read the live STALKER 2 Update 2.0 GMalloc object and dump its vtable.

Known Update 2.0 GMalloc global RVA: 0x09FD2500
"""

import ctypes
import time
from ctypes import wintypes

EXE_NAME = "Stalker2-Win64-Shipping.exe"
GMALLOC_RVA = 0x09FD2500

PROCESS_VM_READ = 0x0010
PROCESS_QUERY_INFORMATION = 0x0400
TH32CS_SNAPPROCESS = 0x00000002
TH32CS_SNAPMODULE = 0x00000008
TH32CS_SNAPMODULE32 = 0x00000010
INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value

k32 = ctypes.WinDLL("kernel32", use_last_error=True)


class PROCESSENTRY32W(ctypes.Structure):
    _fields_ = [
        ("dwSize", wintypes.DWORD),
        ("cntUsage", wintypes.DWORD),
        ("th32ProcessID", wintypes.DWORD),
        ("th32DefaultHeapID", ctypes.c_size_t),
        ("th32ModuleID", wintypes.DWORD),
        ("cntThreads", wintypes.DWORD),
        ("th32ParentProcessID", wintypes.DWORD),
        ("pcPriClassBase", wintypes.LONG),
        ("dwFlags", wintypes.DWORD),
        ("szExeFile", wintypes.WCHAR * 260),
    ]


class MODULEENTRY32W(ctypes.Structure):
    _fields_ = [
        ("dwSize", wintypes.DWORD),
        ("th32ModuleID", wintypes.DWORD),
        ("th32ProcessID", wintypes.DWORD),
        ("GlblcntUsage", wintypes.DWORD),
        ("ProccntUsage", wintypes.DWORD),
        ("modBaseAddr", ctypes.POINTER(ctypes.c_byte)),
        ("modBaseSize", wintypes.DWORD),
        ("hModule", wintypes.HMODULE),
        ("szModule", wintypes.WCHAR * 256),
        ("szExePath", wintypes.WCHAR * 260),
    ]


k32.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
k32.OpenProcess.restype = wintypes.HANDLE

k32.ReadProcessMemory.argtypes = [
    wintypes.HANDLE,
    ctypes.c_void_p,
    ctypes.c_void_p,
    ctypes.c_size_t,
    ctypes.POINTER(ctypes.c_size_t),
]


def find_pid():
    snap = k32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
    if snap == INVALID_HANDLE_VALUE:
        return None

    pe = PROCESSENTRY32W()
    pe.dwSize = ctypes.sizeof(pe)

    try:
        ok = k32.Process32FirstW(snap, ctypes.byref(pe))
        while ok:
            if pe.szExeFile.lower() == EXE_NAME.lower():
                return pe.th32ProcessID
            ok = k32.Process32NextW(snap, ctypes.byref(pe))
    finally:
        k32.CloseHandle(snap)
    return None


def get_module(pid):
    snap = k32.CreateToolhelp32Snapshot(
        TH32CS_SNAPMODULE | TH32CS_SNAPMODULE32, pid
    )
    if snap == INVALID_HANDLE_VALUE:
        raise ctypes.WinError(ctypes.get_last_error())

    me = MODULEENTRY32W()
    me.dwSize = ctypes.sizeof(me)

    try:
        ok = k32.Module32FirstW(snap, ctypes.byref(me))
        while ok:
            if me.szModule.lower() == EXE_NAME.lower():
                base = ctypes.cast(me.modBaseAddr, ctypes.c_void_p).value
                return base, me.modBaseSize
            ok = k32.Module32NextW(snap, ctypes.byref(me))
    finally:
        k32.CloseHandle(snap)

    raise RuntimeError("Module not found")


def read_mem(handle, addr, size):
    buf = ctypes.create_string_buffer(size)
    read = ctypes.c_size_t()

    ok = k32.ReadProcessMemory(
        handle,
        ctypes.c_void_p(addr),
        buf,
        size,
        ctypes.byref(read),
    )
    if not ok or read.value != size:
        return None
    return buf.raw


def qword(handle, addr):
    data = read_mem(handle, addr, 8)
    if data is None:
        return None
    return int.from_bytes(data, "little")


def main():
    print("Waiting for Stalker2...")
    pid = None
    while pid is None:
        pid = find_pid()
        if pid is None:
            time.sleep(0.25)

    print(f"PID: {pid}")
    base, module_size = get_module(pid)
    print(f"Module base : 0x{base:X}")
    print(f"Module size : 0x{module_size:X}")

    handle = k32.OpenProcess(
        PROCESS_VM_READ | PROCESS_QUERY_INFORMATION,
        False,
        pid,
    )
    if not handle:
        raise ctypes.WinError(ctypes.get_last_error())

    try:
        gmalloc_address = base + GMALLOC_RVA
        print(f"GMalloc RVA : 0x{GMALLOC_RVA:X}")
        print(f"GMalloc addr: 0x{gmalloc_address:X}")

        value = None
        for _ in range(200):
            value = qword(handle, gmalloc_address)
            if value:
                break
            time.sleep(0.05)

        if not value:
            raise RuntimeError("GMalloc stayed NULL")

        allocator = value
        vtable = qword(handle, allocator)
        if not vtable:
            raise RuntimeError("FMalloc vtable is NULL")

        print()
        print(f"[GMalloc] = 0x{allocator:X}")
        print("Interpretation: GMalloc is a global FMalloc*")
        print(f"FMalloc object: 0x{allocator:X}")
        print(f"VTable ptr    : 0x{vtable:X}")

        module_end = base + module_size

        def in_game_module(addr):
            return base <= addr < module_end

        print()
        print("VTable entries:")
        print()

        for i in range(32):
            slot = vtable + i * 8
            fn = qword(handle, slot)
            if fn is None:
                print(f"{i:02d} +0x{i*8:02X}: unreadable")
                continue

            location = (
                f"game+0x{fn-base:X}"
                if in_game_module(fn)
                else "outside game module"
            )
            code = read_mem(handle, fn, 16)
            code_text = code.hex(" ").upper() if code else "<unreadable>"

            print(f"{i:02d} +0x{i*8:02X}: 0x{fn:016X}  {location}")
            print(f"                 {code_text}")
    finally:
        k32.CloseHandle(handle)


if __name__ == "__main__":
    main()
