# API Reference

??? info "AI Summary"
    Complete API documentation for Python Manta. The main class is `Parser` which provides a unified `parse()` method with collectors for different data types. Data is returned as Pydantic models (`HeaderInfo`, `GameInfo`, `ParseResult`, etc.) for type safety and easy serialization. Main usage: `Parser("match.dem").parse(header=True, game_info=True)`.

---

## Overview

Python Manta provides a single main class and several data models:

### Main Class

| Class | Description |
|-------|-------------|
| [`Parser`](parser) | Main parser class with unified `parse()` method |

### Data Models

| Model | Description |
|-------|-------------|
| [`ParseResult`](parser#parseresult) | Result from `parse()` containing all collected data |
| [`HeaderInfo`](models#headerinfo) | Demo file header metadata |
| [`GameInfo`](models#gameinfo) | Game information (draft, players, teams) |
| [`DraftEvent`](models#draftevent) | Single pick/ban event |
| [`PlayerInfo`](models#playerinfo) | Player information from match |
| [`MessagesResult`](parser#messagesresult) | Messages parsing results |
| [`MessageEvent`](parser#messageevent) | Single message from replay |

---

## Quick Reference

```python
from python_manta import Parser

# Create parser for a demo file
parser = Parser("match.dem")

# Parse header only
result = parser.parse(header=True)
print(f"Map: {result.header.map_name}")

# Parse multiple data types in single pass
result = parser.parse(header=True, game_info=True)
print(f"Map: {result.header.map_name}")
print(f"Match ID: {result.game_info.match_id}")

# Parse messages with filtering
result = parser.parse(messages={
    "filter": "CDOTAUserMsg_ChatMessage",
    "max_messages": 100
})
for msg in result.messages.messages:
    print(f"[{msg.tick}] {msg.data}")
```

---

## Collector Options

The `parse()` method accepts these collector options:

| Collector | Type | Description |
|-----------|------|-------------|
| `header` | `bool` | Enable header parsing |
| `game_info` | `bool` | Enable game info parsing (draft, players, teams) |
| `messages` | `bool` or `dict` | Enable message parsing with optional filter |

### Message Options

When using `messages`, you can pass a dictionary with:

| Key | Type | Description |
|-----|------|-------------|
| `filter` | `str` | Substring match for message types |
| `max_messages` | `int` | Maximum messages to capture |

```python
# All messages (limited)
result = parser.parse(messages={"max_messages": 100})

# Filtered messages
result = parser.parse(messages={"filter": "Chat", "max_messages": 50})
```
