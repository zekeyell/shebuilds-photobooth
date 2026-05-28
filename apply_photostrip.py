#!/usr/bin/env python3
"""
SheBuilds Photobooth — Apply Photostrip Template
Run from inside the shebuilds-photobooth folder:
  python apply_photostrip.py

What it does:
  - Copies Photostrip.png into public/
  - Updates server.js to composite photos onto the strip template
    instead of serving plain HTML
  - QR code now points to the composited strip image (PNG download)
"""
import shutil, sys
from pathlib import Path

SCRIPT_DIR   = Path(__file__).parent
SERVER_FILE  = SCRIPT_DIR / "server.js"
PUBLIC_DIR   = SCRIPT_DIR / "public"
STRIP_SRC    = SCRIPT_DIR / "Photostrip.png"

REQUIRED = {"Photostrip.png": STRIP_SRC}

def check():
    missing = [n for n,p in REQUIRED.items() if not p.exists()]
    if missing:
        print("❌  Missing files:")
        for m in missing: print(f"    • {m}")
        sys.exit(1)

def main():
    check()
    print("🌸  SheBuilds — Apply Photostrip")
    print("─"*42)

    # Copy strip template into public/
    dest = PUBLIC_DIR / "Photostrip.png"
    shutil.copy(STRIP_SRC, dest)
    print(f"📋  Copied Photostrip.png → public/")

    # Backup server.js
    bak = SCRIPT_DIR / "server.js.bak"
    shutil.copy(SERVER_FILE, bak)
    print(f"💾  Backed up server.js → server.js.bak")

    # Write new server.js
    SERVER_FILE.write_text(NEW_SERVER, encoding="utf-8")
    print(f"✍️   Updated server.js")

    print()
    print("✅  Done! Now run:")
    print("    npx kill-port 3000 && npm start")

NEW_SERVER = r"""const express  = require("express");
const fs       = require("fs");
const path     = require("path");
const QRCode   = require("qrcode");
const { v4: uuidv4 } = require("uuid");
const app  = express();
const PORT = process.env.PORT || 3000;

app.use(express.static(path.join(__dirname, "public")));
app.use(express.json({ limit: "30mb" }));

app.post("/api/save-session", async (req, res) => {
  try {
    const { photos, compositedStrip } = req.body;
    if (!photos || photos.length < 3)
      return res.status(400).json({ error: "Need 3 photos" });

    const sessionId  = uuidv4();
    const sessionDir = path.join(__dirname, "public", "sessions", sessionId);
    fs.mkdirSync(sessionDir, { recursive: true });

    // Save individual photos
    photos.forEach((dataUrl, i) => {
      const base64 = dataUrl.replace(/^data:image\/\w+;base64,/, "");
      fs.writeFileSync(
        path.join(sessionDir, `photo_${i + 1}.jpg`),
        Buffer.from(base64, "base64")
      );
    });

    // Save the browser-composited strip directly (no server canvas needed!)
    const stripPath = path.join(sessionDir, "strip.png");
    if (compositedStrip) {
      const base64 = compositedStrip.replace(/^data:image\/\w+;base64,/, "");
      fs.writeFileSync(stripPath, Buffer.from(base64, "base64"));
    }

    // QR code points directly to the strip PNG (downloadable)
    const host       = req.get("host");
    const protocol   = req.protocol;
    const stripUrl   = `${protocol}://${host}/sessions/${sessionId}/strip.png`;
    const qrCode     = await QRCode.toDataURL(stripUrl, {
      width: 300, margin: 2,
      color: { dark: "#e91e8c", light: "#fff0f8" }
    });

    res.json({ qrCode, stripUrl, sessionId });
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: "Server error: " + err.message });
  }
});

app.get("/api/session/:id", (req, res) => {
  const stripPath = path.join(__dirname, "public", "sessions", req.params.id, "strip.png");
  if (!fs.existsSync(stripPath))
    return res.status(404).json({ error: "Session not found" });
  res.json({ stripUrl: `/sessions/${req.params.id}/strip.png` });
});

app.listen(PORT, () => {
  console.log(`🌸  SheBuilds Photobooth running at http://localhost:${PORT}`);
});
"""

if __name__ == "__main__":
    main()
