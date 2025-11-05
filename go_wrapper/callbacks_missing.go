package main

import (
	"github.com/dotabuff/manta"
	"github.com/dotabuff/manta/dota"
)

// Additional missing DOTA User callbacks
func setupMissingCallbacks(parser *manta.Parser, messages *[]MessageEvent, filter string, maxMsgs int) {
	parser.Callbacks.OnCDOTAUserMsg_AbilityPing(func(m *dota.CDOTAUserMsg_AbilityPing) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_AbilityPing", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_BotChat(func(m *dota.CDOTAUserMsg_BotChat) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_BotChat", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_BuyBackStateAlert(func(m *dota.CDOTAUserMsg_BuyBackStateAlert) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_BuyBackStateAlert", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_ChatWheel(func(m *dota.CDOTAUserMsg_ChatWheel) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_ChatWheel", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_CoachHUDPing(func(m *dota.CDOTAUserMsg_CoachHUDPing) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_CoachHUDPing", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_CourierKilledAlert(func(m *dota.CDOTAUserMsg_CourierKilledAlert) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_CourierKilledAlert", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_DodgeTrackingProjectiles(func(m *dota.CDOTAUserMsg_DodgeTrackingProjectiles) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_DodgeTrackingProjectiles", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_ESArcanaCombo(func(m *dota.CDOTAUserMsg_ESArcanaCombo) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_ESArcanaCombo", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_EnemyItemAlert(func(m *dota.CDOTAUserMsg_EnemyItemAlert) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_EnemyItemAlert", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_GlobalLightColor(func(m *dota.CDOTAUserMsg_GlobalLightColor) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_GlobalLightColor", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_GlobalLightDirection(func(m *dota.CDOTAUserMsg_GlobalLightDirection) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_GlobalLightDirection", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_GlyphAlert(func(m *dota.CDOTAUserMsg_GlyphAlert) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_GlyphAlert", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_HeroRelicProgress(func(m *dota.CDOTAUserMsg_HeroRelicProgress) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_HeroRelicProgress", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_HudError(func(m *dota.CDOTAUserMsg_HudError) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_HudError", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_ItemAlert(func(m *dota.CDOTAUserMsg_ItemAlert) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_ItemAlert", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_ItemPurchased(func(m *dota.CDOTAUserMsg_ItemPurchased) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_ItemPurchased", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_ItemSold(func(m *dota.CDOTAUserMsg_ItemSold) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_ItemSold", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_KillcamDamageTaken(func(m *dota.CDOTAUserMsg_KillcamDamageTaken) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_KillcamDamageTaken", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_LocationPing(func(m *dota.CDOTAUserMsg_LocationPing) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_LocationPing", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_MapLine(func(m *dota.CDOTAUserMsg_MapLine) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_MapLine", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_MarsArenaOfBloodAttack(func(m *dota.CDOTAUserMsg_MarsArenaOfBloodAttack) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_MarsArenaOfBloodAttack", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_MinimapDebugPoint(func(m *dota.CDOTAUserMsg_MinimapDebugPoint) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_MinimapDebugPoint", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_MinimapEvent(func(m *dota.CDOTAUserMsg_MinimapEvent) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_MinimapEvent", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_MuertaReleaseEvent_AssignedTargetKilled(func(m *dota.CDOTAUserMsg_MuertaReleaseEvent_AssignedTargetKilled) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_MuertaReleaseEvent_AssignedTargetKilled", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_NeutralCampAlert(func(m *dota.CDOTAUserMsg_NeutralCampAlert) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_NeutralCampAlert", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_NevermoreRequiem(func(m *dota.CDOTAUserMsg_NevermoreRequiem) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_NevermoreRequiem", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_OverheadEvent(func(m *dota.CDOTAUserMsg_OverheadEvent) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_OverheadEvent", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_PauseMinigameData(func(m *dota.CDOTAUserMsg_PauseMinigameData) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_PauseMinigameData", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_PingConfirmation(func(m *dota.CDOTAUserMsg_PingConfirmation) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_PingConfirmation", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_QuestStatus(func(m *dota.CDOTAUserMsg_QuestStatus) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_QuestStatus", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_QuickBuyAlert(func(m *dota.CDOTAUserMsg_QuickBuyAlert) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_QuickBuyAlert", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_ReceivedXmasGift(func(m *dota.CDOTAUserMsg_ReceivedXmasGift) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_ReceivedXmasGift", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_ReplaceQueryUnit(func(m *dota.CDOTAUserMsg_ReplaceQueryUnit) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_ReplaceQueryUnit", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_SendGenericToolTip(func(m *dota.CDOTAUserMsg_SendGenericToolTip) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_SendGenericToolTip", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_SendRoshanPopup(func(m *dota.CDOTAUserMsg_SendRoshanPopup) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_SendRoshanPopup", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_SendStatPopup(func(m *dota.CDOTAUserMsg_SendStatPopup) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_SendStatPopup", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_SetNextAutobuyItem(func(m *dota.CDOTAUserMsg_SetNextAutobuyItem) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_SetNextAutobuyItem", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_SharedCooldown(func(m *dota.CDOTAUserMsg_SharedCooldown) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_SharedCooldown", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_ShowSurvey(func(m *dota.CDOTAUserMsg_ShowSurvey) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_ShowSurvey", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_SpectatorPlayerClick(func(m *dota.CDOTAUserMsg_SpectatorPlayerClick) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_SpectatorPlayerClick", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_SpectatorPlayerUnitOrders(func(m *dota.CDOTAUserMsg_SpectatorPlayerUnitOrders) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_SpectatorPlayerUnitOrders", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_StatsHeroMinuteDetails(func(m *dota.CDOTAUserMsg_StatsHeroMinuteDetails) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_StatsHeroMinuteDetails", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_StatsMatchDetails(func(m *dota.CDOTAUserMsg_StatsMatchDetails) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_StatsMatchDetails", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_SuggestHeroPick(func(m *dota.CDOTAUserMsg_SuggestHeroPick) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_SuggestHeroPick", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_SuggestHeroRole(func(m *dota.CDOTAUserMsg_SuggestHeroRole) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_SuggestHeroRole", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_SwapVerify(func(m *dota.CDOTAUserMsg_SwapVerify) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_SwapVerify", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_TutorialTipInfo(func(m *dota.CDOTAUserMsg_TutorialTipInfo) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_TutorialTipInfo", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_UnitEvent(func(m *dota.CDOTAUserMsg_UnitEvent) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_UnitEvent", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_UpdateQuestProgress(func(m *dota.CDOTAUserMsg_UpdateQuestProgress) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_UpdateQuestProgress", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_UpdateSharedContent(func(m *dota.CDOTAUserMsg_UpdateSharedContent) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_UpdateSharedContent", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_WillPurchaseAlert(func(m *dota.CDOTAUserMsg_WillPurchaseAlert) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_WillPurchaseAlert", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_WorldLine(func(m *dota.CDOTAUserMsg_WorldLine) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_WorldLine", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	// Source1 Legacy callbacks
	parser.Callbacks.OnCMsgSource1LegacyGameEvent(func(m *dota.CMsgSource1LegacyGameEvent) error {
		return addFilteredMessage(messages, "CMsgSource1LegacyGameEvent", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCMsgSource1LegacyGameEventList(func(m *dota.CMsgSource1LegacyGameEventList) error {
		return addFilteredMessage(messages, "CMsgSource1LegacyGameEventList", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
}