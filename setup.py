#!/usr/bin/env python3
"""
SheBuilds Photobooth — Setup Script
Creates server.js and package.json, then runs npm install.
Run from: C:\\dev\\shebuilds-photobooth\\
"""
import subprocess, sys
from pathlib import Path

BASE = Path(__file__).parent

# ── package.json ─────────────────────────────────────────────
PACKAGE_JSON = """{
  "name": "shebuilds-photobooth",
  "version": "1.0.0",
  "description": "SheBuilds Photobooth – GDG on Campus TUP Manila",
  "main": "server.js",
  "scripts": {
    "start": "node server.js"
  },
  "dependencies": {
    "express": "^4.18.2",
    "qrcode": "^1.5.3",
    "uuid": "^9.0.0"
  }
}
"""

# ── server.js ─────────────────────────────────────────────────
SERVER_JS = r"""const express = require("express");
const fs      = require("fs");
const path    = require("path");
const QRCode  = require("qrcode");
const { v4: uuidv4 } = require("uuid");

const app  = express();
const PORT = 3000;

app.use(express.static(path.join(__dirname, "public")));
app.use(express.json({ limit: "20mb" }));

app.post("/api/save-session", async (req, res) => {
  try {
    const { photos } = req.body;
    if (!photos || photos.length < 3)
      return res.status(400).json({ error: "Need 3 photos" });

    const sessionId  = uuidv4();
    const sessionDir = path.join(__dirname, "public", "sessions", sessionId);
    fs.mkdirSync(sessionDir, { recursive: true });

    photos.forEach((dataUrl, i) => {
      const base64 = dataUrl.replace(/^data:image\/\w+;base64,/, "");
      fs.writeFileSync(
        path.join(sessionDir, `photo_${i + 1}.jpg`),
        Buffer.from(base64, "base64")
      );
    });

    const sessionUrl = `http://localhost:${PORT}/sessions/${sessionId}/strip.html`;

    const stripHtml = `<!DOCTYPE html>
<html><head><meta charset="UTF-8"/>
<title>SheBuilds Photobooth Strip</title>
<style>
  body{background:#f9c8e0;display:flex;flex-direction:column;align-items:center;
       font-family:sans-serif;padding:20px;gap:12px}
  img{width:320px;border-radius:12px;box-shadow:0 4px 16px rgba(0,0,0,.2)}
  h2{color:#c7306d}
</style></head><body>
<h2>🌸 SheBuilds Photobooth</h2>
<img src="photo_1.jpg"/>
<img src="photo_2.jpg"/>
<img src="photo_3.jpg"/>
</body></html>`;
    fs.writeFileSync(path.join(sessionDir, "strip.html"), stripHtml);

    const qrCode = await QRCode.toDataURL(sessionUrl);
    res.json({ qrCode, sessionUrl });
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: "Server error" });
  }
});

app.listen(PORT, () => {
  console.log(`✅  SheBuilds Photobooth running at http://localhost:${PORT}`);
});
"""

def write(path, content, label):
    path.write_text(content, encoding="utf-8")
    print(f"✅  Created {label}")

def main():
    print("🌸  SheBuilds Photobooth — Setup")
    print("─" * 40)

    write(BASE / "package.json", PACKAGE_JSON, "package.json")
    write(BASE / "server.js",    SERVER_JS,    "server.js")

    (BASE / "public").mkdir(exist_ok=True)
    (BASE / "public" / "sessions").mkdir(exist_ok=True)
    print("✅  Created public/ and public/sessions/ folders")

    print("\n📦  Running npm install...")
    result = subprocess.run(["npm", "install"], cwd=BASE, shell=True)
    if result.returncode != 0:
        print("❌  npm install failed. Make sure Node.js is installed.")
        sys.exit(1)

    print("\n✅  All done! Now run:")
    print("    python update_ui.py   ← generates public/index.html")
    print("    npm start             ← starts the server on http://localhost:3000")

if __name__ == "__main__":
    main()
