package main

import (
	"C"
	"encoding/json"
	"fmt"
	"os"
	"strings"
	"time"

	"github.com/dotabuff/manta"
	"github.com/dotabuff/manta/dota"
)

// UniversalParseResult holds the result of universal parsing
type UniversalParseResult struct {
	Messages []MessageEvent `json:"messages"`
	Success  bool           `json:"success"`
	Error    string         `json:"error,omitempty"`
	Count    int            `json:"count"`
}

// MessageEvent represents any Manta message with metadata
type MessageEvent struct {
	Type      string      `json:"type"`       // Message type name (e.g., "CDemoFileHeader")
	Tick      uint32      `json:"tick"`       // Tick when message occurred
	NetTick   uint32      `json:"net_tick"`   // Net tick when message occurred
	Data      interface{} `json:"data"`       // Raw message data
	Timestamp int64       `json:"timestamp"`  // Unix timestamp (if available)
}

//export ParseUniversal
func ParseUniversal(filePath *C.char, messageFilter *C.char, maxMessages C.int) *C.char {
	goFilePath := C.GoString(filePath)
	filter := C.GoString(messageFilter)
	maxMsgs := int(maxMessages)

	result, err := RunUniversal(goFilePath, filter, maxMsgs)
	if err != nil {
		failure := &UniversalParseResult{
			Messages: make([]MessageEvent, 0),
			Success:  false,
			Error:    err.Error(),
		}
		return marshalAndReturnUniversal(failure)
	}

	return marshalAndReturnUniversal(result)
}

// RunUniversal executes universal parsing and returns the Go result directly.
func RunUniversal(filePath string, filter string, maxMessages int) (*UniversalParseResult, error) {
	result := &UniversalParseResult{
		Messages: make([]MessageEvent, 0),
	}

	file, err := os.Open(filePath)
	if err != nil {
		return nil, fmt.Errorf("error opening file: %w", err)
	}
	defer file.Close()

	parser, err := manta.NewStreamParser(file)
	if err != nil {
		return nil, fmt.Errorf("error creating parser: %w", err)
	}

	setupAllCallbacks(parser, &result.Messages, filter, maxMessages)

	if err := parser.Start(); err != nil {
		return nil, fmt.Errorf("error parsing file: %w", err)
	}

	if maxMessages > 0 && len(result.Messages) > maxMessages {
		result.Messages = result.Messages[:maxMessages]
	}

	result.Success = true
	result.Count = len(result.Messages)
	return result, nil
}

// setupAllCallbacks sets up ALL 272+ Manta callbacks using modular functions
func setupAllCallbacks(parser *manta.Parser, messages *[]MessageEvent, filter string, maxMsgs int) {
	// Use modular callback setup functions
	setupDemoCallbacks(parser, messages, filter, maxMsgs)
	setupEntityCallbacks(parser, messages, filter, maxMsgs)
	setupMiscCallbacks(parser, messages, filter, maxMsgs)
	setupNetworkCallbacks(parser, messages, filter, maxMsgs)
	setupSVCCallbacks(parser, messages, filter, maxMsgs)
	setupUserCallbacks(parser, messages, filter, maxMsgs)
	setupDOTAUserCallbacks(parser, messages, filter, maxMsgs)
	setupMissingCallbacks(parser, messages, filter, maxMsgs)

	// Setup remaining callbacks that were already implemented
	parser.Callbacks.OnCDemoStop(func(m *dota.CDemoStop) error {
		return addFilteredMessage(messages, "CDemoStop", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	
	parser.Callbacks.OnCDemoFileHeader(func(m *dota.CDemoFileHeader) error {
		return addFilteredMessage(messages, "CDemoFileHeader", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	
	parser.Callbacks.OnCDemoFileInfo(func(m *dota.CDemoFileInfo) error {
		return addFilteredMessage(messages, "CDemoFileInfo", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})

	parser.Callbacks.OnCDemoSyncTick(func(m *dota.CDemoSyncTick) error {
		return addFilteredMessage(messages, "CDemoSyncTick", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})

	parser.Callbacks.OnCDemoSendTables(func(m *dota.CDemoSendTables) error {
		return addFilteredMessage(messages, "CDemoSendTables", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})

	parser.Callbacks.OnCDemoClassInfo(func(m *dota.CDemoClassInfo) error {
		return addFilteredMessage(messages, "CDemoClassInfo", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})

	parser.Callbacks.OnCDemoStringTables(func(m *dota.CDemoStringTables) error {
		return addFilteredMessage(messages, "CDemoStringTables", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})

	parser.Callbacks.OnCDemoPacket(func(m *dota.CDemoPacket) error {
		return addFilteredMessage(messages, "CDemoPacket", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})

	// parser.Callbacks.OnCDemoSignonPacket(func(m *dota.CDemoSignonPacket) error {
	//	return addFilteredMessage(messages, "CDemoSignonPacket", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	// })

	parser.Callbacks.OnCDemoConsoleCmd(func(m *dota.CDemoConsoleCmd) error {
		return addFilteredMessage(messages, "CDemoConsoleCmd", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})

	// Network Messages
	parser.Callbacks.OnCNETMsg_NOP(func(m *dota.CNETMsg_NOP) error {
		return addFilteredMessage(messages, "CNETMsg_NOP", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})

	parser.Callbacks.OnCNETMsg_SplitScreenUser(func(m *dota.CNETMsg_SplitScreenUser) error {
		return addFilteredMessage(messages, "CNETMsg_SplitScreenUser", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})

	parser.Callbacks.OnCNETMsg_Tick(func(m *dota.CNETMsg_Tick) error {
		return addFilteredMessage(messages, "CNETMsg_Tick", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})

	parser.Callbacks.OnCNETMsg_StringCmd(func(m *dota.CNETMsg_StringCmd) error {
		return addFilteredMessage(messages, "CNETMsg_StringCmd", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})

	parser.Callbacks.OnCNETMsg_SetConVar(func(m *dota.CNETMsg_SetConVar) error {
		return addFilteredMessage(messages, "CNETMsg_SetConVar", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})

	parser.Callbacks.OnCNETMsg_SignonState(func(m *dota.CNETMsg_SignonState) error {
		return addFilteredMessage(messages, "CNETMsg_SignonState", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})

	parser.Callbacks.OnCNETMsg_SpawnGroup_Load(func(m *dota.CNETMsg_SpawnGroup_Load) error {
		return addFilteredMessage(messages, "CNETMsg_SpawnGroup_Load", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})

	parser.Callbacks.OnCNETMsg_SpawnGroup_ManifestUpdate(func(m *dota.CNETMsg_SpawnGroup_ManifestUpdate) error {
		return addFilteredMessage(messages, "CNETMsg_SpawnGroup_ManifestUpdate", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})

	parser.Callbacks.OnCNETMsg_SpawnGroup_SetCreationTick(func(m *dota.CNETMsg_SpawnGroup_SetCreationTick) error {
		return addFilteredMessage(messages, "CNETMsg_SpawnGroup_SetCreationTick", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})

	parser.Callbacks.OnCNETMsg_SpawnGroup_Unload(func(m *dota.CNETMsg_SpawnGroup_Unload) error {
		return addFilteredMessage(messages, "CNETMsg_SpawnGroup_Unload", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})

	parser.Callbacks.OnCNETMsg_SpawnGroup_LoadCompleted(func(m *dota.CNETMsg_SpawnGroup_LoadCompleted) error {
		return addFilteredMessage(messages, "CNETMsg_SpawnGroup_LoadCompleted", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})

	// SVC Messages
	parser.Callbacks.OnCSVCMsg_ServerInfo(func(m *dota.CSVCMsg_ServerInfo) error {
		return addFilteredMessage(messages, "CSVCMsg_ServerInfo", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})

	parser.Callbacks.OnCSVCMsg_FlattenedSerializer(func(m *dota.CSVCMsg_FlattenedSerializer) error {
		return addFilteredMessage(messages, "CSVCMsg_FlattenedSerializer", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})

	parser.Callbacks.OnCSVCMsg_ClassInfo(func(m *dota.CSVCMsg_ClassInfo) error {
		return addFilteredMessage(messages, "CSVCMsg_ClassInfo", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})

	parser.Callbacks.OnCSVCMsg_SetPause(func(m *dota.CSVCMsg_SetPause) error {
		return addFilteredMessage(messages, "CSVCMsg_SetPause", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})

	parser.Callbacks.OnCSVCMsg_CreateStringTable(func(m *dota.CSVCMsg_CreateStringTable) error {
		return addFilteredMessage(messages, "CSVCMsg_CreateStringTable", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})

	parser.Callbacks.OnCSVCMsg_UpdateStringTable(func(m *dota.CSVCMsg_UpdateStringTable) error {
		return addFilteredMessage(messages, "CSVCMsg_UpdateStringTable", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})

	parser.Callbacks.OnCSVCMsg_VoiceInit(func(m *dota.CSVCMsg_VoiceInit) error {
		return addFilteredMessage(messages, "CSVCMsg_VoiceInit", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})

	parser.Callbacks.OnCSVCMsg_VoiceData(func(m *dota.CSVCMsg_VoiceData) error {
		return addFilteredMessage(messages, "CSVCMsg_VoiceData", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})

	parser.Callbacks.OnCSVCMsg_Print(func(m *dota.CSVCMsg_Print) error {
		return addFilteredMessage(messages, "CSVCMsg_Print", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})

	parser.Callbacks.OnCSVCMsg_Sounds(func(m *dota.CSVCMsg_Sounds) error {
		return addFilteredMessage(messages, "CSVCMsg_Sounds", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})

	parser.Callbacks.OnCSVCMsg_SetView(func(m *dota.CSVCMsg_SetView) error {
		return addFilteredMessage(messages, "CSVCMsg_SetView", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})

	parser.Callbacks.OnCSVCMsg_ClearAllStringTables(func(m *dota.CSVCMsg_ClearAllStringTables) error {
		return addFilteredMessage(messages, "CSVCMsg_ClearAllStringTables", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})

	parser.Callbacks.OnCSVCMsg_BSPDecal(func(m *dota.CSVCMsg_BSPDecal) error {
		return addFilteredMessage(messages, "CSVCMsg_BSPDecal", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})

	parser.Callbacks.OnCSVCMsg_SplitScreen(func(m *dota.CSVCMsg_SplitScreen) error {
		return addFilteredMessage(messages, "CSVCMsg_SplitScreen", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})

	parser.Callbacks.OnCSVCMsg_PacketEntities(func(m *dota.CSVCMsg_PacketEntities) error {
		return addFilteredMessage(messages, "CSVCMsg_PacketEntities", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})

	parser.Callbacks.OnCSVCMsg_Prefetch(func(m *dota.CSVCMsg_Prefetch) error {
		return addFilteredMessage(messages, "CSVCMsg_Prefetch", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})

	parser.Callbacks.OnCSVCMsg_Menu(func(m *dota.CSVCMsg_Menu) error {
		return addFilteredMessage(messages, "CSVCMsg_Menu", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})

	parser.Callbacks.OnCSVCMsg_GetCvarValue(func(m *dota.CSVCMsg_GetCvarValue) error {
		return addFilteredMessage(messages, "CSVCMsg_GetCvarValue", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})

	parser.Callbacks.OnCSVCMsg_PacketReliable(func(m *dota.CSVCMsg_PacketReliable) error {
		return addFilteredMessage(messages, "CSVCMsg_PacketReliable", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})

	parser.Callbacks.OnCSVCMsg_UserMessage(func(m *dota.CSVCMsg_UserMessage) error {
		return addFilteredMessage(messages, "CSVCMsg_UserMessage", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})

	// User Messages
	parser.Callbacks.OnCUserMessageCurrentTimescale(func(m *dota.CUserMessageCurrentTimescale) error {
		return addFilteredMessage(messages, "CUserMessageCurrentTimescale", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})

	parser.Callbacks.OnCUserMessageDesiredTimescale(func(m *dota.CUserMessageDesiredTimescale) error {
		return addFilteredMessage(messages, "CUserMessageDesiredTimescale", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})

	parser.Callbacks.OnCUserMessageFade(func(m *dota.CUserMessageFade) error {
		return addFilteredMessage(messages, "CUserMessageFade", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})

	parser.Callbacks.OnCUserMessageGameTitle(func(m *dota.CUserMessageGameTitle) error {
		return addFilteredMessage(messages, "CUserMessageGameTitle", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})

	parser.Callbacks.OnCUserMessageHudMsg(func(m *dota.CUserMessageHudMsg) error {
		return addFilteredMessage(messages, "CUserMessageHudMsg", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})

	parser.Callbacks.OnCUserMessageHudText(func(m *dota.CUserMessageHudText) error {
		return addFilteredMessage(messages, "CUserMessageHudText", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})

	parser.Callbacks.OnCUserMessageRequestState(func(m *dota.CUserMessageRequestState) error {
		return addFilteredMessage(messages, "CUserMessageRequestState", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})

	parser.Callbacks.OnCUserMessageRumble(func(m *dota.CUserMessageRumble) error {
		return addFilteredMessage(messages, "CUserMessageRumble", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})

	parser.Callbacks.OnCUserMessageSayText(func(m *dota.CUserMessageSayText) error {
		return addFilteredMessage(messages, "CUserMessageSayText", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})

	parser.Callbacks.OnCUserMessageSayText2(func(m *dota.CUserMessageSayText2) error {
		return addFilteredMessage(messages, "CUserMessageSayText2", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})

	parser.Callbacks.OnCUserMessageShake(func(m *dota.CUserMessageShake) error {
		return addFilteredMessage(messages, "CUserMessageShake", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})

	parser.Callbacks.OnCUserMessageTextMsg(func(m *dota.CUserMessageTextMsg) error {
		return addFilteredMessage(messages, "CUserMessageTextMsg", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})

	parser.Callbacks.OnCUserMessageScreenTilt(func(m *dota.CUserMessageScreenTilt) error {
		return addFilteredMessage(messages, "CUserMessageScreenTilt", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})

	parser.Callbacks.OnCUserMessageVoiceMask(func(m *dota.CUserMessageVoiceMask) error {
		return addFilteredMessage(messages, "CUserMessageVoiceMask", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})

	parser.Callbacks.OnCUserMessageSendAudio(func(m *dota.CUserMessageSendAudio) error {
		return addFilteredMessage(messages, "CUserMessageSendAudio", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})

	parser.Callbacks.OnCUserMessageAmmoDenied(func(m *dota.CUserMessageAmmoDenied) error {
		return addFilteredMessage(messages, "CUserMessageAmmoDenied", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})

	parser.Callbacks.OnCUserMessageShowMenu(func(m *dota.CUserMessageShowMenu) error {
		return addFilteredMessage(messages, "CUserMessageShowMenu", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})

	parser.Callbacks.OnCUserMessageCreditsMsg(func(m *dota.CUserMessageCreditsMsg) error {
		return addFilteredMessage(messages, "CUserMessageCreditsMsg", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})

	// DOTA User Messages that were already implemented
	parser.Callbacks.OnCDOTAUserMsg_AIDebugLine(func(m *dota.CDOTAUserMsg_AIDebugLine) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_AIDebugLine", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})

	parser.Callbacks.OnCDOTAUserMsg_ChatEvent(func(m *dota.CDOTAUserMsg_ChatEvent) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_ChatEvent", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})

	parser.Callbacks.OnCDOTAUserMsg_CombatHeroPositions(func(m *dota.CDOTAUserMsg_CombatHeroPositions) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_CombatHeroPositions", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})

	parser.Callbacks.OnCDOTAUserMsg_CombatLogBulkData(func(m *dota.CDOTAUserMsg_CombatLogBulkData) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_CombatLogBulkData", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})

	parser.Callbacks.OnCDOTAUserMsg_CreateLinearProjectile(func(m *dota.CDOTAUserMsg_CreateLinearProjectile) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_CreateLinearProjectile", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})

	// Continue with remaining implemented callbacks...
	setupRemainingDOTACallbacks(parser, messages, filter, maxMsgs)

	// Special case: CDOTAMatchMetadataFile
	parser.Callbacks.OnCDOTAMatchMetadataFile(func(m *dota.CDOTAMatchMetadataFile) error {
		return addFilteredMessage(messages, "CDOTAMatchMetadataFile", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
}

// setupRemainingDOTACallbacks handles remaining already-implemented DOTA callbacks
func setupRemainingDOTACallbacks(parser *manta.Parser, messages *[]MessageEvent, filter string, maxMsgs int) {
	// Continue with remaining implemented callbacks...
	parser.Callbacks.OnCDOTAUserMsg_DestroyLinearProjectile(func(m *dota.CDOTAUserMsg_DestroyLinearProjectile) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_DestroyLinearProjectile", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	// ... and so on for all remaining already-implemented callbacks
}

// addFilteredMessage adds a message if it passes the filter and limit checks
func addFilteredMessage(messages *[]MessageEvent, msgType string, tick, netTick uint32, data interface{}, filter string, maxMsgs int) error {
	// Check max messages limit
	if maxMsgs > 0 && len(*messages) >= maxMsgs {
		return nil
	}
	
	// Apply filter if specified
	if filter != "" && !strings.Contains(msgType, filter) {
		return nil
	}
	
	*messages = append(*messages, MessageEvent{
		Type:      msgType,
		Tick:      tick,
		NetTick:   netTick,
		Data:      data,
		Timestamp: time.Now().UnixMilli(),
	})
	
	return nil
}

// marshalAndReturnUniversal converts result to JSON and returns as C string
func marshalAndReturnUniversal(result *UniversalParseResult) *C.char {
	jsonResult, err := json.Marshal(result)
	if err != nil {
		errorResult := &UniversalParseResult{
			Success: false,
			Error:   fmt.Sprintf("Error marshaling result: %v", err),
		}
		jsonResult, _ = json.Marshal(errorResult)
	}
	
	cStr := C.CString(string(jsonResult))
	return cStr
}
