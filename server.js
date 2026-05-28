const express = require("express");
const QRCode  = require("qrcode");
const { v4: uuidv4 } = require("uuid");

const app  = express();
const PORT = process.env.PORT || 3000;

app.use(express.static(require("path").join(__dirname, "public")));
app.use(express.json({ limit: "50mb" }));

// In-memory store — good enough for a one-time event
const sessions = new Map();

app.post("/api/save-session", async (req, res) => {
  try {
    const { photos, compositedStrip } = req.body;
    if (!photos || photos.length < 3)
      return res.status(400).json({ error: "Need 3 photos" });

    const sessionId = uuidv4();

    // Store composited strip in memory
    sessions.set(sessionId, {
      strip: compositedStrip,
      createdAt: Date.now()
    });

    // Clean up sessions older than 2 hours
    for (const [id, s] of sessions.entries()) {
      if (Date.now() - s.createdAt > 2 * 60 * 60 * 1000) sessions.delete(id);
    }

    const baseUrl = process.env.VERCEL_URL
      ? `https://${process.env.VERCEL_URL}`
      : `${req.protocol}://${req.get("host")}`;

    const stripUrl = `${baseUrl}/api/strip/${sessionId}`;

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

// Serve strip image from memory
app.get("/api/strip/:id", (req, res) => {
  const session = sessions.get(req.params.id);
  if (!session || !session.strip) {
    return res.status(404).send("Session not found or expired.");
  }
  // Convert base64 data URL to buffer and serve as image
  const base64 = session.strip.replace(/^data:image\/\w+;base64,/, "");
  const buf = Buffer.from(base64, "base64");
  res.set("Content-Type", "image/jpeg");
  res.set("Content-Disposition", `attachment; filename="shebuilds-photobooth.jpg"`);
  res.send(buf);
});

app.listen(PORT, () => {
  console.log(`🌸  SheBuilds Photobooth running on port ${PORT}`);
});
