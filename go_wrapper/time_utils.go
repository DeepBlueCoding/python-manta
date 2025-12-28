package main

import "fmt"

const TicksPerSecond float32 = 30.0

// FormatGameTime converts seconds to game clock format.
// Examples: -40.0 → "-0:40", 187.0 → "3:07", 0.0 → "0:00"
func FormatGameTime(seconds float32) string {
	negative := seconds < 0
	abs := seconds
	if negative {
		abs = -seconds
	}
	mins := int(abs) / 60
	secs := int(abs) % 60
	if negative {
		return fmt.Sprintf("-%d:%02d", mins, secs)
	}
	return fmt.Sprintf("%d:%02d", mins, secs)
}

// GameTimeToTick converts game_time (seconds from horn) to tick.
func GameTimeToTick(gameTime float32, gameStartTick uint32) uint32 {
	return uint32(int32(gameStartTick) + int32(gameTime*TicksPerSecond))
}

// TickToGameTime converts tick to game_time (seconds from horn).
func TickToGameTime(tick uint32, gameStartTick uint32) float32 {
	return float32(int32(tick)-int32(gameStartTick)) / TicksPerSecond
}

// TickToReplayTime converts tick to replay time (seconds from replay start).
func TickToReplayTime(tick uint32) float32 {
	return float32(tick) / TicksPerSecond
}
