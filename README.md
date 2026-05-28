# 🌸 SheBuilds Photobooth

A cute pink photobooth web app! Takes 3 photos with a countdown timer, generates a QR code so guests can download their photos on their phones.

## Features
- 📸 3-photo sequence with 3-second countdown
- ✨ Flash effect + live strip preview
- 📱 QR code for mobile photo download
- 🌸 SheBuilds pink aesthetic

## Tech Stack
- **Frontend**: Vanilla HTML/CSS/JS (single file)
- **Backend**: Node.js + Express
- **Libraries**: `qrcode`, `uuid`, `multer`, `cors`

---

## Local Development

```bash
npm install
npm start
# Open http://localhost:3000
```

---

## Deploy to Vercel

### Step 1 — Push to GitHub

```bash
git init
git add .
git commit -m "Initial commit: SheBuilds Photobooth"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/shebuilds-photobooth.git
git push -u origin main
```

### Step 2 — Deploy on Vercel

1. Go to [vercel.com](https://vercel.com) and sign in with GitHub
2. Click **"Add New Project"**
3. Import your `shebuilds-photobooth` repository
4. Vercel will auto-detect the settings from `vercel.json`
5. Click **Deploy** — done! 🎉

Your app will be live at `https://shebuilds-photobooth.vercel.app` (or similar).

---

## Notes

- **Photos are stored in memory** (RAM) for 1 hour. This is perfect for event use.
- **Camera access** requires HTTPS in production — Vercel provides this automatically.
- To support more than ~50 simultaneous sessions, consider adding a database (e.g. Supabase or Redis).

---

Made with 💗 for SheBuilds
