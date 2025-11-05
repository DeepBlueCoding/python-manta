package main

import (
	"github.com/dotabuff/manta"
	"github.com/dotabuff/manta/dota"
)

// Demo message callbacks
func setupDemoCallbacks(parser *manta.Parser, messages *[]MessageEvent, filter string, maxMsgs int) {
	// CDemoAnimationData
	parser.Callbacks.OnCDemoAnimationData(func(m *dota.CDemoAnimationData) error {
		return addFilteredMessage(messages, "CDemoAnimationData", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})

	// CDemoAnimationHeader
	parser.Callbacks.OnCDemoAnimationHeader(func(m *dota.CDemoAnimationHeader) error {
		return addFilteredMessage(messages, "CDemoAnimationHeader", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})

	// CDemoCustomData
	parser.Callbacks.OnCDemoCustomData(func(m *dota.CDemoCustomData) error {
		return addFilteredMessage(messages, "CDemoCustomData", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})

	// CDemoCustomDataCallbacks
	parser.Callbacks.OnCDemoCustomDataCallbacks(func(m *dota.CDemoCustomDataCallbacks) error {
		return addFilteredMessage(messages, "CDemoCustomDataCallbacks", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})

	// CDemoFullPacket
	parser.Callbacks.OnCDemoFullPacket(func(m *dota.CDemoFullPacket) error {
		return addFilteredMessage(messages, "CDemoFullPacket", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})

	// CDemoRecovery
	parser.Callbacks.OnCDemoRecovery(func(m *dota.CDemoRecovery) error {
		return addFilteredMessage(messages, "CDemoRecovery", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})

	// CDemoSaveGame
	parser.Callbacks.OnCDemoSaveGame(func(m *dota.CDemoSaveGame) error {
		return addFilteredMessage(messages, "CDemoSaveGame", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})

	// CDemoSpawnGroups
	parser.Callbacks.OnCDemoSpawnGroups(func(m *dota.CDemoSpawnGroups) error {
		return addFilteredMessage(messages, "CDemoSpawnGroups", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})

	// CDemoUserCmd
	parser.Callbacks.OnCDemoUserCmd(func(m *dota.CDemoUserCmd) error {
		return addFilteredMessage(messages, "CDemoUserCmd", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
}