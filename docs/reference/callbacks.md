
# Callbacks Reference

??? info "AI Summary"
    Complete reference of all 272 message callbacks available in Python Manta. Use with `parse_universal(demo_path, callback_name, max_messages)`. Callbacks are categorized: Dota User Messages (143 types for game events, chat, pings, items), Demo Messages (16 types for recording metadata), Network Messages (31 types for low-level networking), and misc messages. Filter matches substrings: "Chat" matches ChatMessage, ChatEvent, ChatWheel.

---

## Overview

Python Manta supports **272 message callbacks** inherited from the [dotabuff/manta](https://github.com/dotabuff/manta) Go library. Use `parse_universal()` to capture any of these message types.

```python
from python_manta import MantaParser

parser = MantaParser()

# Filter by exact callback name
result = parser.parse_universal("match.dem", "CDOTAUserMsg_ChatMessage", 100)

# Filter by substring (matches multiple)
result = parser.parse_universal("match.dem", "Chat", 200)  # ChatMessage, ChatEvent, etc.
```

---

## Dota User Messages (143)

Game-related messages visible to players.

### Communication

| Callback | Description |
|----------|-------------|
| `CDOTAUserMsg_ChatMessage` | Player chat messages |
| `CDOTAUserMsg_ChatEvent` | Chat events (kills, items, etc.) |
| `CDOTAUserMsg_ChatWheel` | Chat wheel phrases |
| `CDOTAUserMsg_ChatWheelCooldown` | Chat wheel cooldown |
| `CDOTAUserMsg_BotChat` | Bot chat messages |
| `CDOTAUserMsg_BeastChat` | Beast chat (custom game) |
| `CDOTAUserMsg_SpeechBubble` | Speech bubbles |

### Pings and Alerts

| Callback | Description |
|----------|-------------|
| `CDOTAUserMsg_LocationPing` | Map location pings |
| `CDOTAUserMsg_Ping` | General ping |
| `CDOTAUserMsg_PingConfirmation` | Ping confirmation |
| `CDOTAUserMsg_AbilityPing` | Ability ping |
| `CDOTAUserMsg_InnatePing` | Innate ability ping |
| `CDOTAUserMsg_FacetPing` | Facet ping |
| `CDOTAUserMsg_MinimapEvent` | Minimap events |
| `CDOTAUserMsg_MinimapDebugPoint` | Debug minimap points |
| `CDOTAUserMsg_MapLine` | Map drawing lines |
| `CDOTAUserMsg_WorldLine` | World drawing lines |
| `CDOTAUserMsg_CoachHUDPing` | Coach HUD pings |
| `CDOTAUserMsg_RadarAlert` | Radar alerts |

### Item Events

| Callback | Description |
|----------|-------------|
| `CDOTAUserMsg_ItemPurchased` | Item purchases |
| `CDOTAUserMsg_ItemSold` | Item sales |
| `CDOTAUserMsg_ItemFound` | Items found |
| `CDOTAUserMsg_ItemAlert` | Item alerts |
| `CDOTAUserMsg_EnemyItemAlert` | Enemy item alerts |
| `CDOTAUserMsg_QuickBuyAlert` | Quick buy alerts |
| `CDOTAUserMsg_WillPurchaseAlert` | Will purchase alerts |
| `CDOTAUserMsg_SetNextAutobuyItem` | Auto-buy settings |
| `CDOTAUserMsg_EmptyItemSlotAlert` | Empty slot alerts |
| `CDOTAUserMsg_FoundNeutralItem` | Neutral item found |

### Combat and Abilities

| Callback | Description |
|----------|-------------|
| `CDOTAUserMsg_UnitEvent` | Unit events (spawn, death, etc.) |
| `CDOTAUserMsg_OverheadEvent` | Overhead numbers (damage, heal) |
| `CDOTAUserMsg_DamageReport` | Damage reports |
| `CDOTAUserMsg_KillcamDamageTaken` | Killcam damage |
| `CDOTAUserMsg_MiniKillCamInfo` | Mini killcam info |
| `CDOTAUserMsg_AbilitySteal` | Ability steal (Rubick) |
| `CDOTAUserMsg_ModifierAlert` | Modifier alerts |
| `CDOTAUserMsg_SharedCooldown` | Shared cooldowns |
| `CDOTAUserMsg_DodgeTrackingProjectiles` | Projectile dodging |

### Projectiles

| Callback | Description |
|----------|-------------|
| `CDOTAUserMsg_CreateLinearProjectile` | Create projectile |
| `CDOTAUserMsg_DestroyLinearProjectile` | Destroy projectile |
| `CDOTAUserMsg_UpdateLinearProjectileCPData` | Update projectile |
| `CDOTAUserMsg_TE_Projectile` | Projectile effect |
| `CDOTAUserMsg_TE_ProjectileLoc` | Projectile location |
| `CDOTAUserMsg_TE_DestroyProjectile` | Destroy projectile effect |
| `CDOTAUserMsg_TE_DotaBloodImpact` | Blood impact effect |

### Animation

| Callback | Description |
|----------|-------------|
| `CDOTAUserMsg_TE_UnitAnimation` | Unit animation |
| `CDOTAUserMsg_TE_UnitAnimationEnd` | Animation end |
| `CDOTAUserMsg_MiniTaunt` | Mini taunt |
| `CDOTAUserMsg_HighFiveCompleted` | High five complete |
| `CDOTAUserMsg_HighFiveLeftHanging` | High five missed |
| `CDOTAUserMsg_SalutePlayer` | Player salute |

### Game State

| Callback | Description |
|----------|-------------|
| `CDOTAUserMsg_GamerulesStateChanged` | Game state change |
| `CDOTAUserMsg_SendFinalGold` | Final gold amounts |
| `CDOTAUserMsg_SelectPenaltyGold` | Penalty gold |
| `CDOTAUserMsg_RoshanTimer` | Roshan timer |
| `CDOTAUserMsg_SendRoshanPopup` | Roshan popup |
| `CDOTAUserMsg_SendRoshanSpectatorPhase` | Roshan phase |
| `CDOTAUserMsg_OutpostCaptured` | Outpost captured |
| `CDOTAUserMsg_OutpostGrantedXP` | Outpost XP |
| `CDOTAUserMsg_XPAlert` | XP alerts |

### Draft and Hero Selection

| Callback | Description |
|----------|-------------|
| `CDOTAUserMsg_AbilityDraftRequestAbility` | Ability draft request |
| `CDOTAUserMsg_PlayerDraftPick` | Draft pick |
| `CDOTAUserMsg_PlayerDraftSuggestPick` | Draft suggestion |
| `CDOTAUserMsg_SuggestHeroPick` | Hero suggestion |
| `CDOTAUserMsg_SuggestHeroRole` | Role suggestion |
| `CDOTAUserMsg_SwapVerify` | Swap verification |

### Stats and Progress

| Callback | Description |
|----------|-------------|
| `CDOTAUserMsg_StatsMatchDetails` | Match statistics |
| `CDOTAUserMsg_StatsHeroMinuteDetails` | Per-minute hero stats |
| `CDOTAUserMsg_HeroRelicProgress` | Hero relic progress |
| `CDOTAUserMsg_QuestStatus` | Quest status |
| `CDOTAUserMsg_UpdateQuestProgress` | Quest progress update |
| `CDOTAUserMsg_AddQuestLogEntry` | Quest log entry |
| `CDOTAUserMsg_GuildChallenge_Progress` | Guild challenge |
| `CDOTAUserMsg_CompendiumState` | Compendium state |

### Spectator

| Callback | Description |
|----------|-------------|
| `CDOTAUserMsg_SpectatorPlayerClick` | Spectator clicks |
| `CDOTAUserMsg_SpectatorPlayerUnitOrders` | Spectator unit orders |
| `CDOTAUserMsg_MoveCameraToUnit` | Camera movement |
| `CDOTAUserMsg_CombatHeroPositions` | Hero positions |

### Alerts

| Callback | Description |
|----------|-------------|
| `CDOTAUserMsg_HPManaAlert` | HP/Mana alerts |
| `CDOTAUserMsg_GlyphAlert` | Glyph alerts |
| `CDOTAUserMsg_NeutralCampAlert` | Neutral camp alerts |
| `CDOTAUserMsg_CourierKilledAlert` | Courier killed |
| `CDOTAUserMsg_BuyBackStateAlert` | Buyback state |
| `CDOTAUserMsg_AghsStatusAlert` | Aghanim's status |
| `CDOTAUserMsg_TalentTreeAlert` | Talent alerts |
| `CDOTAUserMsg_TimerAlert` | Timer alerts |
| `CDOTAUserMsg_TipAlert` | Tip alerts |
| `CDOTAUserMsg_MadstoneAlert` | Madstone alerts |
| `CDOTAUserMsg_EmptyTeleportAlert` | Empty TP scroll |

### Duel and Combat

| Callback | Description |
|----------|-------------|
| `CDOTAUserMsg_DuelRequested` | Duel request |
| `CDOTAUserMsg_DuelAccepted` | Duel accepted |
| `CDOTAUserMsg_DuelOpponentKilled` | Duel kill |
| `CDOTAUserMsg_NevermoreRequiem` | SF Requiem |
| `CDOTAUserMsg_MarsArenaOfBloodAttack` | Mars Arena |

### Arcana and Cosmetics

| Callback | Description |
|----------|-------------|
| `CDOTAUserMsg_ESArcanaCombo` | Earth Spirit Arcana |
| `CDOTAUserMsg_ESArcanaComboSummary` | ES Arcana summary |
| `CDOTAUserMsg_WRArcanaProgress` | Windranger Arcana |
| `CDOTAUserMsg_WRArcanaSummary` | WR Arcana summary |
| `CDOTAUserMsg_QoP_ArcanaSummary` | QoP Arcana |
| `CDOTAUserMsg_OMArcanaCombo` | Ogre Magi Arcana |
| `CDOTAUserMsg_WK_Arcana_Progress` | Wraith King Arcana |
| `CDOTAUserMsg_MuertaReleaseEvent_AssignedTargetKilled` | Muerta event |

### Voting and Social

| Callback | Description |
|----------|-------------|
| `CDOTAUserMsg_VoteStart` | Vote start |
| `CDOTAUserMsg_VoteUpdate` | Vote update |
| `CDOTAUserMsg_VoteEnd` | Vote end |
| `CDOTAUserMsg_FlipCoinResult` | Coin flip |
| `CDOTAUserMsg_RollDiceResult` | Dice roll |
| `CDOTAUserMsg_RockPaperScissorsStarted` | RPS started |
| `CDOTAUserMsg_RockPaperScissorsFinished` | RPS finished |
| `CDOTAUserMsg_GiftPlayer` | Gift player |

### UI and HUD

| Callback | Description |
|----------|-------------|
| `CDOTAUserMsg_HudError` | HUD errors |
| `CDOTAUserMsg_SendStatPopup` | Stat popup |
| `CDOTAUserMsg_SendGenericToolTip` | Generic tooltip |
| `CDOTAUserMsg_ShowGenericPopup` | Generic popup |
| `CDOTAUserMsg_DismissAllStatPopups` | Dismiss popups |
| `CDOTAUserMsg_CustomMsg` | Custom message |
| `CDOTAUserMsg_CustomHeaderMessage` | Custom header |
| `CDOTAUserMsg_CustomHudElement_Create` | Custom HUD create |
| `CDOTAUserMsg_CustomHudElement_Modify` | Custom HUD modify |
| `CDOTAUserMsg_CustomHudElement_Destroy` | Custom HUD destroy |
| `CDOTAUserMsg_ContextualTip` | Contextual tips |
| `CDOTAUserMsg_ShowSurvey` | Survey popup |
| `CDOTAUserMsg_InvalidCommand` | Invalid command |

### Tutorial

| Callback | Description |
|----------|-------------|
| `CDOTAUserMsg_TutorialTipInfo` | Tutorial tips |
| `CDOTAUserMsg_TutorialFade` | Tutorial fade |
| `CDOTAUserMsg_TutorialFinish` | Tutorial finish |
| `CDOTAUserMsg_TutorialMinimapPosition` | Minimap position |
| `CDOTAUserMsg_TutorialPingMinimap` | Minimap ping |
| `CDOTAUserMsg_TutorialRequestExp` | Request XP |

### Misc Dota

| Callback | Description |
|----------|-------------|
| `CDOTAUserMsg_BoosterState` | Booster state |
| `CDOTAUserMsg_HalloweenDrops` | Halloween drops |
| `CDOTAUserMsg_ReceivedXmasGift` | Xmas gift |
| `CDOTAUserMsg_MutedPlayers` | Muted players |
| `CDOTAUserMsg_PauseMinigameData` | Pause minigame |
| `CDOTAUserMsg_ReplaceQueryUnit` | Replace query unit |
| `CDOTAUserMsg_UpdateSharedContent` | Shared content |
| `CDOTAUserMsg_QueuedOrderRemoved` | Queued order |
| `CDOTAUserMsg_ProjectionAbility` | Projection ability |
| `CDOTAUserMsg_ProjectionEvent` | Projection event |
| `CDOTAUserMsg_VersusScene_PlayerBehavior` | Versus scene |
| `CDOTAUserMsg_AIDebugLine` | AI debug |
| `CDOTAUserMsg_CombatLogBulkData` | Combat log bulk |
| `CDOTAUserMsg_AllStarEvent` | All-Star event |
| `CDOTAUserMsg_DebugChallenge` | Debug challenge |
| `CDOTAUserMsg_ClientLoadGridNav` | Grid nav |
| `CDOTAUserMsg_GlobalLightColor` | Global light color |
| `CDOTAUserMsg_GlobalLightDirection` | Global light direction |
| `CDOTAUserMsg_ShovelUnearth` | Shovel unearth |
| `CDOTAUserMsg_NeutralCraftAvailable` | Neutral craft |
| `CDOTAUserMsg_HotPotato_Created` | Hot potato created |
| `CDOTAUserMsg_HotPotato_Exploded` | Hot potato exploded |

---

## Demo Messages (16)

Recording-related messages from the demo file.

| Callback | Description |
|----------|-------------|
| `CDemoFileHeader` | File header |
| `CDemoFileInfo` | Match info (picks/bans) |
| `CDemoPacket` | Demo packet |
| `CDemoFullPacket` | Full state snapshot |
| `CDemoSyncTick` | Sync tick |
| `CDemoStop` | Demo stop |
| `CDemoStringTables` | String tables |
| `CDemoSendTables` | Send tables |
| `CDemoClassInfo` | Class info |
| `CDemoSignonPacket` | Signon packet |
| `CDemoConsoleCmd` | Console command |
| `CDemoCustomData` | Custom data |
| `CDemoCustomDataCallbacks` | Custom callbacks |
| `CDemoUserCmd` | User command |
| `CDemoSaveGame` | Save game |
| `CDemoSpawnGroups` | Spawn groups |
| `CDemoAnimationData` | Animation data |
| `CDemoAnimationHeader` | Animation header |
| `CDemoRecovery` | Recovery data |
| `CDOTAMatchMetadataFile` | Match metadata |

---

## Network Messages (31)

Low-level network protocol messages.

### NET Messages

| Callback | Description |
|----------|-------------|
| `CNETMsg_Tick` | Network tick (very frequent!) |
| `CNETMsg_NOP` | No operation |
| `CNETMsg_SetConVar` | Set console variable |
| `CNETMsg_SignonState` | Signon state |
| `CNETMsg_StringCmd` | String command |
| `CNETMsg_SplitScreenUser` | Split screen |
| `CNETMsg_DebugOverlay` | Debug overlay |

### Spawn Group Messages

| Callback | Description |
|----------|-------------|
| `CNETMsg_SpawnGroup_Load` | Load spawn group |
| `CNETMsg_SpawnGroup_Unload` | Unload spawn group |
| `CNETMsg_SpawnGroup_LoadCompleted` | Load complete |
| `CNETMsg_SpawnGroup_ManifestUpdate` | Manifest update |
| `CNETMsg_SpawnGroup_SetCreationTick` | Creation tick |

### SVC Messages

| Callback | Description |
|----------|-------------|
| `CSVCMsg_ServerInfo` | Server information |
| `CSVCMsg_ClassInfo` | Class information |
| `CSVCMsg_CreateStringTable` | Create string table |
| `CSVCMsg_UpdateStringTable` | Update string table |
| `CSVCMsg_ClearAllStringTables` | Clear string tables |
| `CSVCMsg_PacketEntities` | Entity updates |
| `CSVCMsg_PacketReliable` | Reliable packet |
| `CSVCMsg_FlattenedSerializer` | Serializer data |
| `CSVCMsg_Prefetch` | Prefetch |
| `CSVCMsg_SetView` | Set view |
| `CSVCMsg_SetPause` | Set pause |
| `CSVCMsg_Sounds` | Sound events |
| `CSVCMsg_VoiceInit` | Voice init |
| `CSVCMsg_VoiceData` | Voice data |
| `CSVCMsg_Print` | Print message |
| `CSVCMsg_Menu` | Menu |
| `CSVCMsg_GetCvarValue` | Get cvar value |
| `CSVCMsg_UserMessage` | User message |
| `CSVCMsg_SplitScreen` | Split screen |
| `CSVCMsg_BSPDecal` | BSP decal |
| `CSVCMsg_CmdKeyValues` | Key values |
| `CSVCMsg_Broadcast_Command` | Broadcast command |
| `CSVCMsg_FullFrameSplit` | Frame split |
| `CSVCMsg_HLTVStatus` | HLTV status |
| `CSVCMsg_HltvFixupOperatorStatus` | HLTV fixup |
| `CSVCMsg_PeerList` | Peer list |
| `CSVCMsg_RconServerDetails` | RCON details |
| `CSVCMsg_ServerSteamID` | Server Steam ID |
| `CSVCMsg_StopSound` | Stop sound |

---

## Combat Log Message

| Callback | Description |
|----------|-------------|
| `CMsgDOTACombatLogEntry` | Combat log entry |

!!! note

    For structured combat log parsing, use `parse_combat_log()` instead of `parse_universal()`.

---

## Entity Messages (6)

Entity-related messages.

| Callback | Description |
|----------|-------------|
| `CEntityMessageDoSpark` | Spark effect |
| `CEntityMessageFixAngle` | Fix angle |
| `CEntityMessagePlayJingle` | Play jingle |
| `CEntityMessagePropagateForce` | Propagate force |
| `CEntityMessageRemoveAllDecals` | Remove decals |
| `CEntityMessageScreenOverlay` | Screen overlay |

---

## General User Messages (25)

Generic Source 2 user messages.

| Callback | Description |
|----------|-------------|
| `CUserMessageSayText` | Say text |
| `CUserMessageSayText2` | Say text 2 |
| `CUserMessageSayTextChannel` | Say text channel |
| `CUserMessageTextMsg` | Text message |
| `CUserMessageHudMsg` | HUD message |
| `CUserMessageHudText` | HUD text |
| `CUserMessageShake` | Screen shake |
| `CUserMessageShakeDir` | Directional shake |
| `CUserMessageFade` | Screen fade |
| `CUserMessageScreenTilt` | Screen tilt |
| `CUserMessageRumble` | Rumble |
| `CUserMessageCloseCaption` | Closed caption |
| `CUserMessageCloseCaptionDirect` | Direct caption |
| `CUserMessageCloseCaptionPlaceholder` | Caption placeholder |
| `CUserMessageSendAudio` | Send audio |
| `CUserMessageAudioParameter` | Audio parameter |
| `CUserMessageVoiceMask` | Voice mask |
| `CUserMessageRequestState` | Request state |
| `CUserMessageRequestInventory` | Request inventory |
| `CUserMessageRequestDiagnostic` | Request diagnostic |
| `CUserMessageRequestDllStatus` | Request DLL status |
| `CUserMessageRequestUtilAction` | Request util action |
| `CUserMessageResetHUD` | Reset HUD |
| `CUserMessageItemPickup` | Item pickup |
| `CUserMessageShowMenu` | Show menu |
| `CUserMessageColoredText` | Colored text |
| `CUserMessageCreditsMsg` | Credits |
| `CUserMessageAchievementEvent` | Achievement |
| `CUserMessageCurrentTimescale` | Current timescale |
| `CUserMessageDesiredTimescale` | Desired timescale |
| `CUserMessageGameTitle` | Game title |
| `CUserMessageAmmoDenied` | Ammo denied |
| `CUserMessageCameraTransition` | Camera transition |
| `CUserMessageHapticsManagerEffect` | Haptics effect |
| `CUserMessageHapticsManagerPulse` | Haptics pulse |
| `CUserMessageLagCompensationError` | Lag compensation |
| `CUserMessageServerFrameTime` | Server frame time |
| `CUserMessageUpdateCssClasses` | Update CSS |
| `CUserMessageWaterShake` | Water shake |

---

## Misc Messages (15)

Other message types.

| Callback | Description |
|----------|-------------|
| `CMsgSource1LegacyGameEvent` | Legacy game event |
| `CMsgSource1LegacyGameEventList` | Game event list |
| `CMsgSource1LegacyListenEvents` | Listen events |
| `CMsgDOTACombatLogEntry` | Combat log |
| `CMsgGCToClientTournamentItemDrop` | Tournament drop |
| `CMsgVDebugGameSessionIDEvent` | Debug session ID |
| `CMsgPlaceDecalEvent` | Place decal |
| `CMsgClearWorldDecalsEvent` | Clear world decals |
| `CMsgClearEntityDecalsEvent` | Clear entity decals |
| `CMsgClearDecalsForSkeletonInstanceEvent` | Clear skeleton decals |
| `CMsgSosStartSoundEvent` | Start sound |
| `CMsgSosStopSoundEvent` | Stop sound |
| `CMsgSosStopSoundEventHash` | Stop sound hash |
| `CMsgSosSetSoundEventParams` | Sound params |
| `CMsgSosSetLibraryStackFields` | Library stack |

---

## Usage Examples

### Common Filters

```python
# Chat and communication
chat = parser.parse_universal("match.dem", "ChatMessage", 100)
pings = parser.parse_universal("match.dem", "LocationPing", 100)
wheel = parser.parse_universal("match.dem", "ChatWheel", 100)

# Items
purchases = parser.parse_universal("match.dem", "ItemPurchased", 500)
alerts = parser.parse_universal("match.dem", "ItemAlert", 100)

# Combat
overhead = parser.parse_universal("match.dem", "OverheadEvent", 500)
unit_events = parser.parse_universal("match.dem", "UnitEvent", 200)

# Game state
state_changes = parser.parse_universal("match.dem", "GamerulesStateChanged", 20)
```

### Filtering Multiple Types

```python
# Substring "Alert" matches many alert types
alerts = parser.parse_universal("match.dem", "Alert", 500)

# Common matched types:
# - CDOTAUserMsg_ItemAlert
# - CDOTAUserMsg_EnemyItemAlert
# - CDOTAUserMsg_GlyphAlert
# - CDOTAUserMsg_NeutralCampAlert
# - etc.
```
