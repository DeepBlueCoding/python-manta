package main

/*
#include <stdlib.h>
*/
import "C"

import (
	"encoding/json"
	"fmt"
	"os"
	"sync"
	"sync/atomic"

	"github.com/dotabuff/manta"
	"github.com/dotabuff/manta/dota"
)

// StreamHandle holds state for an active streaming session
type StreamHandle struct {
	file      *os.File
	parser    *manta.Parser
	config    StreamConfig
	events    chan StreamEvent
	done      chan struct{}
	err       error
	started   bool
	completed atomic.Bool
}

// StreamConfig specifies what events to stream
type StreamConfig struct {
	CombatLog    bool     `json:"combat_log"`
	Entities     bool     `json:"entities"`
	Messages     bool     `json:"messages"`
	GameEvents   bool     `json:"game_events"`
	Modifiers    bool     `json:"modifiers"`
	FilterTypes  []string `json:"filter_types"`
	MaxEvents    int      `json:"max_events"`
	IntervalTick int      `json:"interval_tick"`
}

// StreamEvent is a single event yielded during streaming
type StreamEvent struct {
	Kind    string      `json:"kind"`
	Tick    int         `json:"tick"`
	NetTick int         `json:"net_tick"`
	Type    string      `json:"type,omitempty"`
	Data    interface{} `json:"data"`
}

// StreamResult is returned from Next()
type StreamResult struct {
	Event   *StreamEvent `json:"event,omitempty"`
	Done    bool         `json:"done"`
	Success bool         `json:"success"`
	Error   string       `json:"error,omitempty"`
}

// Global handle storage
var (
	handles      = make(map[int64]*StreamHandle)
	handlesMutex sync.RWMutex
	nextHandleID int64
)

func getNextHandleID() int64 {
	return atomic.AddInt64(&nextHandleID, 1)
}

func storeHandle(h *StreamHandle) int64 {
	id := getNextHandleID()
	handlesMutex.Lock()
	handles[id] = h
	handlesMutex.Unlock()
	return id
}

func getHandle(id int64) *StreamHandle {
	handlesMutex.RLock()
	h := handles[id]
	handlesMutex.RUnlock()
	return h
}

func removeHandle(id int64) {
	handlesMutex.Lock()
	delete(handles, id)
	handlesMutex.Unlock()
}

//export StreamOpen
func StreamOpen(filePath *C.char, configJSON *C.char) *C.char {
	path := C.GoString(filePath)
	configStr := C.GoString(configJSON)

	// Parse config
	var config StreamConfig
	if err := json.Unmarshal([]byte(configStr), &config); err != nil {
		result := map[string]interface{}{
			"success":   false,
			"error":     fmt.Sprintf("Invalid config JSON: %v", err),
			"handle_id": int64(-1),
		}
		jsonResult, _ := json.Marshal(result)
		return C.CString(string(jsonResult))
	}

	// Open file
	file, err := os.Open(path)
	if err != nil {
		result := map[string]interface{}{
			"success":   false,
			"error":     fmt.Sprintf("Failed to open file: %v", err),
			"handle_id": int64(-1),
		}
		jsonResult, _ := json.Marshal(result)
		return C.CString(string(jsonResult))
	}

	// Create parser
	parser, err := manta.NewStreamParser(file)
	if err != nil {
		file.Close()
		result := map[string]interface{}{
			"success":   false,
			"error":     fmt.Sprintf("Failed to create parser: %v", err),
			"handle_id": int64(-1),
		}
		jsonResult, _ := json.Marshal(result)
		return C.CString(string(jsonResult))
	}

	// Create handle
	handle := &StreamHandle{
		file:   file,
		parser: parser,
		config: config,
		events: make(chan StreamEvent, 1000), // Buffer for events
		done:   make(chan struct{}),
	}

	// Store handle
	handleID := storeHandle(handle)

	// Start parsing in goroutine
	go runStreamParser(handle)

	result := map[string]interface{}{
		"success":   true,
		"handle_id": handleID,
	}
	jsonResult, _ := json.Marshal(result)
	return C.CString(string(jsonResult))
}

func runStreamParser(h *StreamHandle) {
	defer func() {
		h.completed.Store(true)
		close(h.events)
	}()

	eventCount := 0
	maxEvents := h.config.MaxEvents
	if maxEvents <= 0 {
		maxEvents = 1000000 // Default limit
	}

	// Register callbacks based on config
	if h.config.CombatLog {
		h.parser.Callbacks.OnCMsgDOTACombatLogEntry(func(m *dota.CMsgDOTACombatLogEntry) error {
			if eventCount >= maxEvents {
				return nil
			}

			entry := map[string]interface{}{
				"type":          m.GetType(),
				"target_name":   m.GetTargetName(),
				"attacker_name": m.GetAttackerName(),
				"damage":        m.GetValue(),
				"health":        m.GetHealth(),
				"timestamp":     m.GetTimestamp(),
			}

			select {
			case h.events <- StreamEvent{
				Kind:    "combat_log",
				Tick:    int(h.parser.Tick),
				NetTick: int(h.parser.NetTick),
				Type:    "CMsgDOTACombatLogEntry",
				Data:    entry,
			}:
				eventCount++
			case <-h.done:
				return fmt.Errorf("stream closed")
			}
			return nil
		})
	}

	if h.config.Messages {
		// Register common message callbacks
		registerStreamMessageCallback(h, &eventCount, maxEvents)
	}

	if h.config.GameEvents {
		h.parser.Callbacks.OnCMsgSource1LegacyGameEvent(func(m *dota.CMsgSource1LegacyGameEvent) error {
			if eventCount >= maxEvents {
				return nil
			}

			select {
			case h.events <- StreamEvent{
				Kind:    "game_event",
				Tick:    int(h.parser.Tick),
				NetTick: int(h.parser.NetTick),
				Type:    m.GetEventName(),
				Data:    m,
			}:
				eventCount++
			case <-h.done:
				return fmt.Errorf("stream closed")
			}
			return nil
		})
	}

	// Start parsing
	h.err = h.parser.Start()
}

func registerStreamMessageCallback(h *StreamHandle, eventCount *int, maxEvents int) {
	// Register file header
	h.parser.Callbacks.OnCDemoFileHeader(func(m *dota.CDemoFileHeader) error {
		if *eventCount >= maxEvents {
			return nil
		}

		select {
		case h.events <- StreamEvent{
			Kind:    "message",
			Tick:    int(h.parser.Tick),
			NetTick: int(h.parser.NetTick),
			Type:    "CDemoFileHeader",
			Data:    m,
		}:
			*eventCount++
		case <-h.done:
			return fmt.Errorf("stream closed")
		}
		return nil
	})

	// Register chat messages
	h.parser.Callbacks.OnCDOTAUserMsg_ChatMessage(func(m *dota.CDOTAUserMsg_ChatMessage) error {
		if *eventCount >= maxEvents {
			return nil
		}

		select {
		case h.events <- StreamEvent{
			Kind:    "message",
			Tick:    int(h.parser.Tick),
			NetTick: int(h.parser.NetTick),
			Type:    "CDOTAUserMsg_ChatMessage",
			Data:    m,
		}:
			*eventCount++
		case <-h.done:
			return fmt.Errorf("stream closed")
		}
		return nil
	})
}

//export StreamNext
func StreamNext(handleID C.longlong) *C.char {
	h := getHandle(int64(handleID))
	if h == nil {
		result := StreamResult{
			Done:    true,
			Success: false,
			Error:   "Invalid handle",
		}
		jsonResult, _ := json.Marshal(result)
		return C.CString(string(jsonResult))
	}

	// Try to get next event
	select {
	case event, ok := <-h.events:
		if !ok {
			// Channel closed, parsing complete
			result := StreamResult{
				Done:    true,
				Success: true,
			}
			if h.err != nil {
				result.Success = false
				result.Error = h.err.Error()
			}
			jsonResult, _ := json.Marshal(result)
			return C.CString(string(jsonResult))
		}

		result := StreamResult{
			Event:   &event,
			Done:    false,
			Success: true,
		}
		jsonResult, _ := json.Marshal(result)
		return C.CString(string(jsonResult))

	default:
		// No event available yet, check if done
		if h.completed.Load() {
			result := StreamResult{
				Done:    true,
				Success: true,
			}
			if h.err != nil {
				result.Success = false
				result.Error = h.err.Error()
			}
			jsonResult, _ := json.Marshal(result)
			return C.CString(string(jsonResult))
		}

		// Still parsing, no event ready
		result := StreamResult{
			Done:    false,
			Success: true,
		}
		jsonResult, _ := json.Marshal(result)
		return C.CString(string(jsonResult))
	}
}

//export StreamClose
func StreamClose(handleID C.longlong) *C.char {
	h := getHandle(int64(handleID))
	if h == nil {
		result := map[string]interface{}{
			"success": false,
			"error":   "Invalid handle",
		}
		jsonResult, _ := json.Marshal(result)
		return C.CString(string(jsonResult))
	}

	// Signal parser to stop
	close(h.done)

	// Close file
	if h.file != nil {
		h.file.Close()
	}

	// Remove handle
	removeHandle(int64(handleID))

	result := map[string]interface{}{
		"success": true,
	}
	jsonResult, _ := json.Marshal(result)
	return C.CString(string(jsonResult))
}

// Note: Using dota.* types directly in callbacks
