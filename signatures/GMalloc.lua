-- STALKER 2: Heart of Chornobyl Update 2.0
-- Tested with UE4SS zDEV v3.0.1-1028-gd7e7826d
-- Static target: GMalloc global at 0x149FD2500
-- RVA: 0x09FD2500
--
-- PatternSleuth produced a false positive at 0x149FD30C0 on this build.
-- This signature resolves the global FMalloc* variable used before
-- the "Allocator: %s" log formatting call.

function Register()
    return "48 8B 0D ?? ?? ?? ?? 48 8B 01 FF 90 C8 00 00 00 48 8D 0D ?? ?? ?? ?? 48 8D 15 ?? ?? ?? ?? 49 89 C0"
end

function OnMatchFound(MatchAddress)
    local NextInstr = MatchAddress + 0x7
    local Offset = DerefToInt32(MatchAddress + 0x3)
    return NextInstr + Offset
end
