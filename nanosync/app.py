from __future__ import annotations

import os
import sqlite3
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path

from mutagen import File
from mutagen.id3 import ID3, ID3NoHeaderError, TIT2, TPE1, TALB, TDRC, TRCK, TCON, APIC

APP_DIR = Path.home() / "NanoSync"
DB_PATH = APP_DIR / "library.db"
AUDIO_EXTENSIONS = {".mp3", ".m4a", ".aac", ".wav", ".aiff", ".flac"}


def db():
    APP_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS tracks (
            path TEXT PRIMARY KEY,
            title TEXT, artist TEXT, album TEXT, year TEXT,
            track_no TEXT, genre TEXT, duration REAL,
            bitrate INTEGER, size INTEGER, has_art INTEGER
        )
    """)
    return conn


def tag_value(tags, key):
    try:
        value = tags.get(key)
        if value is None:
            return ""
        if hasattr(value, "text"):
            return str(value.text[0]) if value.text else ""
        return str(value[0]) if isinstance(value, list) else str(value)
    except Exception:
        return ""


def read_track(path: Path):
    audio = File(path, easy=True)
    raw = File(path)
    info = getattr(raw, "info", None)
    tags = audio.tags if audio else {}
    return {
        "path": str(path),
        "title": tag_value(tags, "title") or path.stem,
        "artist": tag_value(tags, "artist"),
        "album": tag_value(tags, "album"),
        "year": tag_value(tags, "date"),
        "track_no": tag_value(tags, "tracknumber"),
        "genre": tag_value(tags, "genre"),
        "duration": float(getattr(info, "length", 0) or 0),
        "bitrate": int(getattr(info, "bitrate", 0) or 0),
        "size": path.stat().st_size,
        "has_art": int(has_artwork(path)),
    }


def has_artwork(path: Path):
    try:
        audio = File(path)
        if audio is None:
            return False
        if path.suffix.lower() == ".mp3":
            return bool(audio.tags and audio.tags.getall("APIC"))
        return False
    except Exception:
        return False


def save_track_tags(path: Path, values):
    audio = File(path, easy=True)
    if audio is None:
        raise ValueError("This audio format could not be read.")
    if audio.tags is None:
        audio.add_tags()
    mapping = {
        "title": values["title"], "artist": values["artist"],
        "album": values["album"], "date": values["year"],
        "tracknumber": values["track_no"], "genre": values["genre"]
    }
    for key, value in mapping.items():
        if value.strip():
            audio[key] = value.strip()
        elif key in audio:
            del audio[key]
    audio.save()


def embed_mp3_art(path: Path, image_path: Path):
    try:
        tags = ID3(path)
    except ID3NoHeaderError:
        tags = ID3()
    data = image_path.read_bytes()
    ext = image_path.suffix.lower()
    mime = "image/png" if ext == ".png" else "image/jpeg"
    tags.delall("APIC")
    tags.add(APIC(encoding=3, mime=mime, type=3, desc="Cover", data=data))
    tags.save(path, v2_version=3)


class NanoSyncApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("NanoSync | Personal Music Library")
        self.geometry("1120x700")
        self.minsize(900, 560)
        self.configure(bg="#101319")
        self.selected_path = None
        self._style()
        self._build()
        self.refresh()

    def _style(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure(".", font=("Segoe UI", 10))
        style.configure("Treeview", background="#191f29", foreground="#edf1f7",
                        fieldbackground="#191f29", rowheight=29, borderwidth=0)
        style.configure("Treeview.Heading", background="#252d3a", foreground="#cbd5e1",
                        font=("Segoe UI", 9, "bold"), relief="flat")
        style.map("Treeview", background=[("selected", "#315d86")],
                  foreground=[("selected", "white")])
        style.configure("TButton", padding=(12, 7))
        style.configure("TEntry", padding=6)
        style.configure("TLabel", background="#101319", foreground="#e7edf5")
        style.configure("Muted.TLabel", background="#101319", foreground="#9aa8ba")
        style.configure("TFrame", background="#101319")
        style.configure("TLabelframe", background="#101319", foreground="#e7edf5")
        style.configure("TLabelframe.Label", background="#101319", foreground="#9fb4cc")

    def _build(self):
        header = tk.Frame(self, bg="#101319")
        header.pack(fill="x", padx=22, pady=(18, 8))
        tk.Label(header, text="NanoSync", bg="#101319", fg="#f4f7fb",
                 font=("Segoe UI Semibold", 23)).pack(side="left")
        tk.Label(header, text="YOUR MUSIC, YOUR DEVICE.", bg="#101319", fg="#7f91a8",
                 font=("Segoe UI", 9, "bold")).pack(side="left", padx=14, pady=(10, 0))
        actions = tk.Frame(self, bg="#101319")
        actions.pack(fill="x", padx=22, pady=8)
        ttk.Button(actions, text="＋  Add music folder", command=self.scan_folder).pack(side="left")
        ttk.Button(actions, text="Refresh library", command=self.refresh).pack(side="left", padx=8)
        ttk.Button(actions, text="Export playlist (.m3u8)", command=self.export_playlist).pack(side="left")
        self.status = tk.StringVar(value="Ready")
        ttk.Label(actions, textvariable=self.status, style="Muted.TLabel").pack(side="right")

        main = tk.Frame(self, bg="#101319")
        main.pack(fill="both", expand=True, padx=22, pady=(8, 18))
        left = tk.Frame(main, bg="#101319")
        left.pack(side="left", fill="both", expand=True)
        cols = ("title", "artist", "album", "year", "bitrate")
        self.tree = ttk.Treeview(left, columns=cols, show="headings", selectmode="browse")
        headings = {"title":"TITLE", "artist":"ARTIST", "album":"ALBUM", "year":"YEAR", "bitrate":"KBPS"}
        widths = {"title":260, "artist":170, "album":190, "year":65, "bitrate":65}
        for col in cols:
            self.tree.heading(col, text=headings[col])
            self.tree.column(col, width=widths[col], minwidth=50, stretch=(col in ("title","album")))
        yscroll = ttk.Scrollbar(left, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=yscroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        yscroll.pack(side="right", fill="y")
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

        panel = tk.Frame(main, bg="#171d27", width=300)
        panel.pack(side="right", fill="y", padx=(14, 0))
        panel.pack_propagate(False)
        tk.Label(panel, text="TRACK DETAILS", bg="#171d27", fg="#91a6bf",
                 font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=16, pady=(16, 10))
        self.fields = {}
        for label, key in [("Title","title"),("Artist","artist"),("Album","album"),
                           ("Year","year"),("Track number","track_no"),("Genre","genre")]:
            tk.Label(panel, text=label, bg="#171d27", fg="#aab7c7",
                     font=("Segoe UI", 9)).pack(anchor="w", padx=16, pady=(7, 2))
            var = tk.StringVar()
            ent = ttk.Entry(panel, textvariable=var)
            ent.pack(fill="x", padx=16)
            self.fields[key] = var
        ttk.Button(panel, text="Save tags", command=self.save_selected).pack(fill="x", padx=16, pady=(16, 7))
        ttk.Button(panel, text="Add / replace MP3 cover", command=self.add_cover).pack(fill="x", padx=16, pady=4)
        ttk.Button(panel, text="Open containing folder", command=self.open_folder).pack(fill="x", padx=16, pady=4)
        self.detail = tk.StringVar(value="Select a track to inspect its tags.")
        tk.Label(panel, textvariable=self.detail, bg="#171d27", fg="#91a0b3",
                 justify="left", wraplength=265, font=("Segoe UI", 9)).pack(anchor="w", padx=16, pady=14)

        footer = tk.Frame(self, bg="#101319")
        footer.pack(fill="x", padx=22, pady=(0, 12))
        self.count = tk.StringVar(value="0 tracks")
        ttk.Label(footer, textvariable=self.count, style="Muted.TLabel").pack(side="left")
        ttk.Label(footer, text="MP3 artwork embedding supported in this first version",
                  style="Muted.TLabel").pack(side="right")

    def scan_folder(self):
        folder = filedialog.askdirectory(title="Choose a music folder")
        if not folder:
            return
        paths = []
        for base, _, names in os.walk(folder):
            for name in names:
                p = Path(base) / name
                if p.suffix.lower() in AUDIO_EXTENSIONS:
                    paths.append(p)
        conn = db()
        added = 0
        for p in paths:
            try:
                item = read_track(p)
                conn.execute("""INSERT OR REPLACE INTO tracks
                    (path,title,artist,album,year,track_no,genre,duration,bitrate,size,has_art)
                    VALUES (:path,:title,:artist,:album,:year,:track_no,:genre,:duration,:bitrate,:size,:has_art)""", item)
                added += 1
            except Exception:
                pass
        conn.commit()
        conn.close()
        self.refresh()
        self.status.set(f"Scanned {added} audio files")

    def refresh(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        conn = db()
        rows = conn.execute("SELECT path,title,artist,album,year,bitrate FROM tracks ORDER BY artist,album,title").fetchall()
        conn.close()
        for row in rows:
            path, title, artist, album, year, bitrate = row
            self.tree.insert("", "end", iid=path, values=(title, artist, album, year, round((bitrate or 0)/1000) if bitrate else ""))
        self.count.set(f"{len(rows)} tracks in library")
        if not rows:
            self.status.set("Add a music folder to get started")

    def on_select(self, _event=None):
        selected = self.tree.selection()
        if not selected:
            return
        self.selected_path = Path(selected[0])
        try:
            data = read_track(self.selected_path)
            for key in self.fields:
                self.fields[key].set(data.get(key, ""))
            duration = int(data["duration"])
            self.detail.set(f"{self.selected_path.name}\n\n{duration//60}:{duration%60:02d}  •  {data['size']/1024/1024:.1f} MB\nArtwork: {'Embedded' if data['has_art'] else 'Missing'}")
        except Exception as exc:
            self.detail.set(str(exc))

    def save_selected(self):
        if not self.selected_path:
            messagebox.showinfo("NanoSync", "Select a track first.")
            return
        try:
            save_track_tags(self.selected_path, {k:v.get() for k,v in self.fields.items()})
            self.refresh()
            self.tree.selection_set(str(self.selected_path))
            self.on_select()
            self.status.set("Tags saved")
        except Exception as exc:
            messagebox.showerror("Could not save tags", str(exc))

    def add_cover(self):
        if not self.selected_path:
            messagebox.showinfo("NanoSync", "Select a track first.")
            return
        if self.selected_path.suffix.lower() != ".mp3":
            messagebox.showinfo("Artwork", "This first version embeds artwork into MP3 files only.")
            return
        image = filedialog.askopenfilename(filetypes=[("Image files","*.jpg *.jpeg *.png")])
        if not image:
            return
        try:
            embed_mp3_art(self.selected_path, Path(image))
            self.refresh()
            self.tree.selection_set(str(self.selected_path))
            self.on_select()
            self.status.set("Cover embedded")
        except Exception as exc:
            messagebox.showerror("Could not embed artwork", str(exc))

    def open_folder(self):
        if not self.selected_path:
            return
        os.startfile(self.selected_path.parent)

    def export_playlist(self):
        selected = self.tree.selection()
        if selected:
            paths = list(selected)
        else:
            conn = db()
            paths = [r[0] for r in conn.execute("SELECT path FROM tracks ORDER BY artist,album,title").fetchall()]
            conn.close()
        target = filedialog.asksaveasfilename(defaultextension=".m3u8",
                    filetypes=[("M3U8 playlist","*.m3u8")], initialfile="NanoSync-Library.m3u8")
        if not target:
            return
        Path(target).write_text("#EXTM3U\n" + "\n".join(paths) + "\n", encoding="utf-8")
        self.status.set(f"Playlist exported: {len(paths)} tracks")


if __name__ == "__main__":
    NanoSyncApp().mainloop()
