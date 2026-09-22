# roblox-multi

Small CLI tool I built to manage multiple Roblox accounts and run simultaneous game instances side by side on Windows.

Roblox normally enforces a single client instance via a named mutex (`ROBLOX_singletonMutex`). This tool keeps track of account cookies, requests launch tickets from the Roblox auth API, unlocks the singleton handle when needed, and spawns instances directly via protocol URIs.

## Requirements

- Python 3.10+
- Windows 10/11 (for the multi-instance mutex unlocker; profile management works cross-platform)

## Install

```bash
git clone https://github.com/author/roblox-multi
cd roblox-multi
pip install .
```

Or run in editable mode:

```bash
pip install -e .
```

## Usage

### Add accounts

Save account session cookies under named profiles:

```bash
roblox-multi profile add main --cookie "_|WARNING:-DO-NOT-SHARE-THIS..."
roblox-multi profile add alt1 --cookie "_|WARNING:-DO-NOT-SHARE-THIS..."
```

List saved profiles and check if their session cookies are still valid:

```bash
roblox-multi profile list
```

### Launching games

Launch a place on a specific profile:

```bash
roblox-multi launch --profile main --place-id 189707
```

Launch two accounts into the same place:

```bash
roblox-multi launch --profile main --place-id 189707
roblox-multi launch --profile alt1 --place-id 189707
```

Join a specific server job:

```bash
roblox-multi launch --profile alt1 --place-id 189707 --job-id "3b98f2c2-d35a-4b92-8874-941c61831c2e"
```

### Process supervisor

Check active Roblox processes and their memory footprint:

```bash
roblox-multi ps
```

Kill all running Roblox instances:

```bash
roblox-multi kill
```

## Storage

Profiles are stored in plain JSON at `~/.config/roblox-multi/profiles.json` (or `%APPDATA%\roblox-multi\profiles.json` on Windows).

<!-- last-sync: 2026-09-22 -->
