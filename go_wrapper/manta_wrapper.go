package main

/*
#include <stdlib.h>
*/
import "C"
import (
	"encoding/json"
	"fmt"
	"os"
	"regexp"
	"strconv"
	"unsafe"

	"github.com/dotabuff/manta"
	"github.com/dotabuff/manta/dota"
)

// gameBuildRegexp extracts game build from game_directory (e.g., 6559 from /dota_v6559/)
var gameBuildRegexp = regexp.MustCompile(`/dota_v(\d+)/`)

// extractGameBuild extracts the game build number from a game directory path
func extractGameBuild(gameDir string) int32 {
	matches := gameBuildRegexp.FindStringSubmatch(gameDir)
	if len(matches) >= 2 {
		if build, err := strconv.ParseInt(matches[1], 10, 32); err == nil {
			return int32(build)
		}
	}
	return 0
}

// HeaderInfo represents the basic demo file header information
type HeaderInfo struct {
	MapName         string `json:"map_name"`
	ServerName      string `json:"server_name"`
	ClientName      string `json:"client_name"`
	GameDirectory   string `json:"game_directory"`
	NetworkProtocol int32  `json:"network_protocol"`
	DemoFileStamp   string `json:"demo_file_stamp"`
	BuildNum        int32  `json:"build_num"`
	GameBuild       int32  `json:"game_build"` // Extracted from game_directory (e.g., 6559 from /dota_v6559/)
	Game            string `json:"game"`
	ServerStartTick int32  `json:"server_start_tick"`
	Success         bool   `json:"success"`
	Error           string `json:"error,omitempty"`
}

// CHeroSelectEvent represents a pick or ban event - matches Manta naming
type CHeroSelectEvent struct {
	IsPick bool   `json:"is_pick"`    // true for pick, false for ban
	Team   uint32 `json:"team"`       // 2=Radiant, 3=Dire  
	HeroId int32  `json:"hero_id"`    // Hero ID
}

// CDotaGameInfo represents complete draft phase information - matches Manta naming
// CPlayerInfo matches Manta's CGameInfo.CDotaGameInfo.CPlayerInfo
type CPlayerInfo struct {
	HeroName     string `json:"hero_name"`
	PlayerName   string `json:"player_name"`
	IsFakeClient bool   `json:"is_fake_client"`
	SteamID      uint64 `json:"steamid"`
	GameTeam     int32  `json:"game_team"` // 2=Radiant, 3=Dire
}

// CDotaGameInfo matches Manta's CGameInfo.CDotaGameInfo
type CDotaGameInfo struct {
	// Basic match info
	MatchID    uint64 `json:"match_id"`
	GameMode   int32  `json:"game_mode"`
	GameWinner int32  `json:"game_winner"` // 2=Radiant, 3=Dire
	LeagueID   uint32 `json:"leagueid"`    // Manta uses 'leagueid'
	EndTime    uint32 `json:"end_time"`

	// Team info (pro matches only)
	RadiantTeamID  uint32 `json:"radiant_team_id"`
	DireTeamID     uint32 `json:"dire_team_id"`
	RadiantTeamTag string `json:"radiant_team_tag"`
	DireTeamTag    string `json:"dire_team_tag"`

	// Players - Manta uses 'player_info'
	PlayerInfo []CPlayerInfo `json:"player_info"`

	// Draft
	PicksBans []CHeroSelectEvent `json:"picks_bans"`

	// Playback info (from CDemoFileInfo parent)
	PlaybackTime   float32 `json:"playback_time"`
	PlaybackTicks  int32   `json:"playback_ticks"`
	PlaybackFrames int32   `json:"playback_frames"`

	Success bool   `json:"success"`
	Error   string `json:"error,omitempty"`
}

//export ParseHeader
func ParseHeader(filePath *C.char) (result *C.char) {
	goFilePath := C.GoString(filePath)

	header := &HeaderInfo{
		Success: false,
	}

	// Recover from any panics in manta library
	defer func() {
		if r := recover(); r != nil {
			header.Success = false
			header.Error = fmt.Sprintf("panic during parsing: %v", r)
			result = marshalAndReturn(header)
		}
	}()

	// Open the file
	file, err := os.Open(goFilePath)
	if err != nil {
		header.Error = fmt.Sprintf("Error opening file: %v", err)
		return marshalAndReturn(header)
	}
	defer file.Close()

	// Create parser
	parser, err := manta.NewStreamParser(file)
	if err != nil {
		header.Error = fmt.Sprintf("Error creating parser: %v", err)
		return marshalAndReturn(header)
	}

	// Set up header callback to capture the data
	headerFound := false
	parser.Callbacks.OnCDemoFileHeader(func(m *dota.CDemoFileHeader) error {
		header.MapName = m.GetMapName()
		header.ServerName = m.GetServerName()
		header.ClientName = m.GetClientName()
		header.GameDirectory = m.GetGameDirectory()
		header.NetworkProtocol = m.GetNetworkProtocol()
		header.DemoFileStamp = m.GetDemoFileStamp()
		header.BuildNum = m.GetBuildNum()
		header.GameBuild = extractGameBuild(m.GetGameDirectory())
		header.Game = m.GetGame()
		header.ServerStartTick = m.GetServerStartTick()
		header.Success = true
		headerFound = true

		// Stop parsing after getting header
		parser.Stop()
		return nil
	})

	// Start parsing (will stop after header is found)
	err = parser.Start()
	if err != nil && !headerFound {
		header.Error = fmt.Sprintf("Error parsing file: %v", err)
		return marshalAndReturn(header)
	}

	if !headerFound {
		header.Error = "Header not found in demo file"
		return marshalAndReturn(header)
	}

	return marshalAndReturn(header)
}

// Helper function to marshal HeaderInfo to JSON and return as C string
func marshalAndReturn(header *HeaderInfo) *C.char {
	jsonData, err := json.Marshal(header)
	if err != nil {
		// Fallback error response
		fallback := &HeaderInfo{
			Success: false,
			Error:   fmt.Sprintf("JSON marshal error: %v", err),
		}
		jsonData, _ = json.Marshal(fallback)
	}

	// Allocate C string that Python can free
	cstr := C.CString(string(jsonData))
	return cstr
}

// Helper function to marshal CDotaGameInfo to JSON and return as C string
func marshalAndReturnGameInfo(gameInfo *CDotaGameInfo) *C.char {
	jsonData, err := json.Marshal(gameInfo)
	if err != nil {
		// Fallback error response
		fallback := &CDotaGameInfo{
			Success: false,
			Error:   fmt.Sprintf("JSON marshal error: %v", err),
		}
		jsonData, _ = json.Marshal(fallback)
	}

	// Allocate C string - caller must free with FreeString
	cstr := C.CString(string(jsonData))
	return cstr
}

//export ParseMatchInfo
func ParseMatchInfo(filePath *C.char) (result *C.char) {
	goFilePath := C.GoString(filePath)

	gameInfo := &CDotaGameInfo{
		Success: false,
	}

	// Recover from any panics in manta library
	defer func() {
		if r := recover(); r != nil {
			gameInfo.Success = false
			gameInfo.Error = fmt.Sprintf("panic during parsing: %v", r)
			result = marshalAndReturnGameInfo(gameInfo)
		}
	}()

	// Open the file
	file, err := os.Open(goFilePath)
	if err != nil {
		gameInfo.Error = fmt.Sprintf("Error opening file: %v", err)
		return marshalAndReturnGameInfo(gameInfo)
	}
	defer file.Close()

	// Create parser
	parser, err := manta.NewStreamParser(file)
	if err != nil {
		gameInfo.Error = fmt.Sprintf("Error creating parser: %v", err)
		return marshalAndReturnGameInfo(gameInfo)
	}

	// Set up callback to capture game information from CDemoFileInfo
	infoFound := false
	parser.Callbacks.OnCDemoFileInfo(func(m *dota.CDemoFileInfo) error {
		// Playback info (from CDemoFileInfo)
		gameInfo.PlaybackTime = m.GetPlaybackTime()
		gameInfo.PlaybackTicks = m.GetPlaybackTicks()
		gameInfo.PlaybackFrames = m.GetPlaybackFrames()

		if m.GetGameInfo() != nil && m.GetGameInfo().GetDota() != nil {
			dotaInfo := m.GetGameInfo().GetDota()

			// Basic match info
			gameInfo.MatchID = dotaInfo.GetMatchId()
			gameInfo.GameMode = dotaInfo.GetGameMode()
			gameInfo.GameWinner = dotaInfo.GetGameWinner()
			gameInfo.LeagueID = dotaInfo.GetLeagueid()
			gameInfo.EndTime = dotaInfo.GetEndTime()

			// Team info (pro matches)
			gameInfo.RadiantTeamID = dotaInfo.GetRadiantTeamId()
			gameInfo.DireTeamID = dotaInfo.GetDireTeamId()
			gameInfo.RadiantTeamTag = dotaInfo.GetRadiantTeamTag()
			gameInfo.DireTeamTag = dotaInfo.GetDireTeamTag()

			// Players
			if dotaInfo.GetPlayerInfo() != nil {
				gameInfo.PlayerInfo = make([]CPlayerInfo, 0, len(dotaInfo.GetPlayerInfo()))
				for _, p := range dotaInfo.GetPlayerInfo() {
					player := CPlayerInfo{
						HeroName:     p.GetHeroName(),
						PlayerName:   p.GetPlayerName(),
						IsFakeClient: p.GetIsFakeClient(),
						SteamID:      p.GetSteamid(),
						GameTeam:     p.GetGameTeam(),
					}
					gameInfo.PlayerInfo = append(gameInfo.PlayerInfo, player)
				}
			}

			// Draft picks/bans
			if dotaInfo.GetPicksBans() != nil {
				gameInfo.PicksBans = make([]CHeroSelectEvent, 0, len(dotaInfo.GetPicksBans()))
				for _, pb := range dotaInfo.GetPicksBans() {
					event := CHeroSelectEvent{
						IsPick: pb.GetIsPick(),
						Team:   pb.GetTeam(),
						HeroId: pb.GetHeroId(),
					}
					gameInfo.PicksBans = append(gameInfo.PicksBans, event)
				}
			}

			gameInfo.Success = true
			infoFound = true
		}

		// Stop parsing after getting info
		parser.Stop()
		return nil
	})

	// Start parsing
	err = parser.Start()
	if err != nil && !infoFound {
		gameInfo.Error = fmt.Sprintf("Error parsing file: %v", err)
		return marshalAndReturnGameInfo(gameInfo)
	}

	if !infoFound {
		gameInfo.Error = "Game information not found in demo file"
		return marshalAndReturnGameInfo(gameInfo)
	}

	return marshalAndReturnGameInfo(gameInfo)
}

//export FreeString
func FreeString(str *C.char) {
	if str != nil {
		C.free(unsafe.Pointer(str))
	}
}

func main() {
	// CGO requires a main function, but we won't use it for the library
}