# STALKER 2 Update 2.0 — UE4SS Dump Profile

Рабочий dump-only профиль для **S.T.A.L.K.E.R. 2: Heart of Chornobyl Update 2.0**
после перехода игры на новый UE5-билд.

Цель этого репозитория — запустить **UE4SS Dumpers / CXX Header Dump**
на Update 2.0. Это **не** полный конфиг совместимости всех UE4SS-хуков.

## Проверено

- S.T.A.L.K.E.R. 2 Update 2.0
- Windows / Steam
- `Stalker2-Win64-Shipping.exe`: 174,726,192 байта
- UE4SS zDEV `v3.0.1-1028-gd7e7826d`
- UE4SS определяет Engine Version как 5.5
- Object Dumper / Dumpers GUI: работает в dump-only режиме

## Что сломалось после Update 2.0

На проверенном билде потребовалось исправить сразу несколько вещей:

1. старый `GUObjectArray` AOB больше не подходил;
2. встроенный `FName::ToString` scan выбирал плохой адрес;
3. PatternSleuth находил ложный `GMalloc`;
4. стандартный UE5.5 `[FMalloc]` vtable layout не совпадал с игрой;
5. `LoadMap` hook приводил к падению;
6. для стабильного дампа gameplay hooks были отключены.

Подробности: [`docs/TECHNICAL_NOTES.md`](docs/TECHNICAL_NOTES.md).

## Быстрая установка

### 1. Установить UE4SS

Использовалась сборка:

```text
UE4SS zDEV v3.0.1-1028-gd7e7826d
Git SHA d7e7826d
```

Рекомендуется начать именно с того же commit/build, потому что сигнатуры и
layout проверялись на нём.

### 2. Склонировать/распаковать этот репозиторий

### 3. Запустить установщик профиля

```powershell
python tools\install_dumper_profile.py "<путь_до_папки_с_игрой>\Stalker2\Binaries\Win64\ue4ss"
```

Скрипт:

- создаст `MemberVariableLayout.ini` из
  `MemberVariableLayout_5_05_Template.ini`, если файла ещё нет;
- создаст `VTableLayout.ini` из `VTableLayout_5_05_Template.ini`, если файла ещё нет;
- добавит три дополнительные позиции в `[FMalloc]`;
- установит:
  - `GUObjectArray.lua`
  - `FName_ToString.lua`
  - `GMalloc.lua`
- переведёт `UE4SS-settings.ini` в dump-only режим;
- создаст `.bak` для изменяемых файлов, если backup ещё не существует.

### 4. Отключить моды

Для первого стабильного запуска рекомендуется временно отключить все Lua/C++ моды.

В проверенной конфигурации gameplay hooks также выключены.

### 5. Запустить игру

После инициализации UE4SS открыть вкладку **Dumpers** и выполнить нужный dump.

## Что должно быть в логе

Критические строки:

```text
GMalloc address: ... <- Lua Script
FName::ToString address: ... <- Lua Script
GUObjectArray address: ... <- Lua Script
```

Для `FMalloc`:

```text
FMalloc::Malloc = 0x28
FMalloc::TryMalloc = 0x30
FMalloc::Realloc = 0x38
FMalloc::TryRealloc = 0x40
FMalloc::Free = 0x48
FMalloc::GetDescriptiveName = 0xC8
```

## Известные ограничения

Это dump-only профиль.

На проверенном билде остаются нерешёнными:

```text
GNatives not found
ProcessLocalScriptFunction is not available
```

Также `HookLoadMap=1` приводил к падению в `TDetourInstance::StaticHookFn`,
хотя сам адрес `UEngine::LoadMap` был подтверждён строковыми xref'ами.


## Файлы

```text
signatures/
  GUObjectArray.lua
  FName_ToString.lua
  GMalloc.lua

tools/
  install_dumper_profile.py
  inspect_gmalloc.py

docs/
  TECHNICAL_NOTES.md
  DUMPER7_STATUS.md
  TROUBLESHOOTING.md

examples/
  UE4SS-settings.dumper-only.ini.snippet
  FMalloc.expected-layout.txt
```

## Важно

Все AOB и RVA здесь относятся к проверенному **Update 2.0** executable.
После любого следующего патча их нужно перепроверять.

Не заменяйте адреса вслепую только потому, что сигнатура перестала находиться.
