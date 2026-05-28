const express = require("express");
const fs      = require("fs");
const path    = require("path");
const QRCode  = require("qrcode");
const { v4: uuidv4 } = require("uuid");

const app  = express();
const PORT = process.env.PORT || 3000;
const BASE_URL = process.env.HOST_URL || null; // e.g. http://192.168.1.2:3000

app.use(express.static(path.join(__dirname, "public")));
app.use(express.json({ limit: "50mb" }));

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

    // Save the browser-composited strip PNG for QR download
    const stripPath = path.join(sessionDir, "strip.png");
    if (compositedStrip) {
      const base64 = compositedStrip.replace(/^data:image\/\w+;base64,/, "");
      fs.writeFileSync(stripPath, Buffer.from(base64, "base64"));
    }

    // Use HOST_URL env var if set, otherwise fall back to request host
    const baseUrl = BASE_URL || `${req.protocol}://${req.get("host")}`;
    const stripUrl = `${baseUrl}/sessions/${sessionId}/strip.png`;

    const qrCode = await QRCode.toDataURL(stripUrl, {
      width: 300, margin: 2,
      color: { dark: "#e91e8c", light: "#fff0f8" }
    });

    res.json({ qrCode, stripUrl, sessionId });
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: "Server error: " + err.message });
  }
});

app.listen(PORT, () => {
  const baseUrl = BASE_URL || `http://localhost:${PORT}`;
  console.log(`🌸  SheBuilds Photobooth running at ${baseUrl}`);
});
