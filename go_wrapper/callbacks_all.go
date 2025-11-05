package main

import (
	"github.com/dotabuff/manta"
	"github.com/dotabuff/manta/dota"
)

// All remaining callback setups in one file for simplicity

func setupMiscCallbacks(parser *manta.Parser, messages *[]MessageEvent, filter string, maxMsgs int) {
	parser.Callbacks.OnCMsgClearDecalsForSkeletonInstanceEvent(func(m *dota.CMsgClearDecalsForSkeletonInstanceEvent) error {
		return addFilteredMessage(messages, "CMsgClearDecalsForSkeletonInstanceEvent", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCMsgClearEntityDecalsEvent(func(m *dota.CMsgClearEntityDecalsEvent) error {
		return addFilteredMessage(messages, "CMsgClearEntityDecalsEvent", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCMsgClearWorldDecalsEvent(func(m *dota.CMsgClearWorldDecalsEvent) error {
		return addFilteredMessage(messages, "CMsgClearWorldDecalsEvent", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCMsgDOTACombatLogEntry(func(m *dota.CMsgDOTACombatLogEntry) error {
		return addFilteredMessage(messages, "CMsgDOTACombatLogEntry", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCMsgGCToClientTournamentItemDrop(func(m *dota.CMsgGCToClientTournamentItemDrop) error {
		return addFilteredMessage(messages, "CMsgGCToClientTournamentItemDrop", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCMsgPlaceDecalEvent(func(m *dota.CMsgPlaceDecalEvent) error {
		return addFilteredMessage(messages, "CMsgPlaceDecalEvent", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCMsgSosSetLibraryStackFields(func(m *dota.CMsgSosSetLibraryStackFields) error {
		return addFilteredMessage(messages, "CMsgSosSetLibraryStackFields", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCMsgSosSetSoundEventParams(func(m *dota.CMsgSosSetSoundEventParams) error {
		return addFilteredMessage(messages, "CMsgSosSetSoundEventParams", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCMsgSosStartSoundEvent(func(m *dota.CMsgSosStartSoundEvent) error {
		return addFilteredMessage(messages, "CMsgSosStartSoundEvent", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCMsgSosStopSoundEvent(func(m *dota.CMsgSosStopSoundEvent) error {
		return addFilteredMessage(messages, "CMsgSosStopSoundEvent", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCMsgSosStopSoundEventHash(func(m *dota.CMsgSosStopSoundEventHash) error {
		return addFilteredMessage(messages, "CMsgSosStopSoundEventHash", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCMsgSource1LegacyListenEvents(func(m *dota.CMsgSource1LegacyListenEvents) error {
		return addFilteredMessage(messages, "CMsgSource1LegacyListenEvents", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCMsgVDebugGameSessionIDEvent(func(m *dota.CMsgVDebugGameSessionIDEvent) error {
		return addFilteredMessage(messages, "CMsgVDebugGameSessionIDEvent", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
}

func setupNetworkCallbacks(parser *manta.Parser, messages *[]MessageEvent, filter string, maxMsgs int) {
	parser.Callbacks.OnCNETMsg_DebugOverlay(func(m *dota.CNETMsg_DebugOverlay) error {
		return addFilteredMessage(messages, "CNETMsg_DebugOverlay", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
}

func setupSVCCallbacks(parser *manta.Parser, messages *[]MessageEvent, filter string, maxMsgs int) {
	parser.Callbacks.OnCSVCMsg_Broadcast_Command(func(m *dota.CSVCMsg_Broadcast_Command) error {
		return addFilteredMessage(messages, "CSVCMsg_Broadcast_Command", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCSVCMsg_CmdKeyValues(func(m *dota.CSVCMsg_CmdKeyValues) error {
		return addFilteredMessage(messages, "CSVCMsg_CmdKeyValues", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCSVCMsg_FullFrameSplit(func(m *dota.CSVCMsg_FullFrameSplit) error {
		return addFilteredMessage(messages, "CSVCMsg_FullFrameSplit", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCSVCMsg_HLTVStatus(func(m *dota.CSVCMsg_HLTVStatus) error {
		return addFilteredMessage(messages, "CSVCMsg_HLTVStatus", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCSVCMsg_HltvFixupOperatorStatus(func(m *dota.CSVCMsg_HltvFixupOperatorStatus) error {
		return addFilteredMessage(messages, "CSVCMsg_HltvFixupOperatorStatus", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCSVCMsg_PeerList(func(m *dota.CSVCMsg_PeerList) error {
		return addFilteredMessage(messages, "CSVCMsg_PeerList", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCSVCMsg_RconServerDetails(func(m *dota.CSVCMsg_RconServerDetails) error {
		return addFilteredMessage(messages, "CSVCMsg_RconServerDetails", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCSVCMsg_ServerSteamID(func(m *dota.CSVCMsg_ServerSteamID) error {
		return addFilteredMessage(messages, "CSVCMsg_ServerSteamID", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCSVCMsg_StopSound(func(m *dota.CSVCMsg_StopSound) error {
		return addFilteredMessage(messages, "CSVCMsg_StopSound", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
}

func setupUserCallbacks(parser *manta.Parser, messages *[]MessageEvent, filter string, maxMsgs int) {
	parser.Callbacks.OnCUserMessageAchievementEvent(func(m *dota.CUserMessageAchievementEvent) error {
		return addFilteredMessage(messages, "CUserMessageAchievementEvent", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCUserMessageAudioParameter(func(m *dota.CUserMessageAudioParameter) error {
		return addFilteredMessage(messages, "CUserMessageAudioParameter", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCUserMessageCameraTransition(func(m *dota.CUserMessageCameraTransition) error {
		return addFilteredMessage(messages, "CUserMessageCameraTransition", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCUserMessageCloseCaption(func(m *dota.CUserMessageCloseCaption) error {
		return addFilteredMessage(messages, "CUserMessageCloseCaption", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCUserMessageCloseCaptionDirect(func(m *dota.CUserMessageCloseCaptionDirect) error {
		return addFilteredMessage(messages, "CUserMessageCloseCaptionDirect", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCUserMessageCloseCaptionPlaceholder(func(m *dota.CUserMessageCloseCaptionPlaceholder) error {
		return addFilteredMessage(messages, "CUserMessageCloseCaptionPlaceholder", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCUserMessageColoredText(func(m *dota.CUserMessageColoredText) error {
		return addFilteredMessage(messages, "CUserMessageColoredText", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCUserMessageHapticsManagerEffect(func(m *dota.CUserMessageHapticsManagerEffect) error {
		return addFilteredMessage(messages, "CUserMessageHapticsManagerEffect", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCUserMessageHapticsManagerPulse(func(m *dota.CUserMessageHapticsManagerPulse) error {
		return addFilteredMessage(messages, "CUserMessageHapticsManagerPulse", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCUserMessageItemPickup(func(m *dota.CUserMessageItemPickup) error {
		return addFilteredMessage(messages, "CUserMessageItemPickup", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCUserMessageLagCompensationError(func(m *dota.CUserMessageLagCompensationError) error {
		return addFilteredMessage(messages, "CUserMessageLagCompensationError", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCUserMessageRequestDiagnostic(func(m *dota.CUserMessageRequestDiagnostic) error {
		return addFilteredMessage(messages, "CUserMessageRequestDiagnostic", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCUserMessageRequestDllStatus(func(m *dota.CUserMessageRequestDllStatus) error {
		return addFilteredMessage(messages, "CUserMessageRequestDllStatus", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCUserMessageRequestInventory(func(m *dota.CUserMessageRequestInventory) error {
		return addFilteredMessage(messages, "CUserMessageRequestInventory", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCUserMessageRequestUtilAction(func(m *dota.CUserMessageRequestUtilAction) error {
		return addFilteredMessage(messages, "CUserMessageRequestUtilAction", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCUserMessageResetHUD(func(m *dota.CUserMessageResetHUD) error {
		return addFilteredMessage(messages, "CUserMessageResetHUD", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCUserMessageSayTextChannel(func(m *dota.CUserMessageSayTextChannel) error {
		return addFilteredMessage(messages, "CUserMessageSayTextChannel", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCUserMessageServerFrameTime(func(m *dota.CUserMessageServerFrameTime) error {
		return addFilteredMessage(messages, "CUserMessageServerFrameTime", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCUserMessageShakeDir(func(m *dota.CUserMessageShakeDir) error {
		return addFilteredMessage(messages, "CUserMessageShakeDir", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCUserMessageUpdateCssClasses(func(m *dota.CUserMessageUpdateCssClasses) error {
		return addFilteredMessage(messages, "CUserMessageUpdateCssClasses", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCUserMessageWaterShake(func(m *dota.CUserMessageWaterShake) error {
		return addFilteredMessage(messages, "CUserMessageWaterShake", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
}