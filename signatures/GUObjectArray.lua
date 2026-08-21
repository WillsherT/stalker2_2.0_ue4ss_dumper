-- STALKER 2: Heart of Chornobyl Update 2.0
-- Tested with UE4SS zDEV v3.0.1-1028-gd7e7826d
-- Static target (image base 0x140000000): 0x14A0D5840
-- RVA: 0x0A0D5840
--
-- IMPORTANT:
-- This is intentionally build-specific. If the executable changes,
-- revalidate the target before reusing the signature.

function Register()
    return "48 8D 0D 63 66 D8 07 E8 C6 80 44 00 E9 44 F9 FF FF E8 D8 36 38 00 84 C0 0F 84 5E F9 FF FF 89 F5 B0 01 45 31 E4"
end

function OnMatchFound(MatchAddress)
    local NextInstr = MatchAddress + 0x7
    local Offset = DerefToInt32(MatchAddress + 0x3)

    -- The LEA target is 0x10 bytes before FUObjectArray on this build.
    return NextInstr + Offset + 0x10
end
