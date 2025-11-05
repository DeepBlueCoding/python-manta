package main

import (
	"github.com/dotabuff/manta"
	"github.com/dotabuff/manta/dota"
)

func setupDOTAUserCallbacks(parser *manta.Parser, messages *[]MessageEvent, filter string, maxMsgs int) {
	// All 94 missing DOTA User Message callbacks
	parser.Callbacks.OnCDOTAUserMsg_AbilityDraftRequestAbility(func(m *dota.CDOTAUserMsg_AbilityDraftRequestAbility) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_AbilityDraftRequestAbility", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_AbilitySteal(func(m *dota.CDOTAUserMsg_AbilitySteal) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_AbilitySteal", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_AddQuestLogEntry(func(m *dota.CDOTAUserMsg_AddQuestLogEntry) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_AddQuestLogEntry", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_AghsStatusAlert(func(m *dota.CDOTAUserMsg_AghsStatusAlert) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_AghsStatusAlert", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_AllStarEvent(func(m *dota.CDOTAUserMsg_AllStarEvent) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_AllStarEvent", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_BeastChat(func(m *dota.CDOTAUserMsg_BeastChat) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_BeastChat", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_BoosterState(func(m *dota.CDOTAUserMsg_BoosterState) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_BoosterState", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_ChatMessage(func(m *dota.CDOTAUserMsg_ChatMessage) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_ChatMessage", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_ChatWheelCooldown(func(m *dota.CDOTAUserMsg_ChatWheelCooldown) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_ChatWheelCooldown", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_ClientLoadGridNav(func(m *dota.CDOTAUserMsg_ClientLoadGridNav) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_ClientLoadGridNav", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_CompendiumState(func(m *dota.CDOTAUserMsg_CompendiumState) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_CompendiumState", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_ContextualTip(func(m *dota.CDOTAUserMsg_ContextualTip) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_ContextualTip", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_CustomHeaderMessage(func(m *dota.CDOTAUserMsg_CustomHeaderMessage) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_CustomHeaderMessage", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_CustomHudElement_Create(func(m *dota.CDOTAUserMsg_CustomHudElement_Create) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_CustomHudElement_Create", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_CustomHudElement_Destroy(func(m *dota.CDOTAUserMsg_CustomHudElement_Destroy) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_CustomHudElement_Destroy", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_CustomHudElement_Modify(func(m *dota.CDOTAUserMsg_CustomHudElement_Modify) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_CustomHudElement_Modify", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_CustomMsg(func(m *dota.CDOTAUserMsg_CustomMsg) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_CustomMsg", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_DamageReport(func(m *dota.CDOTAUserMsg_DamageReport) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_DamageReport", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_DebugChallenge(func(m *dota.CDOTAUserMsg_DebugChallenge) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_DebugChallenge", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_DismissAllStatPopups(func(m *dota.CDOTAUserMsg_DismissAllStatPopups) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_DismissAllStatPopups", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_DuelAccepted(func(m *dota.CDOTAUserMsg_DuelAccepted) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_DuelAccepted", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_DuelOpponentKilled(func(m *dota.CDOTAUserMsg_DuelOpponentKilled) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_DuelOpponentKilled", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_DuelRequested(func(m *dota.CDOTAUserMsg_DuelRequested) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_DuelRequested", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_ESArcanaComboSummary(func(m *dota.CDOTAUserMsg_ESArcanaComboSummary) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_ESArcanaComboSummary", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_EmptyItemSlotAlert(func(m *dota.CDOTAUserMsg_EmptyItemSlotAlert) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_EmptyItemSlotAlert", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_EmptyTeleportAlert(func(m *dota.CDOTAUserMsg_EmptyTeleportAlert) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_EmptyTeleportAlert", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_FacetPing(func(m *dota.CDOTAUserMsg_FacetPing) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_FacetPing", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_FlipCoinResult(func(m *dota.CDOTAUserMsg_FlipCoinResult) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_FlipCoinResult", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_FoundNeutralItem(func(m *dota.CDOTAUserMsg_FoundNeutralItem) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_FoundNeutralItem", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_GamerulesStateChanged(func(m *dota.CDOTAUserMsg_GamerulesStateChanged) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_GamerulesStateChanged", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_GiftPlayer(func(m *dota.CDOTAUserMsg_GiftPlayer) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_GiftPlayer", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_GuildChallenge_Progress(func(m *dota.CDOTAUserMsg_GuildChallenge_Progress) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_GuildChallenge_Progress", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_HPManaAlert(func(m *dota.CDOTAUserMsg_HPManaAlert) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_HPManaAlert", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_HalloweenDrops(func(m *dota.CDOTAUserMsg_HalloweenDrops) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_HalloweenDrops", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_HighFiveCompleted(func(m *dota.CDOTAUserMsg_HighFiveCompleted) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_HighFiveCompleted", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_HighFiveLeftHanging(func(m *dota.CDOTAUserMsg_HighFiveLeftHanging) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_HighFiveLeftHanging", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_HotPotato_Created(func(m *dota.CDOTAUserMsg_HotPotato_Created) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_HotPotato_Created", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_HotPotato_Exploded(func(m *dota.CDOTAUserMsg_HotPotato_Exploded) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_HotPotato_Exploded", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_InnatePing(func(m *dota.CDOTAUserMsg_InnatePing) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_InnatePing", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_InvalidCommand(func(m *dota.CDOTAUserMsg_InvalidCommand) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_InvalidCommand", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_ItemFound(func(m *dota.CDOTAUserMsg_ItemFound) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_ItemFound", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_MadstoneAlert(func(m *dota.CDOTAUserMsg_MadstoneAlert) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_MadstoneAlert", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_MiniKillCamInfo(func(m *dota.CDOTAUserMsg_MiniKillCamInfo) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_MiniKillCamInfo", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_MiniTaunt(func(m *dota.CDOTAUserMsg_MiniTaunt) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_MiniTaunt", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_ModifierAlert(func(m *dota.CDOTAUserMsg_ModifierAlert) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_ModifierAlert", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_MoveCameraToUnit(func(m *dota.CDOTAUserMsg_MoveCameraToUnit) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_MoveCameraToUnit", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_MutedPlayers(func(m *dota.CDOTAUserMsg_MutedPlayers) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_MutedPlayers", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_NeutralCraftAvailable(func(m *dota.CDOTAUserMsg_NeutralCraftAvailable) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_NeutralCraftAvailable", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_OMArcanaCombo(func(m *dota.CDOTAUserMsg_OMArcanaCombo) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_OMArcanaCombo", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_OutpostCaptured(func(m *dota.CDOTAUserMsg_OutpostCaptured) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_OutpostCaptured", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_OutpostGrantedXP(func(m *dota.CDOTAUserMsg_OutpostGrantedXP) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_OutpostGrantedXP", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_Ping(func(m *dota.CDOTAUserMsg_Ping) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_Ping", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_PlayerDraftPick(func(m *dota.CDOTAUserMsg_PlayerDraftPick) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_PlayerDraftPick", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_PlayerDraftSuggestPick(func(m *dota.CDOTAUserMsg_PlayerDraftSuggestPick) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_PlayerDraftSuggestPick", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_ProjectionAbility(func(m *dota.CDOTAUserMsg_ProjectionAbility) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_ProjectionAbility", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_ProjectionEvent(func(m *dota.CDOTAUserMsg_ProjectionEvent) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_ProjectionEvent", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_QoP_ArcanaSummary(func(m *dota.CDOTAUserMsg_QoP_ArcanaSummary) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_QoP_ArcanaSummary", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_QueuedOrderRemoved(func(m *dota.CDOTAUserMsg_QueuedOrderRemoved) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_QueuedOrderRemoved", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_RadarAlert(func(m *dota.CDOTAUserMsg_RadarAlert) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_RadarAlert", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_RockPaperScissorsFinished(func(m *dota.CDOTAUserMsg_RockPaperScissorsFinished) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_RockPaperScissorsFinished", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_RockPaperScissorsStarted(func(m *dota.CDOTAUserMsg_RockPaperScissorsStarted) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_RockPaperScissorsStarted", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_RollDiceResult(func(m *dota.CDOTAUserMsg_RollDiceResult) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_RollDiceResult", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_RoshanTimer(func(m *dota.CDOTAUserMsg_RoshanTimer) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_RoshanTimer", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_SalutePlayer(func(m *dota.CDOTAUserMsg_SalutePlayer) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_SalutePlayer", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_SelectPenaltyGold(func(m *dota.CDOTAUserMsg_SelectPenaltyGold) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_SelectPenaltyGold", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_SendFinalGold(func(m *dota.CDOTAUserMsg_SendFinalGold) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_SendFinalGold", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_SendRoshanSpectatorPhase(func(m *dota.CDOTAUserMsg_SendRoshanSpectatorPhase) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_SendRoshanSpectatorPhase", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_ShovelUnearth(func(m *dota.CDOTAUserMsg_ShovelUnearth) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_ShovelUnearth", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_ShowGenericPopup(func(m *dota.CDOTAUserMsg_ShowGenericPopup) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_ShowGenericPopup", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_SpeechBubble(func(m *dota.CDOTAUserMsg_SpeechBubble) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_SpeechBubble", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_TE_DestroyProjectile(func(m *dota.CDOTAUserMsg_TE_DestroyProjectile) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_TE_DestroyProjectile", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_TE_DotaBloodImpact(func(m *dota.CDOTAUserMsg_TE_DotaBloodImpact) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_TE_DotaBloodImpact", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_TE_Projectile(func(m *dota.CDOTAUserMsg_TE_Projectile) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_TE_Projectile", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_TE_ProjectileLoc(func(m *dota.CDOTAUserMsg_TE_ProjectileLoc) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_TE_ProjectileLoc", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_TE_UnitAnimation(func(m *dota.CDOTAUserMsg_TE_UnitAnimation) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_TE_UnitAnimation", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_TE_UnitAnimationEnd(func(m *dota.CDOTAUserMsg_TE_UnitAnimationEnd) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_TE_UnitAnimationEnd", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_TalentTreeAlert(func(m *dota.CDOTAUserMsg_TalentTreeAlert) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_TalentTreeAlert", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_TimerAlert(func(m *dota.CDOTAUserMsg_TimerAlert) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_TimerAlert", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_TipAlert(func(m *dota.CDOTAUserMsg_TipAlert) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_TipAlert", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_TutorialFade(func(m *dota.CDOTAUserMsg_TutorialFade) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_TutorialFade", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_TutorialFinish(func(m *dota.CDOTAUserMsg_TutorialFinish) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_TutorialFinish", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_TutorialMinimapPosition(func(m *dota.CDOTAUserMsg_TutorialMinimapPosition) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_TutorialMinimapPosition", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_TutorialPingMinimap(func(m *dota.CDOTAUserMsg_TutorialPingMinimap) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_TutorialPingMinimap", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_TutorialRequestExp(func(m *dota.CDOTAUserMsg_TutorialRequestExp) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_TutorialRequestExp", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_UpdateLinearProjectileCPData(func(m *dota.CDOTAUserMsg_UpdateLinearProjectileCPData) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_UpdateLinearProjectileCPData", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_VersusScene_PlayerBehavior(func(m *dota.CDOTAUserMsg_VersusScene_PlayerBehavior) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_VersusScene_PlayerBehavior", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_VoteEnd(func(m *dota.CDOTAUserMsg_VoteEnd) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_VoteEnd", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_VoteStart(func(m *dota.CDOTAUserMsg_VoteStart) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_VoteStart", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_VoteUpdate(func(m *dota.CDOTAUserMsg_VoteUpdate) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_VoteUpdate", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_WK_Arcana_Progress(func(m *dota.CDOTAUserMsg_WK_Arcana_Progress) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_WK_Arcana_Progress", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_WRArcanaProgress(func(m *dota.CDOTAUserMsg_WRArcanaProgress) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_WRArcanaProgress", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_WRArcanaSummary(func(m *dota.CDOTAUserMsg_WRArcanaSummary) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_WRArcanaSummary", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_XPAlert(func(m *dota.CDOTAUserMsg_XPAlert) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_XPAlert", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
}