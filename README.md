# Python Manta

> **Python bindings for the [dotabuff/manta](https://github.com/dotabuff/manta) Dota 2 replay parser**

[![PyPI version](https://badge.fury.io/py/python-manta.svg)](https://pypi.org/project/python-manta/)
[![Build Status](https://github.com/equilibrium-coach/python-manta/actions/workflows/ci.yml/badge.svg)](https://github.com/equilibrium-coach/python-manta/actions)
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

---

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [API Reference](#api-reference)
- [Supported Callbacks (272 Total)](#supported-callbacks-272-total)
- [Data Models](#data-models)
- [Common Use Cases](#common-use-cases)
- [Building from Source](#building-from-source)
- [Architecture](#architecture)
- [AI Integration Guide](#ai-integration-guide)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

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
from python_manta import parse_demo_header

# Parse header metadata
header = parse_demo_header("match.dem")

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
from python_manta import parse_demo_draft

# Get draft information
draft = parse_demo_draft("match.dem")

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
    def parse_header(self, demo_file_path: str) -> HeaderInfo
    def parse_draft(self, demo_file_path: str) -> CDotaGameInfo
    def parse_universal(self, demo_file_path: str, message_filter: str = "", max_messages: int = 0) -> UniversalParseResult
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

#### parse_draft(demo_file_path: str) -> CDotaGameInfo

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

### Convenience Functions

```python
# Quick header parsing
header = parse_demo_header("match.dem")

# Quick draft parsing
draft = parse_demo_draft("match.dem")

# Quick universal parsing
result = parse_demo_universal("match.dem", "CDOTAUserMsg_ChatMessage", 50)
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

## Building from Source

### Prerequisites

- **Python 3.8+**
- **Go 1.19+**
- **Git**

### Steps

1. **Clone the repository:**
   ```bash
   git clone https://github.com/equilibrium-coach/python-manta.git
   cd python-manta
   ```

2. **Clone the Manta dependency:**
   ```bash
   # From the project root
   git clone https://github.com/dotabuff/manta.git ../manta
   ```

3. **Build the CGO library:**
   ```bash
   ./build.sh
   ```

4. **Install the Python package:**
   ```bash
   pip install -e '.[dev]'
   ```

5. **Verify installation:**
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

### Quick Reference for AI

```python
# IMPORT
from python_manta import MantaParser, parse_demo_header, parse_demo_draft

# INITIALIZE
parser = MantaParser()  # Uses bundled library automatically

# PARSE HEADER (metadata)
header = parse_demo_header("path/to/match.dem")
# Returns: HeaderInfo with map_name, build_num, server_name, etc.

# PARSE DRAFT (picks/bans)
draft = parse_demo_draft("path/to/match.dem")
# Returns: CDotaGameInfo with picks_bans list

# PARSE ANY MESSAGE TYPE
result = parser.parse_universal(
    "path/to/match.dem",     # Demo file path
    "CDOTAUserMsg_ChatMessage",  # Exact callback name (case-sensitive)
    100                       # Max messages (0 = unlimited)
)
# Returns: UniversalParseResult with messages list
```

### Common Callback Names for AI

| Use Case | Callback Name |
|----------|---------------|
| Player chat | `CDOTAUserMsg_ChatMessage` |
| Map pings | `CDOTAUserMsg_LocationPing` |
| Item purchases | `CDOTAUserMsg_ItemPurchased` |
| Combat log | `CMsgDOTACombatLogEntry` |
| Game state | `CDOTAUserMsg_GamerulesStateChanged` |
| Unit events | `CDOTAUserMsg_UnitEvent` |
| Server info | `CSVCMsg_ServerInfo` |
| Network ticks | `CNETMsg_Tick` |

### Message Data Structure

All messages follow this structure:
```python
{
    "type": "CDOTAUserMsg_ChatMessage",  # Callback name
    "tick": 12345,                        # Game tick
    "net_tick": 12340,                    # Network tick
    "data": {                             # Message-specific fields
        "source_player_id": 3,
        "message_text": "glhf"
    },
    "timestamp": 1699900000000            # Unix timestamp (ms)
}
```

### Error Handling Pattern

```python
from python_manta import MantaParser

parser = MantaParser()

try:
    result = parser.parse_universal("match.dem", "CDOTAUserMsg_ChatMessage", 100)

    if result.success:
        for msg in result.messages:
            # Process msg.data
            pass
    else:
        print(f"Parse error: {result.error}")

except FileNotFoundError:
    print("Demo file not found")
except ValueError as e:
    print(f"Parsing failed: {e}")
```

### Key Constraints for AI

1. **Callback names are case-sensitive** - Use exact names from the callback list
2. **Message filter uses substring matching** - `"Chat"` matches both `CDOTAUserMsg_ChatMessage` and `CDOTAUserMsg_ChatEvent`
3. **Use `max_messages` > 0 for large replays** - Prevents memory issues
4. **Replay files are large** - Typical match ~100-200MB
5. **Some callbacks produce many messages** - `CNETMsg_Tick` fires thousands of times per match

### Typical Message Counts per Match

| Callback | Typical Count |
|----------|---------------|
| `CNETMsg_Tick` | 50,000+ |
| `CSVCMsg_PacketEntities` | 30,000+ |
| `CDOTAUserMsg_UnitEvent` | 5,000+ |
| `CDOTAUserMsg_OverheadEvent` | 2,000+ |
| `CDOTAUserMsg_ChatMessage` | 10-100 |
| `CDOTAUserMsg_LocationPing` | 50-500 |
| `CDOTAUserMsg_ItemPurchased` | 100-300 |
| `CDemoFileHeader` | 1 |
| `CDemoFileInfo` | 1 |

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

- **Python Manta GitHub:** https://github.com/equilibrium-coach/python-manta
- **PyPI Package:** https://pypi.org/project/python-manta/
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
