-- STALKER 2: Heart of Chornobyl Update 2.0
-- Tested with UE4SS zDEV v3.0.1-1028-gd7e7826d
-- Static target (image base 0x140000000): 0x14211850C
-- RVA: 0x0211850C

function Register()
    return "48 8D 4C 24 38 48 89 01 48 8D 7C 24 20 48 89 FA E8 ?? ?? ?? ?? 48 39 F7 74 ?? 48 8B 0E"
end

function OnMatchFound(MatchAddress)
    local CallInstr = MatchAddress + 0x10
    local NextInstr = CallInstr + 0x5
    local Offset = DerefToInt32(CallInstr + 0x1)
    return NextInstr + Offset
end
