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
)

type callbackReport struct {
	Callback  string         `json:"callback"`
	Success   bool           `json:"success"`
	Error     string         `json:"error,omitempty"`
	Count     int            `json:"count"`
	ParseTime string         `json:"parse_time"`
	Messages  []MessageEvent `json:"messages"`
}

type parityReport struct {
	Replay      string                     `json:"replay"`
	GeneratedAt string                     `json:"generated_at"`
	Limit       int                        `json:"limit"`
	Callbacks   map[string]callbackReport  `json:"callbacks"`
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
		result, err := RunUniversal(replayPath, cb, limit)
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
			Success:   result.Success,
			Count:     result.Count,
			ParseTime: time.Since(start).String(),
			Messages:  result.Messages,
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
