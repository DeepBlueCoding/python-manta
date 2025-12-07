package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"log"
	"os"
	"path/filepath"
	"strings"
	"time"

	"github.com/dotabuff/manta"
	"github.com/dotabuff/manta/dota"
)

// MessageEvent represents any Manta message with metadata (local copy for standalone tool)
type MessageEvent struct {
	Type    string      `json:"type"`
	Tick    uint32      `json:"tick"`
	NetTick uint32      `json:"net_tick"`
	Data    interface{} `json:"data"`
}

type callbackReport struct {
	Callback  string         `json:"callback"`
	Success   bool           `json:"success"`
	Error     string         `json:"error,omitempty"`
	Count     int            `json:"count"`
	ParseTime string         `json:"parse_time"`
	Messages  []MessageEvent `json:"messages"`
}

type parityReport struct {
	Replay      string                    `json:"replay"`
	GeneratedAt string                    `json:"generated_at"`
	Limit       int                       `json:"limit"`
	Callbacks   map[string]callbackReport `json:"callbacks"`
}

func main() {
	log.SetFlags(0)

	var replayPath string
	var callbackCSV string
	var limit int
	var outputPath string

	flag.StringVar(&replayPath, "replay", "", "Path to replay (.dem) file")
	flag.StringVar(&callbackCSV, "callbacks", "CDemoFileHeader,CDOTAUserMsg_ChatMessage,CDOTAUserMsg_LocationPing,CNETMsg_Tick,CSVCMsg_ServerInfo", "Comma-separated list of callbacks to capture")
	flag.IntVar(&limit, "limit", 10, "Maximum messages per callback (0 for all)")
	flag.StringVar(&outputPath, "output", "", "Optional output file for JSON report")
	flag.Parse()

	if replayPath == "" {
		log.Fatalf("--replay path is required")
	}

	replayPath = filepath.Clean(replayPath)
	if !filepath.IsAbs(replayPath) {
		replayAbs, err := filepath.Abs(replayPath)
		if err != nil {
			log.Fatalf("failed to resolve replay path: %v", err)
		}
		replayPath = replayAbs
	}

	if info, err := os.Stat(replayPath); err != nil {
		log.Fatalf("unable to stat replay: %v", err)
	} else if info.IsDir() {
		log.Fatalf("replay path %s is a directory", replayPath)
	}

	callbackList := parseCallbacks(callbackCSV)
	if len(callbackList) == 0 {
		log.Fatalf("no callbacks specified")
	}

	report := parityReport{
		Replay:      replayPath,
		GeneratedAt: time.Now().UTC().Format(time.RFC3339),
		Limit:       limit,
		Callbacks:   make(map[string]callbackReport),
	}

	for _, cb := range callbackList {
		start := time.Now()
		messages, err := runUniversal(replayPath, cb, limit)
		if err != nil {
			report.Callbacks[cb] = callbackReport{
				Callback:  cb,
				Success:   false,
				Error:     err.Error(),
				ParseTime: time.Since(start).String(),
			}
			continue
		}

		report.Callbacks[cb] = callbackReport{
			Callback:  cb,
			Success:   true,
			Count:     len(messages),
			ParseTime: time.Since(start).String(),
			Messages:  messages,
		}
	}

	payload, err := json.MarshalIndent(report, "", "  ")
	if err != nil {
		log.Fatalf("failed to marshal report: %v", err)
	}

	if outputPath != "" {
		if err := os.WriteFile(outputPath, payload, 0o644); err != nil {
			log.Fatalf("failed to write report: %v", err)
		}
		fmt.Println(outputPath)
		return
	}

	fmt.Println(string(payload))
}

func parseCallbacks(csv string) []string {
	parts := strings.Split(csv, ",")
	callbacks := make([]string, 0, len(parts))
	seen := make(map[string]struct{})
	for _, part := range parts {
		trimmed := strings.TrimSpace(part)
		if trimmed == "" {
			continue
		}
		if _, ok := seen[trimmed]; ok {
			continue
		}
		seen[trimmed] = struct{}{}
		callbacks = append(callbacks, trimmed)
	}
	return callbacks
}

// runUniversal parses the replay and captures messages matching the filter
func runUniversal(filePath string, filter string, maxMessages int) ([]MessageEvent, error) {
	file, err := os.Open(filePath)
	if err != nil {
		return nil, fmt.Errorf("error opening file: %w", err)
	}
	defer file.Close()

	parser, err := manta.NewStreamParser(file)
	if err != nil {
		return nil, fmt.Errorf("error creating parser: %w", err)
	}

	messages := make([]MessageEvent, 0)
	setupCallbacks(parser, &messages, filter, maxMessages)

	if err := parser.Start(); err != nil {
		return nil, fmt.Errorf("error parsing file: %w", err)
	}

	if maxMessages > 0 && len(messages) > maxMessages {
		messages = messages[:maxMessages]
	}

	return messages, nil
}

// addFilteredMessage adds a message if it passes the filter and limit checks
func addFilteredMessage(messages *[]MessageEvent, msgType string, tick, netTick uint32, data interface{}, filter string, maxMsgs int) error {
	if maxMsgs > 0 && len(*messages) >= maxMsgs {
		return nil
	}
	if filter != "" && !strings.Contains(msgType, filter) {
		return nil
	}
	*messages = append(*messages, MessageEvent{
		Type:    msgType,
		Tick:    tick,
		NetTick: netTick,
		Data:    data,
	})
	return nil
}

// setupCallbacks registers the callbacks needed for parity testing
func setupCallbacks(parser *manta.Parser, messages *[]MessageEvent, filter string, maxMsgs int) {
	// Demo messages
	parser.Callbacks.OnCDemoFileHeader(func(m *dota.CDemoFileHeader) error {
		return addFilteredMessage(messages, "CDemoFileHeader", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDemoFileInfo(func(m *dota.CDemoFileInfo) error {
		return addFilteredMessage(messages, "CDemoFileInfo", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDemoSyncTick(func(m *dota.CDemoSyncTick) error {
		return addFilteredMessage(messages, "CDemoSyncTick", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDemoStop(func(m *dota.CDemoStop) error {
		return addFilteredMessage(messages, "CDemoStop", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})

	// Network messages
	parser.Callbacks.OnCNETMsg_Tick(func(m *dota.CNETMsg_Tick) error {
		return addFilteredMessage(messages, "CNETMsg_Tick", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCNETMsg_SetConVar(func(m *dota.CNETMsg_SetConVar) error {
		return addFilteredMessage(messages, "CNETMsg_SetConVar", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCNETMsg_SignonState(func(m *dota.CNETMsg_SignonState) error {
		return addFilteredMessage(messages, "CNETMsg_SignonState", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})

	// SVC messages
	parser.Callbacks.OnCSVCMsg_ServerInfo(func(m *dota.CSVCMsg_ServerInfo) error {
		return addFilteredMessage(messages, "CSVCMsg_ServerInfo", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCSVCMsg_CreateStringTable(func(m *dota.CSVCMsg_CreateStringTable) error {
		return addFilteredMessage(messages, "CSVCMsg_CreateStringTable", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCSVCMsg_UpdateStringTable(func(m *dota.CSVCMsg_UpdateStringTable) error {
		return addFilteredMessage(messages, "CSVCMsg_UpdateStringTable", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCSVCMsg_ClearAllStringTables(func(m *dota.CSVCMsg_ClearAllStringTables) error {
		return addFilteredMessage(messages, "CSVCMsg_ClearAllStringTables", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCSVCMsg_PacketEntities(func(m *dota.CSVCMsg_PacketEntities) error {
		return addFilteredMessage(messages, "CSVCMsg_PacketEntities", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})

	// DOTA User Messages
	parser.Callbacks.OnCDOTAUserMsg_ChatMessage(func(m *dota.CDOTAUserMsg_ChatMessage) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_ChatMessage", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_ChatEvent(func(m *dota.CDOTAUserMsg_ChatEvent) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_ChatEvent", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_LocationPing(func(m *dota.CDOTAUserMsg_LocationPing) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_LocationPing", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_CombatLogBulkData(func(m *dota.CDOTAUserMsg_CombatLogBulkData) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_CombatLogBulkData", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_UnitEvent(func(m *dota.CDOTAUserMsg_UnitEvent) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_UnitEvent", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
	parser.Callbacks.OnCDOTAUserMsg_SpectatorPlayerClick(func(m *dota.CDOTAUserMsg_SpectatorPlayerClick) error {
		return addFilteredMessage(messages, "CDOTAUserMsg_SpectatorPlayerClick", parser.Tick, parser.NetTick, m, filter, maxMsgs)
	})
}
