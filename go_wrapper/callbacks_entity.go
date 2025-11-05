package main

import (
	"github.com/dotabuff/manta"
	"github.com/dotabuff/manta/dota"
)

func setupEntityCallbacks(parser *manta.Parser, messages *[]MessageEvent, filter string, maxMsgs int) {
	parser.Callbacks.OnCEntityMessageDoSpark(func(m *dota.CEntityMessageDoSpark) error {
		return addFilteredMessage(messages, "CEntityMessageDoSpark", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCEntityMessageFixAngle(func(m *dota.CEntityMessageFixAngle) error {
		return addFilteredMessage(messages, "CEntityMessageFixAngle", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCEntityMessagePlayJingle(func(m *dota.CEntityMessagePlayJingle) error {
		return addFilteredMessage(messages, "CEntityMessagePlayJingle", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCEntityMessagePropagateForce(func(m *dota.CEntityMessagePropagateForce) error {
		return addFilteredMessage(messages, "CEntityMessagePropagateForce", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCEntityMessageRemoveAllDecals(func(m *dota.CEntityMessageRemoveAllDecals) error {
		return addFilteredMessage(messages, "CEntityMessageRemoveAllDecals", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCEntityMessageScreenOverlay(func(m *dota.CEntityMessageScreenOverlay) error {
		return addFilteredMessage(messages, "CEntityMessageScreenOverlay", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
}