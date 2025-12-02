package main

/*
#include <stdlib.h>
*/
import "C"
import (
	"encoding/json"
	"fmt"
	"os"
	"unsafe"

	"github.com/dotabuff/manta"
	"github.com/dotabuff/manta/dota"
)

// HeaderInfo represents the basic demo file header information
type HeaderInfo struct {
	MapName        string `json:"map_name"`
	ServerName     string `json:"server_name"`
	ClientName     string `json:"client_name"`
	GameDirectory  string `json:"game_directory"`
	NetworkProtocol int32  `json:"network_protocol"`
	DemoFileStamp  string `json:"demo_file_stamp"`
	BuildNum       int32  `json:"build_num"`
	Game           string `json:"game"`
	ServerStartTick int32  `json:"server_start_tick"`
	Success        bool   `json:"success"`
	Error          string `json:"error,omitempty"`
}

// CHeroSelectEvent represents a pick or ban event - matches Manta naming
type CHeroSelectEvent struct {
	IsPick bool   `json:"is_pick"`    // true for pick, false for ban
	Team   uint32 `json:"team"`       // 2=Radiant, 3=Dire  
	HeroId int32  `json:"hero_id"`    // Hero ID
}

// CDotaGameInfo represents complete draft phase information - matches Manta naming
type CDotaGameInfo struct {
	PicksBans []CHeroSelectEvent `json:"picks_bans"`
	Success   bool               `json:"success"`
	Error     string             `json:"error,omitempty"`
}

// PlayerInfo represents player information from a match
type PlayerInfo struct {
	HeroName     string `json:"hero_name"`
	PlayerName   string `json:"player_name"`
	IsFakeClient bool   `json:"is_fake_client"`
	SteamID      uint64 `json:"steamid"`
	GameTeam     int32  `json:"game_team"` // 2=Radiant, 3=Dire
}

// MatchInfo represents complete match information including pro match data
type MatchInfo struct {
	// Basic match info
	MatchID      uint64 `json:"match_id"`
	GameMode     int32  `json:"game_mode"`
	GameWinner   int32  `json:"game_winner"` // 2=Radiant, 3=Dire
	LeagueID     uint32 `json:"league_id"`
	EndTime      uint32 `json:"end_time"`

	// Team info (pro matches only)
	RadiantTeamID  uint32 `json:"radiant_team_id"`
	DireTeamID     uint32 `json:"dire_team_id"`
	RadiantTeamTag string `json:"radiant_team_tag"`
	DireTeamTag    string `json:"dire_team_tag"`

	// Players
	Players []PlayerInfo `json:"players"`

	// Draft
	PicksBans []CHeroSelectEvent `json:"picks_bans"`

	// Playback info
	PlaybackTime   float32 `json:"playback_time"`
	PlaybackTicks  int32   `json:"playback_ticks"`
	PlaybackFrames int32   `json:"playback_frames"`

	Success bool   `json:"success"`
	Error   string `json:"error,omitempty"`
}

//export ParseHeader
func ParseHeader(filePath *C.char) *C.char {
	goFilePath := C.GoString(filePath)
	
	header := &HeaderInfo{
		Success: false,
	}

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

//export ParseDraft
func ParseDraft(filePath *C.char) *C.char {
	goFilePath := C.GoString(filePath)
	
	draftInfo := &CDotaGameInfo{
		Success: false,
	}

	// Open the file
	file, err := os.Open(goFilePath)
	if err != nil {
		draftInfo.Error = fmt.Sprintf("Error opening file: %v", err)
		return marshalAndReturnDraft(draftInfo)
	}
	defer file.Close()

	// Create parser
	parser, err := manta.NewStreamParser(file)
	if err != nil {
		draftInfo.Error = fmt.Sprintf("Error creating parser: %v", err)
		return marshalAndReturnDraft(draftInfo)
	}

	// Set up callback to capture draft information
	draftFound := false
	parser.Callbacks.OnCDemoFileInfo(func(m *dota.CDemoFileInfo) error {
		if m.GetGameInfo() != nil && m.GetGameInfo().GetDota() != nil {
			dotaInfo := m.GetGameInfo().GetDota()
			if dotaInfo.GetPicksBans() != nil {
				draftInfo.PicksBans = make([]CHeroSelectEvent, 0)
				
				for _, pickBan := range dotaInfo.GetPicksBans() {
					event := CHeroSelectEvent{
						IsPick: pickBan.GetIsPick(),
						Team:   pickBan.GetTeam(),
						HeroId: pickBan.GetHeroId(),
					}
					draftInfo.PicksBans = append(draftInfo.PicksBans, event)
				}
				
				draftInfo.Success = true
				draftFound = true
			}
		}
		
		// Stop parsing after getting draft info
		parser.Stop()
		return nil
	})

	// Start parsing (will stop after draft info is found)
	err = parser.Start()
	if err != nil && !draftFound {
		draftInfo.Error = fmt.Sprintf("Error parsing file: %v", err)
		return marshalAndReturnDraft(draftInfo)
	}

	if !draftFound {
		draftInfo.Error = "Draft information not found in demo file"
		return marshalAndReturnDraft(draftInfo)
	}

	return marshalAndReturnDraft(draftInfo)
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
func marshalAndReturnDraft(draftInfo *CDotaGameInfo) *C.char {
	jsonData, err := json.Marshal(draftInfo)
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
func ParseMatchInfo(filePath *C.char) *C.char {
	goFilePath := C.GoString(filePath)

	matchInfo := &MatchInfo{
		Success: false,
	}

	// Open the file
	file, err := os.Open(goFilePath)
	if err != nil {
		matchInfo.Error = fmt.Sprintf("Error opening file: %v", err)
		return marshalAndReturnMatchInfo(matchInfo)
	}
	defer file.Close()

	// Create parser
	parser, err := manta.NewStreamParser(file)
	if err != nil {
		matchInfo.Error = fmt.Sprintf("Error creating parser: %v", err)
		return marshalAndReturnMatchInfo(matchInfo)
	}

	// Set up callback to capture match information from CDemoFileInfo
	infoFound := false
	parser.Callbacks.OnCDemoFileInfo(func(m *dota.CDemoFileInfo) error {
		// Playback info
		matchInfo.PlaybackTime = m.GetPlaybackTime()
		matchInfo.PlaybackTicks = m.GetPlaybackTicks()
		matchInfo.PlaybackFrames = m.GetPlaybackFrames()

		if m.GetGameInfo() != nil && m.GetGameInfo().GetDota() != nil {
			dotaInfo := m.GetGameInfo().GetDota()

			// Basic match info
			matchInfo.MatchID = dotaInfo.GetMatchId()
			matchInfo.GameMode = dotaInfo.GetGameMode()
			matchInfo.GameWinner = dotaInfo.GetGameWinner()
			matchInfo.LeagueID = dotaInfo.GetLeagueid()
			matchInfo.EndTime = dotaInfo.GetEndTime()

			// Team info (pro matches)
			matchInfo.RadiantTeamID = dotaInfo.GetRadiantTeamId()
			matchInfo.DireTeamID = dotaInfo.GetDireTeamId()
			matchInfo.RadiantTeamTag = dotaInfo.GetRadiantTeamTag()
			matchInfo.DireTeamTag = dotaInfo.GetDireTeamTag()

			// Players
			if dotaInfo.GetPlayerInfo() != nil {
				matchInfo.Players = make([]PlayerInfo, 0, len(dotaInfo.GetPlayerInfo()))
				for _, p := range dotaInfo.GetPlayerInfo() {
					player := PlayerInfo{
						HeroName:     p.GetHeroName(),
						PlayerName:   p.GetPlayerName(),
						IsFakeClient: p.GetIsFakeClient(),
						SteamID:      p.GetSteamid(),
						GameTeam:     p.GetGameTeam(),
					}
					matchInfo.Players = append(matchInfo.Players, player)
				}
			}

			// Draft picks/bans
			if dotaInfo.GetPicksBans() != nil {
				matchInfo.PicksBans = make([]CHeroSelectEvent, 0, len(dotaInfo.GetPicksBans()))
				for _, pb := range dotaInfo.GetPicksBans() {
					event := CHeroSelectEvent{
						IsPick: pb.GetIsPick(),
						Team:   pb.GetTeam(),
						HeroId: pb.GetHeroId(),
					}
					matchInfo.PicksBans = append(matchInfo.PicksBans, event)
				}
			}

			matchInfo.Success = true
			infoFound = true
		}

		// Stop parsing after getting info
		parser.Stop()
		return nil
	})

	// Start parsing
	err = parser.Start()
	if err != nil && !infoFound {
		matchInfo.Error = fmt.Sprintf("Error parsing file: %v", err)
		return marshalAndReturnMatchInfo(matchInfo)
	}

	if !infoFound {
		matchInfo.Error = "Match information not found in demo file"
		return marshalAndReturnMatchInfo(matchInfo)
	}

	return marshalAndReturnMatchInfo(matchInfo)
}

// Helper function to marshal MatchInfo to JSON and return as C string
func marshalAndReturnMatchInfo(matchInfo *MatchInfo) *C.char {
	jsonData, err := json.Marshal(matchInfo)
	if err != nil {
		fallback := &MatchInfo{
			Success: false,
			Error:   fmt.Sprintf("JSON marshal error: %v", err),
		}
		jsonData, _ = json.Marshal(fallback)
	}

	cstr := C.CString(string(jsonData))
	return cstr
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