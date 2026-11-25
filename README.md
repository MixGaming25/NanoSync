# NanoSync

**Your music, your device.**  
A local-first Windows desktop music library manager built with Python and Tkinter to organize, tag, and prepare personal audio collections for an **iPod Nano 5th generation**.

![Platform](https://img.shields.io/badge/Platform-Windows%2010%20%7C%2011-0078D6?style=flat-square)
![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square)
![Database](https://img.shields.io/badge/Storage-Local%20SQLite-003B57?style=flat-square)
![Status](https://img.shields.io/badge/Stage-MVP%20(Library%20%26%20Tagging)-2EA44F?style=flat-square)

---

## Overview

NanoSync gives you a fast, offline desktop interface to catalogue your local music folders, inspect audio properties, edit metadata tags, embed album artwork, and export clean `.m3u8` playlists—without moving your files or relying on cloud services.

Because the iPod Nano 5th generation relies on Apple's proprietary database and device-specific validation hashes, **this initial MVP focuses strictly on library management and file preparation** before introducing direct hardware syncing.

---

## Current MVP Features

- **Recursive Library Scanning:** Scans selected folders for `.mp3`, `.m4a`, `.aac`, `.wav`, `.aiff`, and `.flac` files.
- **Local SQLite Catalogue:** Indexes your collection in `%USERPROFILE%\NanoSync\library.db` while keeping all audio files in their original directories.
- **Track & Audio Inspection:** Displays title, artist, album, year, track number, genre, duration, bitrate (`kbps`), file size (`MB`), and embedded artwork status.
- **Metadata Tag Editor:** Edit and write common tags (`Title`, `Artist`, `Album`, `Year`, `Track number`, `Genre`) directly to supported audio files via `mutagen`.
- **MP3 Cover Art Embedding:** Embed or replace front cover artwork (`JPG` / `PNG`) into MP3 files using ID3v2.3 `APIC` frames.
- **Playlist Export:** Export either a selected track or your entire sorted library as a UTF-8 `.m3u8` playlist.
- **Quick File Access:** Jump straight to any track's folder in Windows Explorer from the inspector panel.

---

## Project Structure

```text
nanosync/
├── nanosync/
│   └── app.py           # Main Tkinter GUI, SQLite database layer, and Mutagen tag handlers
├── requirements.txt     # Python dependencies (mutagen)
├── run_nanosync.bat     # One-click Windows launcher & dependency installer
└── README.md
```

---

## Requirements

- **OS:** Windows 10 or Windows 11
- **Runtime:** Python 3.10 or newer
- **Dependencies:** `mutagen>=1.47.0` *(offline after initial installation)*

---

## Getting Started

### Option 1: One-Click Launch (Recommended)
1. Install [Python for Windows](https://www.python.org/downloads/) and make sure **"Add Python to PATH"** is checked during setup.
2. Double-click **`run_nanosync.bat`** in the root folder. It will automatically install `mutagen` and launch the app.
3. Click **＋ Add music folder** and select your music directory.

### Option 2: Run via Terminal
```bash
py -m pip install -r requirements.txt
py nanosync\app.py
```

---

## Safety & Current Limitations

- **No Direct iPod Writing Yet:** This MVP does not detect or write to an iPod device.
- **Non-Destructive Scanning:** Scanning folders only reads file paths and metadata; it never moves, renames, or deletes audio files.
- **In-Place Tag Edits:** Clicking **Save tags** or **Add / replace MP3 cover** writes directly to the selected audio file. Always keep a backup of your music collection.
- **Artwork Format Support:** Cover art embedding currently supports `.mp3` files only.
- **Playlist Scope:** Exporting generates a standalone `.m3u8` file on disk rather than syncing playlists to an iPod database.

---

## Roadmap

1. **Deezer Metadata Import:** Import library and playlist metadata from Deezer *(metadata only, no audio downloads)*.
2. **Automated Metadata & Cover Lookup:** Integrate MusicBrainz matching and Cover Art Archive fetching.
3. **Lyrics Support:** Look up and embed synchronized/unsynchronized lyrics where supported.
4. **iPod Hardware Detection:** Identify connected iPod Nano 5th-gen devices and run audio compatibility checks.
5. **Safe Sync Engine:** Build a tested iPod database backend featuring automatic device backups and dry-run previews.
6. **Hardware Synchronisation:** Enable full two-way/one-way syncing after thorough verification on physical iPod Nano 5th-gen hardware.
````[cite: 1, 2, 3, 4]