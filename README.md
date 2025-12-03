# Python Manta

> **Python bindings for the [dotabuff/manta](https://github.com/dotabuff/manta) Dota 2 replay parser**

[![PyPI version](https://badge.fury.io/py/python-manta.svg)](https://pypi.org/project/python-manta/)
[![Documentation](https://img.shields.io/badge/docs-GitHub%20Pages-blue)](https://deepbluecoding.github.io/python-manta/)
[![Build Status](https://github.com/DeepBlueCoding/python-manta/actions/workflows/build-wheels.yml/badge.svg)](https://github.com/DeepBlueCoding/python-manta/actions/workflows/build-wheels.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

---

## What This Library Does

**Python Manta is a wrapper/bindings library** that provides Python access to the excellent [Manta](https://github.com/dotabuff/manta) Go library for parsing Dota 2 replay files (`.dem`).

### Important Attribution

**All the heavy lifting is done by [dotabuff/manta](https://github.com/dotabuff/manta)** - the battle-tested Go replay parser maintained by [Dotabuff](https://www.dotabuff.com). This Python library simply:

1. Wraps the Manta Go library using CGO
2. Exposes a Pythonic API via ctypes
3. Provides type-safe Pydantic models for parsed data

If you're working in Go, use [Manta](https://github.com/dotabuff/manta) directly. This library exists for Python developers who need replay parsing capabilities.

### Library Philosophy

Python Manta is a **low-level data extraction library**, not an analytics tool. We provide:

| ✅ In Scope | ❌ Out of Scope |
|-------------|-----------------|
| Raw data extraction | Analysis/aggregation logic |
| Enums/constants for game data (e.g., `RuneType`) | Fight detection algorithms |
| Type-safe Pydantic models | Statistics computation |
| Simple helper properties (e.g., `is_pro_match()`) | Data interpretation |

**The line**: If it's mapping/typing game data → library. If it's interpreting/analyzing → user code.

Users should build analysis logic on top of the raw data we provide.

---

## Table of Contents

- [Documentation](https://deepbluecoding.github.io/python-manta/) ← **Full docs with examples**
- [Versioning](#versioning)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [API Reference](#api-reference)
- [Game Events](#game-events)
- [Modifiers](#modifiers)
- [Entity Queries](#entity-queries)
- [String Tables](#string-tables)
- [Combat Log](#combat-log)
- [Parser Info](#parser-info)
- [Supported Callbacks (272 Total)](#supported-callbacks-272-total)
- [Data Models](#data-models)
- [Common Use Cases](#common-use-cases)
- [Development Setup](#development-setup)
- [Architecture](#architecture)
- [AI Integration Guide](#ai-integration-guide)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

---

## Versioning

Python Manta follows a **4-part versioning scheme** that tracks the upstream [dotabuff/manta](https://github.com/dotabuff/manta) version:

```
v{manta_major}.{manta_minor}.{manta_patch}.{python_manta_release}
```

| Version Part | Meaning |
|--------------|---------|
| `1.4.5` | Base dotabuff/manta version this release is built on |
| `.1`, `.2`, etc. | Python Manta release number for that manta version |

**Examples:**
- `v1.4.5` - Initial release based on manta v1.4.5
- `v1.4.5.1` - First update/bugfix release, still using manta v1.4.5
- `v1.4.5.2` - Second update, still using manta v1.4.5
- `v1.4.6` - New release when manta updates to v1.4.6

This scheme allows us to release updates (new features, bugfixes, documentation) without waiting for upstream manta releases (which happen ~twice per year).

---

## Installation

### From PyPI (Recommended)

```bash
pip install python-manta
```

Pre-built wheels are available for:
- Linux (x86_64)
- macOS (Intel and Apple Silicon)
- Windows (AMD64)

**No Go installation required** - wheels include pre-compiled binaries.

### From Source

See [Building from Source](#building-from-source) section below.

---

## Quick Start

### Parse Demo Header

```python
from python_manta import MantaParser

parser = MantaParser()
header = parser.parse_header("match.dem")

print(f"Map: {header.map_name}")
print(f"Server: {header.server_name}")
print(f"Build: {header.build_num}")
print(f"Network Protocol: {header.network_protocol}")
```

### Parse Specific Messages

```python
from python_manta import MantaParser

# Initialize parser
parser = MantaParser()

# Extract chat messages (limit to 100)
result = parser.parse_universal("match.dem", "CDOTAUserMsg_ChatMessage", 100)

if result.success:
    for msg in result.messages:
        print(f"[Tick {msg.tick}] Player {msg.data['source_player_id']}: {msg.data['message_text']}")
```

### Parse Draft (Picks & Bans)

```python
draft = parser.parse_game_info("match.dem")

for pick_ban in draft.picks_bans:
    action = "PICK" if pick_ban.is_pick else "BAN"
    team = "Radiant" if pick_ban.team == 2 else "Dire"
    print(f"{team} {action}: Hero ID {pick_ban.hero_id}")
```

---

## API Reference

### MantaParser Class

The main class for parsing Dota 2 replay files.

```python
class MantaParser:
    def __init__(self, library_path: Optional[str] = None)

    # Basic parsing
    def parse_header(self, demo_file_path: str) -> HeaderInfo
    def parse_game_info(self, demo_file_path: str) -> CDotaGameInfo
    def parse_universal(self, demo_file_path: str, message_filter: str = "", max_messages: int = 0) -> UniversalParseResult

    # Advanced features
    def parse_game_events(self, demo_file_path: str, ...) -> GameEventsResult
    def parse_modifiers(self, demo_file_path: str, ...) -> ModifiersResult
    def query_entities(self, demo_file_path: str, ...) -> EntitiesResult
    def get_string_tables(self, demo_file_path: str, ...) -> StringTablesResult
    def parse_combat_log(self, demo_file_path: str, ...) -> CombatLogResult
    def get_parser_info(self, demo_file_path: str) -> ParserInfo
```

#### Constructor

```python
parser = MantaParser()  # Uses bundled library
parser = MantaParser("/path/to/libmanta_wrapper.so")  # Custom library path
```

#### parse_header(demo_file_path: str) -> HeaderInfo

Parses the demo file header containing match metadata.

**Parameters:**
- `demo_file_path`: Path to the `.dem` replay file

**Returns:** `HeaderInfo` with match metadata

**Raises:**
- `FileNotFoundError`: If demo file doesn't exist
- `ValueError`: If parsing fails

#### parse_game_info(demo_file_path: str) -> CDotaGameInfo

Extracts draft phase information (picks and bans).

**Parameters:**
- `demo_file_path`: Path to the `.dem` replay file

**Returns:** `CDotaGameInfo` with picks/bans list

#### parse_universal(demo_file_path: str, message_filter: str = "", max_messages: int = 0) -> UniversalParseResult

Universal parser for any Manta callback/message type.

**Parameters:**
- `demo_file_path`: Path to the `.dem` replay file
- `message_filter`: Callback name filter (e.g., `"CDOTAUserMsg_ChatMessage"`)
- `max_messages`: Maximum messages to return (0 = unlimited)

**Returns:** `UniversalParseResult` with matched messages

---

## Game Events

Parse Source 1 legacy game events with typed field access:

```python
from python_manta import MantaParser

parser = MantaParser()

# Get all event type definitions
result = parser.parse_game_events("match.dem", max_events=0, capture_types=True)
print(f"Found {len(result.event_types)} event types")

# Parse specific events
result = parser.parse_game_events("match.dem", event_filter="dota_combatlog", max_events=100)
for event in result.events:
    print(f"[{event.tick}] {event.name}: {event.fields}")
```

---

## Modifiers

Track buffs, debuffs, and auras on units:

```python
parser = MantaParser()

# Get all modifiers
result = parser.parse_modifiers("match.dem", max_modifiers=100)
for mod in result.modifiers:
    print(f"[{mod.tick}] {mod.name} on entity {mod.parent}, duration={mod.duration}, stacks={mod.stack_count}")

# Filter for auras only
result = parser.parse_modifiers("match.dem", max_modifiers=100, auras_only=True)
```

---

## Entity Queries

Query entities by class name and extract properties:

```python
parser = MantaParser()

# Query hero entities
result = parser.query_entities("match.dem", class_filter="Hero", max_entities=10)
for entity in result.entities:
    print(f"{entity.class_name} (index={entity.index})")
    print(f"  Health: {entity.properties.get('m_iHealth')}")

# Query specific properties only
result = parser.query_entities(
    "match.dem",
    class_filter="Hero",
    property_filter=["m_iHealth", "m_iMaxHealth", "m_vecOrigin"],
    max_entities=10
)

# Query by exact class names
result = parser.query_entities(
    "match.dem",
    class_names=["CDOTA_Unit_Hero_Invoker", "CDOTA_Unit_Hero_Pudge"],
    max_entities=20
)
```

---

## String Tables

Extract string tables (userinfo, instancebaseline, etc.):

```python
parser = MantaParser()

# Get all string tables
result = parser.get_string_tables("match.dem")
print(f"Tables: {result.table_names}")

# Get specific table
result = parser.get_string_tables("match.dem", table_names=["userinfo"], max_entries=50)
for entry in result.entries:
    print(f"[{entry.table}] {entry.key}: {entry.value[:50]}...")
```

---

## Combat Log

Parse combat log with filtering and typed entries:

```python
parser = MantaParser()

# Get all combat log entries
result = parser.parse_combat_log("match.dem", max_entries=100)
for entry in result.entries:
    print(f"[{entry.timestamp:.1f}s] {entry.type_name}: {entry.attacker_name} -> {entry.target_name}")

# Filter by type (0=DAMAGE, 1=HEAL, 2=MODIFIER_ADD, etc.)
result = parser.parse_combat_log("match.dem", types=[0], max_entries=100)  # Damage only

# Filter for hero-related entries
result = parser.parse_combat_log("match.dem", heroes_only=True, max_entries=100)
```

---

## Parser Info

Get parser metadata and state:

```python
parser = MantaParser()

info = parser.get_parser_info("match.dem")
print(f"Final tick: {info.tick}")
print(f"Entity count: {info.entity_count}")
print(f"String tables: {info.string_tables}")
```

---

## Supported Callbacks (272 Total)

Python Manta implements **all 272 Manta callbacks**. Use these exact names with `parse_universal()`.

### Communication & Chat

| Callback Name | Description |
|---------------|-------------|
| `CDOTAUserMsg_ChatMessage` | Player text chat messages |
| `CDOTAUserMsg_ChatEvent` | System chat events (kills, items, etc.) |
| `CDOTAUserMsg_ChatWheel` | Chat wheel phrases |
| `CDOTAUserMsg_BotChat` | Bot chat messages |
| `CUserMessageSayText` | Generic say text |
| `CUserMessageSayText2` | Extended say text |

### Map & Location

| Callback Name | Description |
|---------------|-------------|
| `CDOTAUserMsg_LocationPing` | Map ping locations |
| `CDOTAUserMsg_MapLine` | Map drawing/lines |
| `CDOTAUserMsg_WorldLine` | World-space lines |
| `CDOTAUserMsg_MinimapEvent` | Minimap events |
| `CDOTAUserMsg_Ping` | Generic pings |
| `CDOTAUserMsg_CoachHUDPing` | Coach pings |

### Game State & Events

| Callback Name | Description |
|---------------|-------------|
| `CDemoFileHeader` | Demo file metadata |
| `CDemoFileInfo` | Extended demo info (draft, players) |
| `CDOTAUserMsg_GamerulesStateChanged` | Game state transitions |
| `CDOTAUserMsg_OverheadEvent` | Damage numbers, XP, gold |
| `CDOTAUserMsg_UnitEvent` | Unit actions and abilities |
| `CMsgDOTACombatLogEntry` | Combat log entries |

### Draft & Hero Selection

| Callback Name | Description |
|---------------|-------------|
| `CDOTAUserMsg_PlayerDraftPick` | Player draft picks |
| `CDOTAUserMsg_PlayerDraftSuggestPick` | Draft suggestions |
| `CDOTAUserMsg_SuggestHeroPick` | Hero suggestions |
| `CDOTAUserMsg_SuggestHeroRole` | Role suggestions |

### Items & Economy

| Callback Name | Description |
|---------------|-------------|
| `CDOTAUserMsg_ItemPurchased` | Item purchases |
| `CDOTAUserMsg_ItemSold` | Item sales |
| `CDOTAUserMsg_ItemAlert` | Item alerts |
| `CDOTAUserMsg_ItemFound` | Found items |
| `CDOTAUserMsg_FoundNeutralItem` | Neutral item drops |
| `CDOTAUserMsg_QuickBuyAlert` | Quick buy alerts |

### Combat & Abilities

| Callback Name | Description |
|---------------|-------------|
| `CDOTAUserMsg_AbilityPing` | Ability pings |
| `CDOTAUserMsg_AbilitySteal` | Rubick spell steal |
| `CDOTAUserMsg_DamageReport` | Damage reports |
| `CDOTAUserMsg_TE_Projectile` | Projectile events |
| `CDOTAUserMsg_CreateLinearProjectile` | Linear projectiles |

### Network & Technical

| Callback Name | Description |
|---------------|-------------|
| `CNETMsg_Tick` | Network tick synchronization |
| `CNETMsg_SetConVar` | Console variable changes |
| `CNETMsg_SignonState` | Connection state changes |
| `CSVCMsg_ServerInfo` | Server configuration |
| `CSVCMsg_PacketEntities` | Entity updates |

### Demo Control

| Callback Name | Description |
|---------------|-------------|
| `CDemoPacket` | Demo packets |
| `CDemoStop` | Demo end marker |
| `CDemoSyncTick` | Sync tick markers |
| `CDemoStringTables` | String table data |
| `CDemoClassInfo` | Class information |

### Full Callback List by Category

<details>
<summary><strong>Demo Messages (15 callbacks)</strong></summary>

- `CDemoAnimationData`
- `CDemoAnimationHeader`
- `CDemoClassInfo`
- `CDemoConsoleCmd`
- `CDemoCustomData`
- `CDemoCustomDataCallbacks`
- `CDemoFileHeader`
- `CDemoFileInfo`
- `CDemoFullPacket`
- `CDemoPacket`
- `CDemoRecovery`
- `CDemoSaveGame`
- `CDemoSendTables`
- `CDemoSpawnGroups`
- `CDemoStop`
- `CDemoStringTables`
- `CDemoSyncTick`
- `CDemoUserCmd`

</details>

<details>
<summary><strong>Network Messages (15 callbacks)</strong></summary>

- `CNETMsg_DebugOverlay`
- `CNETMsg_NOP`
- `CNETMsg_SetConVar`
- `CNETMsg_SignonState`
- `CNETMsg_SpawnGroup_Load`
- `CNETMsg_SpawnGroup_LoadCompleted`
- `CNETMsg_SpawnGroup_ManifestUpdate`
- `CNETMsg_SpawnGroup_SetCreationTick`
- `CNETMsg_SpawnGroup_Unload`
- `CNETMsg_SplitScreenUser`
- `CNETMsg_StringCmd`
- `CNETMsg_Tick`

</details>

<details>
<summary><strong>SVC Messages (25 callbacks)</strong></summary>

- `CSVCMsg_BSPDecal`
- `CSVCMsg_Broadcast_Command`
- `CSVCMsg_ClassInfo`
- `CSVCMsg_ClearAllStringTables`
- `CSVCMsg_CmdKeyValues`
- `CSVCMsg_CreateStringTable`
- `CSVCMsg_FlattenedSerializer`
- `CSVCMsg_FullFrameSplit`
- `CSVCMsg_GetCvarValue`
- `CSVCMsg_HLTVStatus`
- `CSVCMsg_HltvFixupOperatorStatus`
- `CSVCMsg_Menu`
- `CSVCMsg_PacketEntities`
- `CSVCMsg_PacketReliable`
- `CSVCMsg_PeerList`
- `CSVCMsg_Prefetch`
- `CSVCMsg_Print`
- `CSVCMsg_RconServerDetails`
- `CSVCMsg_ServerInfo`
- `CSVCMsg_ServerSteamID`
- `CSVCMsg_SetPause`
- `CSVCMsg_SetView`
- `CSVCMsg_Sounds`
- `CSVCMsg_SplitScreen`
- `CSVCMsg_StopSound`
- `CSVCMsg_UpdateStringTable`
- `CSVCMsg_UserMessage`
- `CSVCMsg_VoiceData`
- `CSVCMsg_VoiceInit`

</details>

<details>
<summary><strong>User Messages (35 callbacks)</strong></summary>

- `CUserMessageAchievementEvent`
- `CUserMessageAmmoDenied`
- `CUserMessageAudioParameter`
- `CUserMessageCameraTransition`
- `CUserMessageCloseCaption`
- `CUserMessageCloseCaptionDirect`
- `CUserMessageCloseCaptionPlaceholder`
- `CUserMessageColoredText`
- `CUserMessageCreditsMsg`
- `CUserMessageCurrentTimescale`
- `CUserMessageDesiredTimescale`
- `CUserMessageFade`
- `CUserMessageGameTitle`
- `CUserMessageHapticsManagerEffect`
- `CUserMessageHapticsManagerPulse`
- `CUserMessageHudMsg`
- `CUserMessageHudText`
- `CUserMessageItemPickup`
- `CUserMessageLagCompensationError`
- `CUserMessageRequestDiagnostic`
- `CUserMessageRequestDllStatus`
- `CUserMessageRequestInventory`
- `CUserMessageRequestState`
- `CUserMessageRequestUtilAction`
- `CUserMessageResetHUD`
- `CUserMessageRumble`
- `CUserMessageSayText`
- `CUserMessageSayText2`
- `CUserMessageSayTextChannel`
- `CUserMessageSendAudio`
- `CUserMessageServerFrameTime`
- `CUserMessageShake`
- `CUserMessageShakeDir`
- `CUserMessageShowMenu`
- `CUserMessageTextMsg`
- `CUserMessageScreenTilt`
- `CUserMessageUpdateCssClasses`
- `CUserMessageVoiceMask`
- `CUserMessageWaterShake`

</details>

<details>
<summary><strong>DOTA User Messages (140+ callbacks)</strong></summary>

- `CDOTAUserMsg_AbilityDraftRequestAbility`
- `CDOTAUserMsg_AbilityPing`
- `CDOTAUserMsg_AbilitySteal`
- `CDOTAUserMsg_AddQuestLogEntry`
- `CDOTAUserMsg_AghsStatusAlert`
- `CDOTAUserMsg_AIDebugLine`
- `CDOTAUserMsg_AllStarEvent`
- `CDOTAUserMsg_BeastChat`
- `CDOTAUserMsg_BoosterState`
- `CDOTAUserMsg_BotChat`
- `CDOTAUserMsg_BuyBackStateAlert`
- `CDOTAUserMsg_ChatEvent`
- `CDOTAUserMsg_ChatMessage`
- `CDOTAUserMsg_ChatWheel`
- `CDOTAUserMsg_ChatWheelCooldown`
- `CDOTAUserMsg_ClientLoadGridNav`
- `CDOTAUserMsg_CoachHUDPing`
- `CDOTAUserMsg_CombatHeroPositions`
- `CDOTAUserMsg_CombatLogBulkData`
- `CDOTAUserMsg_CompendiumState`
- `CDOTAUserMsg_ContextualTip`
- `CDOTAUserMsg_CourierKilledAlert`
- `CDOTAUserMsg_CreateLinearProjectile`
- `CDOTAUserMsg_CustomHeaderMessage`
- `CDOTAUserMsg_CustomHudElement_Create`
- `CDOTAUserMsg_CustomHudElement_Destroy`
- `CDOTAUserMsg_CustomHudElement_Modify`
- `CDOTAUserMsg_CustomMsg`
- `CDOTAUserMsg_DamageReport`
- `CDOTAUserMsg_DebugChallenge`
- `CDOTAUserMsg_DestroyLinearProjectile`
- `CDOTAUserMsg_DismissAllStatPopups`
- `CDOTAUserMsg_DodgeTrackingProjectiles`
- `CDOTAUserMsg_DuelAccepted`
- `CDOTAUserMsg_DuelOpponentKilled`
- `CDOTAUserMsg_DuelRequested`
- `CDOTAUserMsg_EmptyItemSlotAlert`
- `CDOTAUserMsg_EmptyTeleportAlert`
- `CDOTAUserMsg_EnemyItemAlert`
- `CDOTAUserMsg_ESArcanaCombo`
- `CDOTAUserMsg_ESArcanaComboSummary`
- `CDOTAUserMsg_FacetPing`
- `CDOTAUserMsg_FlipCoinResult`
- `CDOTAUserMsg_FoundNeutralItem`
- `CDOTAUserMsg_GamerulesStateChanged`
- `CDOTAUserMsg_GiftPlayer`
- `CDOTAUserMsg_GlobalLightColor`
- `CDOTAUserMsg_GlobalLightDirection`
- `CDOTAUserMsg_GlyphAlert`
- `CDOTAUserMsg_GuildChallenge_Progress`
- `CDOTAUserMsg_HalloweenDrops`
- `CDOTAUserMsg_HeroRelicProgress`
- `CDOTAUserMsg_HighFiveCompleted`
- `CDOTAUserMsg_HighFiveLeftHanging`
- `CDOTAUserMsg_HotPotato_Created`
- `CDOTAUserMsg_HotPotato_Exploded`
- `CDOTAUserMsg_HPManaAlert`
- `CDOTAUserMsg_HudError`
- `CDOTAUserMsg_InnatePing`
- `CDOTAUserMsg_InvalidCommand`
- `CDOTAUserMsg_ItemAlert`
- `CDOTAUserMsg_ItemFound`
- `CDOTAUserMsg_ItemPurchased`
- `CDOTAUserMsg_ItemSold`
- `CDOTAUserMsg_KillcamDamageTaken`
- `CDOTAUserMsg_LocationPing`
- `CDOTAUserMsg_MadstoneAlert`
- `CDOTAUserMsg_MapLine`
- `CDOTAUserMsg_MarsArenaOfBloodAttack`
- `CDOTAUserMsg_MinimapDebugPoint`
- `CDOTAUserMsg_MinimapEvent`
- `CDOTAUserMsg_MiniKillCamInfo`
- `CDOTAUserMsg_MiniTaunt`
- `CDOTAUserMsg_ModifierAlert`
- `CDOTAUserMsg_MoveCameraToUnit`
- `CDOTAUserMsg_MuertaReleaseEvent_AssignedTargetKilled`
- `CDOTAUserMsg_MutedPlayers`
- `CDOTAUserMsg_NeutralCampAlert`
- `CDOTAUserMsg_NeutralCraftAvailable`
- `CDOTAUserMsg_NevermoreRequiem`
- `CDOTAUserMsg_OMArcanaCombo`
- `CDOTAUserMsg_OutpostCaptured`
- `CDOTAUserMsg_OutpostGrantedXP`
- `CDOTAUserMsg_OverheadEvent`
- `CDOTAUserMsg_PauseMinigameData`
- `CDOTAUserMsg_Ping`
- `CDOTAUserMsg_PingConfirmation`
- `CDOTAUserMsg_PlayerDraftPick`
- `CDOTAUserMsg_PlayerDraftSuggestPick`
- `CDOTAUserMsg_ProjectionAbility`
- `CDOTAUserMsg_ProjectionEvent`
- `CDOTAUserMsg_QoP_ArcanaSummary`
- `CDOTAUserMsg_QuestStatus`
- `CDOTAUserMsg_QueuedOrderRemoved`
- `CDOTAUserMsg_QuickBuyAlert`
- `CDOTAUserMsg_RadarAlert`
- `CDOTAUserMsg_ReceivedXmasGift`
- `CDOTAUserMsg_ReplaceQueryUnit`
- `CDOTAUserMsg_RockPaperScissorsFinished`
- `CDOTAUserMsg_RockPaperScissorsStarted`
- `CDOTAUserMsg_RollDiceResult`
- `CDOTAUserMsg_RoshanTimer`
- `CDOTAUserMsg_SalutePlayer`
- `CDOTAUserMsg_SelectPenaltyGold`
- `CDOTAUserMsg_SendFinalGold`
- `CDOTAUserMsg_SendGenericToolTip`
- `CDOTAUserMsg_SendRoshanPopup`
- `CDOTAUserMsg_SendRoshanSpectatorPhase`
- `CDOTAUserMsg_SendStatPopup`
- `CDOTAUserMsg_SetNextAutobuyItem`
- `CDOTAUserMsg_SharedCooldown`
- `CDOTAUserMsg_ShovelUnearth`
- `CDOTAUserMsg_ShowGenericPopup`
- `CDOTAUserMsg_ShowSurvey`
- `CDOTAUserMsg_SpectatorPlayerClick`
- `CDOTAUserMsg_SpectatorPlayerUnitOrders`
- `CDOTAUserMsg_SpeechBubble`
- `CDOTAUserMsg_StatsHeroMinuteDetails`
- `CDOTAUserMsg_StatsMatchDetails`
- `CDOTAUserMsg_SuggestHeroPick`
- `CDOTAUserMsg_SuggestHeroRole`
- `CDOTAUserMsg_SwapVerify`
- `CDOTAUserMsg_TalentTreeAlert`
- `CDOTAUserMsg_TE_DestroyProjectile`
- `CDOTAUserMsg_TE_DotaBloodImpact`
- `CDOTAUserMsg_TE_Projectile`
- `CDOTAUserMsg_TE_ProjectileLoc`
- `CDOTAUserMsg_TE_UnitAnimation`
- `CDOTAUserMsg_TE_UnitAnimationEnd`
- `CDOTAUserMsg_TimerAlert`
- `CDOTAUserMsg_TipAlert`
- `CDOTAUserMsg_TutorialFade`
- `CDOTAUserMsg_TutorialFinish`
- `CDOTAUserMsg_TutorialMinimapPosition`
- `CDOTAUserMsg_TutorialPingMinimap`
- `CDOTAUserMsg_TutorialRequestExp`
- `CDOTAUserMsg_TutorialTipInfo`
- `CDOTAUserMsg_UnitEvent`
- `CDOTAUserMsg_UpdateLinearProjectileCPData`
- `CDOTAUserMsg_UpdateQuestProgress`
- `CDOTAUserMsg_UpdateSharedContent`
- `CDOTAUserMsg_VersusScene_PlayerBehavior`
- `CDOTAUserMsg_VoteEnd`
- `CDOTAUserMsg_VoteStart`
- `CDOTAUserMsg_VoteUpdate`
- `CDOTAUserMsg_WillPurchaseAlert`
- `CDOTAUserMsg_WK_Arcana_Progress`
- `CDOTAUserMsg_WorldLine`
- `CDOTAUserMsg_WRArcanaProgress`
- `CDOTAUserMsg_WRArcanaSummary`
- `CDOTAUserMsg_XPAlert`

</details>

<details>
<summary><strong>Entity Messages (6 callbacks)</strong></summary>

- `CEntityMessageDoSpark`
- `CEntityMessageFixAngle`
- `CEntityMessagePlayJingle`
- `CEntityMessagePropagateForce`
- `CEntityMessageRemoveAllDecals`
- `CEntityMessageScreenOverlay`

</details>

<details>
<summary><strong>Miscellaneous Messages (15 callbacks)</strong></summary>

- `CMsgClearDecalsForSkeletonInstanceEvent`
- `CMsgClearEntityDecalsEvent`
- `CMsgClearWorldDecalsEvent`
- `CMsgDOTACombatLogEntry`
- `CMsgGCToClientTournamentItemDrop`
- `CMsgPlaceDecalEvent`
- `CMsgSosSetLibraryStackFields`
- `CMsgSosSetSoundEventParams`
- `CMsgSosStartSoundEvent`
- `CMsgSosStopSoundEvent`
- `CMsgSosStopSoundEventHash`
- `CMsgSource1LegacyGameEvent`
- `CMsgSource1LegacyGameEventList`
- `CMsgSource1LegacyListenEvents`
- `CMsgVDebugGameSessionIDEvent`
- `CDOTAMatchMetadataFile`

</details>

---

## Data Models

All models use [Pydantic](https://docs.pydantic.dev/) for validation and serialization.

### HeaderInfo

```python
class HeaderInfo(BaseModel):
    map_name: str              # Map name (e.g., "dota")
    server_name: str           # Server identifier
    client_name: str           # Client type
    game_directory: str        # Game directory path
    network_protocol: int      # Network protocol version
    demo_file_stamp: str       # Demo file signature
    build_num: int             # Game build number
    game: str                  # Game identifier
    server_start_tick: int     # Server start tick
    success: bool              # Parse success flag
    error: Optional[str]       # Error message if failed
```

### CHeroSelectEvent

```python
class CHeroSelectEvent(BaseModel):
    is_pick: bool    # True for pick, False for ban
    team: int        # 2 = Radiant, 3 = Dire
    hero_id: int     # Hero ID (see Dota 2 Wiki for mappings)
```

### CDotaGameInfo

```python
class CDotaGameInfo(BaseModel):
    picks_bans: List[CHeroSelectEvent]  # Draft sequence
    success: bool
    error: Optional[str]
```

### MessageEvent

```python
class MessageEvent(BaseModel):
    type: str                    # Callback name
    tick: int                    # Game tick
    net_tick: int                # Network tick
    data: Any                    # Message-specific data (dict)
    timestamp: Optional[int]     # Unix timestamp (ms)
```

### UniversalParseResult

```python
class UniversalParseResult(BaseModel):
    messages: List[MessageEvent]  # Matched messages
    success: bool                 # Parse success flag
    error: Optional[str]          # Error message
    count: int                    # Number of messages
```

### GameEventData

```python
class GameEventData(BaseModel):
    name: str                     # Event name (e.g., "dota_combatlog")
    tick: int                     # Game tick
    net_tick: int                 # Network tick
    fields: Dict[str, Any]        # Event-specific fields
```

### ModifierEntry

```python
class ModifierEntry(BaseModel):
    tick: int                     # Game tick
    name: str                     # Modifier name
    parent: int                   # Parent entity handle
    duration: float               # Duration in seconds (-1 = permanent)
    stack_count: int              # Number of stacks
    is_aura: bool                 # Whether this is an aura
```

### EntityData

```python
class EntityData(BaseModel):
    index: int                    # Entity index
    class_name: str               # Entity class name
    properties: Dict[str, Any]    # Entity properties
```

### CombatLogEntry

```python
class CombatLogEntry(BaseModel):
    tick: int                     # Game tick
    type: int                     # Combat log type ID
    type_name: str                # Human-readable type name
    attacker_name: str            # Attacker name
    target_name: str              # Target name
    inflictor_name: str           # Ability/item name
    value: int                    # Damage/heal value
    health: int                   # Target HP after event
    timestamp: float              # Game time in seconds
    is_attacker_hero: bool        # Whether attacker is a hero
    is_target_hero: bool          # Whether target is a hero
    stun_duration: float          # Stun duration applied
    assist_players: List[int]     # Assist player IDs (for kills)
    # ... 80+ fields total - see documentation for complete list
```

### ParserInfo

```python
class ParserInfo(BaseModel):
    tick: int                     # Final parser tick
    net_tick: int                 # Final network tick
    entity_count: int             # Number of entities
    string_tables: List[str]      # List of string table names
    success: bool                 # Parse success flag
```

---

## Common Use Cases

### Extract All Chat Messages

```python
from python_manta import MantaParser

parser = MantaParser()
result = parser.parse_universal("match.dem", "CDOTAUserMsg_ChatMessage", 0)

for msg in result.messages:
    player_id = msg.data.get('source_player_id', 'Unknown')
    text = msg.data.get('message_text', '')
    print(f"Player {player_id}: {text}")
```

### Track Item Purchases

```python
from python_manta import MantaParser

parser = MantaParser()
result = parser.parse_universal("match.dem", "CDOTAUserMsg_ItemPurchased", 0)

for msg in result.messages:
    player_id = msg.data.get('player_id')
    item_id = msg.data.get('item_ability_id')
    tick = msg.tick
    print(f"[{tick}] Player {player_id} purchased item {item_id}")
```

### Analyze Location Pings

```python
from python_manta import MantaParser

parser = MantaParser()
result = parser.parse_universal("match.dem", "CDOTAUserMsg_LocationPing", 0)

for msg in result.messages:
    ping_data = msg.data.get('location_ping', {})
    x = ping_data.get('x', 0)
    y = ping_data.get('y', 0)
    player_id = msg.data.get('player_id')
    print(f"Player {player_id} pinged at ({x}, {y})")
```

### Extract Combat Log

```python
from python_manta import MantaParser

parser = MantaParser()
result = parser.parse_universal("match.dem", "CMsgDOTACombatLogEntry", 1000)

for msg in result.messages:
    entry = msg.data
    # Combat log entries contain damage, healing, XP, gold, etc.
    print(f"[{msg.tick}] Combat event: {entry}")
```

### Get Match Statistics

```python
from python_manta import MantaParser

parser = MantaParser()

# Get stats details
result = parser.parse_universal("match.dem", "CDOTAUserMsg_StatsMatchDetails", 10)

if result.success and result.messages:
    stats = result.messages[0].data
    print(f"Match stats: {stats}")
```

### Multiple Message Types

```python
from python_manta import MantaParser

parser = MantaParser()

# Parse multiple message types
message_types = [
    ("CDOTAUserMsg_ChatMessage", 100),
    ("CDOTAUserMsg_LocationPing", 50),
    ("CDOTAUserMsg_ItemPurchased", 200),
]

for msg_type, limit in message_types:
    result = parser.parse_universal("match.dem", msg_type, limit)
    print(f"{msg_type}: {result.count} messages")
```

---

## Development Setup

When you clone this repository, the shared library (`.so`/`.dylib`/`.dll`) is not included. You have two options:

### Option 1: Download Pre-built Library (Recommended)

```bash
git clone https://github.com/DeepBlueCoding/python-manta.git
cd python-manta
python scripts/download_library.py
pip install -e '.[dev]'
```

### Option 2: Build from Source

Requires Go 1.19+ installed.

```bash
git clone https://github.com/DeepBlueCoding/python-manta.git
cd python-manta
git clone https://github.com/dotabuff/manta.git ../manta
./build.sh
pip install -e '.[dev]'
```

### Verify Installation

```bash
python -c "from python_manta import MantaParser; print('Success!')"
```

### Running Tests

```bash
# Unit tests only
python run_tests.py --unit

# Integration tests (requires .dem files)
python run_tests.py --integration

# All tests with coverage
python run_tests.py --all --coverage
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Python Application                      │
├─────────────────────────────────────────────────────────────┤
│  python_manta Package                                        │
│  ├── MantaParser (main interface)                           │
│  ├── Pydantic Models (type-safe data structures)            │
│  └── ctypes bindings (FFI to shared library)                │
├─────────────────────────────────────────────────────────────┤
│  libmanta_wrapper.so (CGO Shared Library)                   │
│  ├── CGO exports (ParseHeader, ParseDraft, ParseUniversal)  │
│  ├── 272 callback implementations                           │
│  └── JSON serialization                                      │
├─────────────────────────────────────────────────────────────┤
│  dotabuff/manta (Go Library)                                │
│  ├── PBDEMS2 format parser                                  │
│  ├── Protobuf message decoding                              │
│  └── Callback system                                         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │  .dem Replay    │
                    │     File        │
                    └─────────────────┘
```

### Data Flow

1. Python calls `parse_universal()` with demo path and filter
2. ctypes marshals parameters to C strings
3. CGO wrapper receives call, opens file
4. Manta Go library parses the binary .dem file
5. Registered callbacks capture matching messages
6. Messages serialized to JSON
7. JSON returned to Python via ctypes
8. Pydantic models validate and structure the data

---

## AI Integration Guide

This section helps AI systems (LLMs, agents, coding assistants) understand and use this library effectively.

### Library Philosophy (Important for AI Agents)

Python Manta is a **low-level data extraction library**, not an analytics tool.

| ✅ In Scope | ❌ Out of Scope |
|-------------|-----------------|
| Raw data extraction | Analysis/aggregation logic |
| Enums/constants (e.g., `RuneType`) | Fight detection algorithms |
| Type-safe Pydantic models | Statistics computation |
| Helper properties (e.g., `is_pro_match()`) | Data interpretation |

**When generating code**: Extract raw data with this library, then write analysis logic separately. Don't expect high-level functions like "get_teamfights()" or "calculate_gpm()" - those belong in user code.

### Quick Reference

```python
from python_manta import MantaParser

parser = MantaParser()

# Basic parsing
header = parser.parse_header("match.dem")           # Match metadata
draft = parser.parse_game_info("match.dem")             # Picks and bans
match = parser.parse_game_info("match.dem")        # Pro match data (teams, league)
result = parser.parse_universal("match.dem", "CDOTAUserMsg_ChatMessage", 100)

# Hero positions over time
entities = parser.parse_entities("match.dem", interval_ticks=900, max_snapshots=100)

# Advanced features
events = parser.parse_game_events("match.dem", event_filter="dota_combatlog", max_events=100)
modifiers = parser.parse_modifiers("match.dem", max_modifiers=100)
hero_state = parser.query_entities("match.dem", class_filter="Hero", max_entities=10)
combat = parser.parse_combat_log("match.dem", heroes_only=True, max_entries=100)
info = parser.get_parser_info("match.dem")
```

### Which API to Use

| Task | Method | Notes |
|------|--------|-------|
| Match metadata | `parse_header()` | Build number, map, server |
| Draft sequence | `parse_game_info()` | Picks/bans with hero IDs |
| Pro match info | `parse_game_info()` | Teams, league, players, winner |
| Hero positions over time | `parse_entities()` | Position, stats at intervals |
| Chat messages | `parse_universal("CDOTAUserMsg_ChatMessage")` | Player text chat |
| Item purchases | `parse_universal("CDOTAUserMsg_ItemPurchased")` | Item buy events |
| Map pings | `parse_universal("CDOTAUserMsg_LocationPing")` | Ping coordinates |
| Combat damage | `parse_combat_log(types=[0])` | Structured damage events |
| Hero kills | `parse_combat_log(heroes_only=True)` | Hero-related combat |
| Buff tracking | `parse_modifiers()` | Active buffs/debuffs |
| Hero state (end) | `query_entities(class_filter="Hero")` | Entity state at end of replay |
| Game events | `parse_game_events()` | 364 named event types |
| Player info | `get_string_tables(table_names=["userinfo"])` | Steam IDs, names |

### Common Patterns

**Extract hero stats at end of game:**
```python
result = parser.query_entities("match.dem", class_filter="Hero", max_entities=10)
for hero in result.entities:
    health = hero.properties.get("m_iHealth", 0)
    max_health = hero.properties.get("m_iMaxHealth", 0)
    print(f"{hero.class_name}: {health}/{max_health} HP")
```

**Track all damage to heroes:**
```python
result = parser.parse_combat_log("match.dem", types=[0], heroes_only=True, max_entries=1000)
for entry in result.entries:
    print(f"{entry.attacker_name} hit {entry.target_name} for {entry.value} damage")
```

**Find specific game events:**
```python
result = parser.parse_game_events("match.dem", event_filter="dota_player_kill", max_events=100)
for event in result.events:
    print(f"Kill at tick {event.tick}: {event.fields}")
```

### Key Constraints

1. **Callback names are case-sensitive** - Use exact names from the callback list
2. **Message filter uses substring matching** - `"Chat"` matches `CDOTAUserMsg_ChatMessage` and `CDOTAUserMsg_ChatEvent`
3. **Always set `max_*` limits** - Prevents memory issues with large replays
4. **Entity queries return end-of-replay state** - For time-series data, use combat log or game events
5. **Combat log only starts after ~12-17 minutes** - HLTV broadcast delay; use entity snapshots for early game

---

## Troubleshooting

### Library Not Found

```
FileNotFoundError: Shared library not found
```

**Solution:** Install from PyPI (`pip install python-manta`) or build from source with `./build.sh`.

### Demo File Not Found

```
FileNotFoundError: Demo file not found: match.dem
```

**Solution:** Provide absolute path or verify the file exists.

### Parsing Returns Empty Results

1. Check the callback name is exact (case-sensitive)
2. The message type may not exist in that replay
3. Try without a filter to see all messages: `parser.parse_universal("match.dem", "", 100)`

### Memory Issues with Large Replays

**Solution:** Always set `max_messages` to a reasonable limit:
```python
# Good - limits memory usage
result = parser.parse_universal("match.dem", "CNETMsg_Tick", 1000)

# Bad - could consume gigabytes of RAM
result = parser.parse_universal("match.dem", "CNETMsg_Tick", 0)
```

### Platform-Specific Issues

**macOS Apple Silicon:**
- Ensure you have the ARM64 wheel or build from source on ARM

**Windows:**
- The library file is `libmanta_wrapper.dll`
- Ensure Visual C++ redistributables are installed

**Linux:**
- The library file is `libmanta_wrapper.so`
- Ensure `glibc` version compatibility

---

## Project Links

- **GitHub:** https://github.com/DeepBlueCoding/python-manta
- **Documentation:** https://deepbluecoding.github.io/python-manta/
- **PyPI:** https://pypi.org/project/python-manta/
- **Original Manta (Go):** https://github.com/dotabuff/manta
- **Dotabuff:** https://www.dotabuff.com

### Related Projects

- [clarity](https://github.com/skadistats/clarity) - Java Dota 2 replay parser
- [demoinfo-go](https://github.com/markus-wa/demoinfocs-golang) - CS:GO demo parser in Go
- [Yasha](https://github.com/dotabuff/yasha) - Source 1 Dota 2 parser (archived)

---

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `python run_tests.py --all`
5. Submit a pull request

---

## License

MIT License - see [LICENSE](LICENSE) file.

---

## Acknowledgments

- **[Manta](https://github.com/dotabuff/manta)** - The Go replay parser that does all the real work
- **[Dotabuff](https://www.dotabuff.com)** - For maintaining Manta and supporting the community
- **Valve Corporation** - For Dota 2 and the replay format
