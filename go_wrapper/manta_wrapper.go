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


//export FreeString  
func FreeString(str *C.char) {
	if str != nil {
		C.free(unsafe.Pointer(str))
	}
}

func main() {
	// CGO requires a main function, but we won't use it for the library
}