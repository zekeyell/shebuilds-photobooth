#!/usr/bin/env python3
"""
SheBuilds Photobooth — UI Update Script
Run: python update_ui.py
"""
import base64, io, shutil, sys
from pathlib import Path

try:
    from PIL import Image, ImageFilter
    import numpy as np
except ImportError:
    print("❌  Missing dependencies. Run:  pip install Pillow numpy")
    sys.exit(1)

SCRIPT_DIR  = Path(__file__).parent
OUTPUT_FILE = SCRIPT_DIR / "public" / "index.html"
BACKUP_FILE = SCRIPT_DIR / "public" / "index.html.bak"

# ── Image file names (no renaming needed)
IMG_THUMBSUP = SCRIPT_DIR / "gigi_thumbsup_old.png"
IMG_DREAMY   = SCRIPT_DIR / "gigi_dreamy_fixed2.png"   # fixed eyes
IMG_SHY      = SCRIPT_DIR / "gigi_shy_old.png"
IMG_LOGO     = SCRIPT_DIR / "shebuilds_logo_final.png"
IMG_GDG      = SCRIPT_DIR / "gdg_logo_clean2.png"
IMG_STRIP    = SCRIPT_DIR / "Photostrip (1).png"

REQUIRED = {
    "gigi_thumbsup_old.png":   IMG_THUMBSUP,
    "gigi_dreamy_fixed2.png":  IMG_DREAMY,
    "gigi_shy_old.png":        IMG_SHY,
    "shebuilds_logo_final.png":IMG_LOGO,
    "gdg_logo_clean2.png":     IMG_GDG,
    "Photostrip (1).png":      IMG_STRIP,
}

def check_images():
    missing = [n for n, p in REQUIRED.items() if not p.exists()]
    if missing:
        print("❌  Missing image files:")
        for m in missing: print(f"    • {m}")
        sys.exit(1)

def remove_black_bg_smooth(path, resize_width=None, threshold=30):
    """Simple threshold — good for black backgrounds (logo, shy, thumbsup)."""
    img = Image.open(path).convert("RGB")
    arr = np.array(img, dtype=np.uint8)
    r,g,b = arr[:,:,0].astype(int), arr[:,:,1].astype(int), arr[:,:,2].astype(int)
    mask = (r < threshold) & (g < threshold) & (b < threshold)
    rgba = np.zeros((*arr.shape[:2], 4), dtype=np.uint8)
    rgba[:,:,:3] = arr
    rgba[:,:,3] = np.where(mask, 0, 255).astype(np.uint8)
    result = Image.fromarray(rgba, "RGBA")
    a = result.getchannel("A").filter(ImageFilter.GaussianBlur(radius=0.6))
    result.putalpha(a)
    bbox = result.getbbox()
    if bbox: result = result.crop(bbox)
    if resize_width:
        w,h = result.size
        result = result.resize((resize_width, int(h*resize_width/w)), Image.LANCZOS)
    buf = io.BytesIO(); result.save(buf,"PNG"); return buf.getvalue()

def remove_black_bg_floodfill(path, resize_width=None, threshold=35):
    """Flood-fill from edges — preserves interior dark pixels like eyes."""
    img = Image.open(path).convert("RGB")
    arr = np.array(img, dtype=np.uint8)
    h, w = arr.shape[:2]
    visited = np.zeros((h,w), dtype=bool)
    stack = []
    for x in range(w): stack += [(0,x),(h-1,x)]
    for y in range(h): stack += [(y,0),(y,w-1)]
    while stack:
        y,x = stack.pop()
        if y<0 or y>=h or x<0 or x>=w or visited[y,x]: continue
        r,g,b = int(arr[y,x,0]),int(arr[y,x,1]),int(arr[y,x,2])
        if r<threshold and g<threshold and b<threshold:
            visited[y,x] = True
            stack += [(y+1,x),(y-1,x),(y,x+1),(y,x-1)]
    rgba = np.zeros((h,w,4), dtype=np.uint8)
    rgba[:,:,:3] = arr
    rgba[:,:,3] = np.where(visited, 0, 255).astype(np.uint8)
    result = Image.fromarray(rgba,"RGBA")
    a = result.getchannel("A").filter(ImageFilter.GaussianBlur(radius=0.6))
    result.putalpha(a)
    bbox = result.getbbox()
    if bbox: result = result.crop(bbox)
    if resize_width:
        ww,hh = result.size
        result = result.resize((resize_width, int(hh*resize_width/ww)), Image.LANCZOS)
    buf = io.BytesIO(); result.save(buf,"PNG"); return buf.getvalue()

def load_as_is(path, resize_width=None):
    img = Image.open(path).convert("RGBA")
    if resize_width:
        w,h = img.size
        img = img.resize((resize_width, int(h*resize_width/w)), Image.LANCZOS)
    buf = io.BytesIO(); img.save(buf,"PNG"); return buf.getvalue()

def b64(data): return base64.b64encode(data).decode()

def main():
    check_images()
    print("🌸  SheBuilds Photobooth — UI Update")
    print("─"*42)
    print("🖌️   Processing images...")
    tu = remove_black_bg_smooth(IMG_THUMBSUP,  resize_width=500)
    dr = remove_black_bg_floodfill(IMG_DREAMY, resize_width=500)  # eyes preserved
    sh = remove_black_bg_smooth(IMG_SHY,       resize_width=380)
    lg = remove_black_bg_smooth(IMG_LOGO,      resize_width=620)
    gd = load_as_is(IMG_GDG,                   resize_width=80)
    st = load_as_is(IMG_STRIP,                 resize_width=180)
    for label,data in [("thumbsup",tu),("dreamy",dr),("shy",sh),("logo",lg),("gdg",gd),("strip",st)]:
        print(f"    {label:<12}: {len(data)//1024} KB")
    print("📦  Encoding...")
    b_tu,b_dr,b_sh,b_lg,b_gd,b_st = b64(tu),b64(dr),b64(sh),b64(lg),b64(gd),b64(st)
    if OUTPUT_FILE.exists():
        shutil.copy(OUTPUT_FILE, BACKUP_FILE)
        print(f"💾  Backed up → index.html.bak")
    print("✍️   Writing index.html...")
    OUTPUT_FILE.write_text(build_html(b_tu,b_dr,b_sh,b_lg,b_gd,b_st), encoding="utf-8")
    print("\n✅  Done! Now run:")
    print("    npx kill-port 3000 && npm start")

def build_html(b_tu, b_dr, b_sh, b_lg, b_gd, b_st):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1.0"/>
  <title>SheBuilds Photobooth ✨</title>
  <link href="https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;900&display=swap" rel="stylesheet"/>
  <style>
    *,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
    :root{{--pk:#f0478a;--pkd:#c7306d;--pkm:#e085b8;--gr:#7dc142;--grd:#5fa32e;}}
    html,body{{width:100%;height:100%;font-family:'Nunito',sans-serif;background:#f9c8e0;overflow:hidden}}

    .screen{{position:fixed;inset:0;display:flex;align-items:center;justify-content:center;
             opacity:0;pointer-events:none;transition:opacity .4s ease;overflow:hidden}}
    .screen.active{{opacity:1;pointer-events:all}}

    .sbg{{position:absolute;inset:0;z-index:0;
          background:linear-gradient(145deg,#fac9e0 0%,#fde8f5 55%,#f7bcd8 100%)}}
    .blob{{position:absolute;border-radius:50%;filter:blur(65px);opacity:.5;pointer-events:none}}
    .b1{{width:400px;height:400px;background:#f9a8d4;top:-90px;left:-90px}}
    .b2{{width:320px;height:320px;background:#fbcfe8;bottom:-70px;right:-50px}}
    .b3{{width:240px;height:240px;background:#f0abcb;top:38%;right:4%}}
    .b4{{width:190px;height:190px;background:#fda4af;top:8%;left:33%}}
    .petal{{position:absolute;pointer-events:none;font-size:1.3rem;opacity:.45;animation:pfall linear infinite}}
    @keyframes pfall{{0%{{transform:translateY(-40px) rotate(0deg);opacity:0}}10%{{opacity:.5}}90%{{opacity:.3}}100%{{transform:translateY(110vh) rotate(720deg);opacity:0}}}}
    .cdeco{{position:absolute;pointer-events:none;color:var(--pk);font-family:monospace;font-size:1.4rem;font-weight:900;opacity:.25;letter-spacing:-4px}}
    .hdeco{{position:absolute;pointer-events:none;color:var(--pk);font-size:.95rem;opacity:.3}}

    /* GDG bar */
    .gdg-bar{{position:absolute;top:0;left:0;right:0;z-index:20;display:flex;align-items:center;
              gap:12px;padding:8px 22px;background:rgba(255,255,255,0.6);
              backdrop-filter:blur(10px);border-bottom:1.5px solid rgba(240,71,138,0.13)}}
    .gdg-bar img.gdg-icon{{height:36px;width:36px;object-fit:contain;flex-shrink:0}}
    .gdg-t1{{font-size:.78rem;font-weight:900;color:#c7306d}}
    .gdg-t2{{font-size:.66rem;font-weight:600;color:#b05080}}

    /* Buttons */
    .btn{{border:none;cursor:pointer;font-family:'Nunito',sans-serif;font-weight:900;
          font-size:1.1rem;letter-spacing:.08em;border-radius:50px;padding:13px 40px;
          text-transform:uppercase;transition:transform .12s,box-shadow .12s;user-select:none}}
    .btn:hover{{transform:translateY(-2px)}}
    .btn:active{{transform:translateY(1px) scale(.98)}}
    .btn-pink{{background:var(--pk);color:#fff;box-shadow:0 6px 0 var(--pkd),0 8px 20px rgba(240,71,138,.35)}}
    .btn-pink:hover{{box-shadow:0 8px 0 var(--pkd)}}
    .btn-pink:active{{box-shadow:0 2px 0 var(--pkd)}}
    .btn-green{{background:var(--gr);color:#fff;box-shadow:0 6px 0 var(--grd),0 8px 20px rgba(125,193,66,.35)}}
    .btn-green:active{{box-shadow:0 2px 0 var(--grd)}}
    .btn-outline{{background:transparent;color:var(--pk);border:2.5px solid var(--pk)}}
    .btn-outline:hover{{background:rgba(240,71,138,.06)}}

    /* Gigi — inward from right edge, vertically centered */
    .gigi{{
      position:fixed;
      right:60px;           /* pushed more inward */
      top:50%;
      transform:translateY(-50%);
      z-index:30;
      width:260px;
      pointer-events:none;
      animation:bob 3s ease-in-out infinite;
    }}
    /* Screen 2 gigi stays bottom-right, smaller, out of the way */
    .gigi.s2-gigi{{
      width:160px;
      right:16px;
      top:auto;
      bottom:0;
      transform:none;
      animation:bob2 3s ease-in-out infinite;
    }}
    .gigi img{{width:100%;display:block}}
    @keyframes bob{{0%,100%{{transform:translateY(-50%)}}50%{{transform:translateY(calc(-50% - 16px))}}}}
    @keyframes bob2{{0%,100%{{transform:translateY(0)}}50%{{transform:translateY(-12px)}}}}

    /* SheBuilds logo */
    .sb-logo{{display:block;width:clamp(260px,34vw,480px);height:auto;
              filter:drop-shadow(0 4px 16px rgba(240,71,138,.2))}}

    /* ════ SCREEN 1 ════ */
    .s1-inner{{
      position:relative;z-index:1;
      display:flex;align-items:center;justify-content:center;
      gap:50px;
      padding:68px 340px 40px 40px;   /* right pad reserves space for Gigi */
      width:100%;max-width:1200px;
    }}
    .s1-strip-wrap{{flex-shrink:0;transform:rotate(-4deg);
                    filter:drop-shadow(0 16px 40px rgba(200,80,140,.3))}}
    .s1-strip-img{{width:160px;height:auto;display:block;border-radius:8px}}
    /* Logo + button stacked, centered */
    .s1-content{{
      display:flex;flex-direction:column;
      align-items:center;   /* CENTER logo and button */
      gap:28px;
    }}

    /* ════ SCREEN 2 ════ */
    .s2-inner{{position:relative;z-index:1;display:flex;align-items:stretch;
               gap:20px;padding:62px 24px 16px;width:100%;max-width:1060px;height:100vh}}
    .s2-left{{flex:1;display:flex;flex-direction:column;gap:10px;min-height:0}}
    .cam-wrap{{flex:1;min-height:0;position:relative}}
    .cam-box{{position:absolute;inset:0;background:#1a0a10;border-radius:14px;overflow:hidden;
              box-shadow:0 8px 40px rgba(200,60,120,.3);border:3px solid rgba(255,255,255,.4)}}
    #camera-video{{width:100%;height:100%;object-fit:cover;transform:scaleX(-1);display:block}}
    .cdown-overlay{{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;
                    background:rgba(0,0,0,.32);opacity:0;pointer-events:none;transition:opacity .2s}}
    .cdown-overlay.visible{{opacity:1}}
    .cdown-num{{font-size:8rem;font-weight:900;color:#fff;
                text-shadow:0 0 40px rgba(240,71,138,.8),4px 4px 0 var(--pk);animation:cpop .3s ease-out}}
    @keyframes cpop{{0%{{transform:scale(1.6);opacity:0}}100%{{transform:scale(1);opacity:1}}}}
    .flash-ov{{position:absolute;inset:0;background:#fff;opacity:0;pointer-events:none;transition:opacity .05s}}
    .flash-ov.flash{{opacity:1;transition:opacity .35s}}
    .dot-bar{{display:flex;gap:10px;justify-content:center;flex-shrink:0}}
    .dot{{width:13px;height:13px;border-radius:50%;background:rgba(255,255,255,.4);
          border:2px solid var(--pk);transition:background .3s}}
    .dot.on{{background:var(--pk)}}
    .s2-status{{text-align:center;font-size:.92rem;font-weight:700;color:var(--pkd);min-height:20px;flex-shrink:0}}
    .s2-btns{{display:flex;gap:12px;flex-shrink:0}}
    .s2-btns .btn{{flex:1;font-size:.95rem;padding:11px 16px}}
    .s2-strip-wrap{{flex-shrink:0;width:190px;display:flex;flex-direction:column}}
    .s2-strip{{background:#fff;border-radius:14px;padding:10px 10px 18px;display:flex;
               flex-direction:column;gap:8px;flex:1;box-shadow:0 10px 40px rgba(200,60,120,.22)}}
    .s2-slot{{flex:1;background:#e8d8f0;border-radius:8px;overflow:hidden;
              display:flex;align-items:center;justify-content:center;
              color:#cbb0d0;font-size:1.8rem;min-height:0}}
    .s2-slot img{{width:100%;height:100%;object-fit:cover;display:block;transform:scaleX(-1)}}

    /* ════ SCREEN 3 ════ */
    .s3-inner{{
      position:relative;z-index:1;
      display:flex;align-items:center;
      gap:46px;
      padding:70px 340px 40px 40px;   /* right pad reserves space for Gigi */
      width:100%;max-width:1200px;
    }}
    .s3-strip-wrap{{flex-shrink:0;filter:drop-shadow(0 14px 40px rgba(200,60,120,.25))}}
    .s3-strip-img{{width:190px;height:auto;display:block;border-radius:8px}}
    .s3-content{{display:flex;flex-direction:column;align-items:center;gap:16px;flex:1}}
    .scan-label{{background:var(--pk);color:#fff;font-weight:900;font-size:.85rem;
                 letter-spacing:.1em;padding:10px 28px;border-radius:50px;
                 display:block;text-transform:uppercase;box-shadow:0 4px 0 var(--pkd);
                 text-align:center;width:100%}}
    .qr-box{{background:#fff;border-radius:16px;padding:13px;width:200px;height:200px;
             display:flex;align-items:center;justify-content:center;
             box-shadow:0 8px 30px rgba(200,60,120,.15)}}
    .qr-box img{{width:100%;height:100%;object-fit:contain}}
    .qr-load{{color:var(--pkm);font-size:.85rem;font-weight:700;text-align:center}}
    .s3-btns .btn{{font-size:.95rem;padding:12px 48px}}

    @media(max-width:900px){{
      .s1-inner,.s3-inner{{padding:68px 40px 40px}}
      .gigi{{right:20px;width:200px}}
    }}
    @media(max-width:700px){{
      /* Hide Gigi on mobile — she blocks everything */
      .gigi{{display:none}}

      /* Screen 1 */
      .s1-inner{{flex-direction:column;gap:16px;padding:64px 16px 16px;text-align:center}}
      .sb-logo{{width:clamp(200px,68vw,340px)}}

      /* Screen 2 */
      .s2-inner{{flex-direction:column;padding:60px 12px 12px;gap:10px}}
      .s2-strip-wrap{{width:100%}}
      .s2-strip{{flex-direction:row;padding:8px;flex:none}}
      .s2-slot{{height:75px;flex:1}}

      /* Screen 3 — scrollable */
      .screen#screen-3{{overflow-y:auto;align-items:flex-start}}
      .s3-inner{{
        flex-direction:column;
        padding:68px 16px 40px;
        gap:20px;
        min-height:100%;
        width:100%;
        align-items:center;
      }}
      .s3-strip-wrap{{width:100%;display:flex;justify-content:center}}
      .s3-strip-img{{width:55vw;max-width:260px}}
      .s3-content{{width:100%;align-items:center}}
      .scan-label{{font-size:.78rem;padding:9px 20px}}
      .qr-box{{width:180px;height:180px}}
      .s3-btns .btn{{padding:12px 40px}}
    }}
  </style>
</head>
<body>

<!-- Gigi — shared, swapped per screen -->
<div class="gigi" id="gigi-wrap">
  <img id="gigi-img" src="data:image/png;base64,{b_sh}" alt="Gigi"/>
</div>

<!-- ════════════ SCREEN 1 ════════════ -->
<div class="screen active" id="screen-1">
  <div class="sbg">
    <div class="blob b1"></div><div class="blob b2"></div>
    <div class="blob b3"></div><div class="blob b4"></div>
    <div class="petal" style="left:8%;animation-duration:7s;animation-delay:0s">🌸</div>
    <div class="petal" style="left:23%;animation-duration:9s;animation-delay:1.5s">🌸</div>
    <div class="petal" style="left:46%;animation-duration:6s;animation-delay:.8s">🌸</div>
    <div class="petal" style="left:64%;animation-duration:8s;animation-delay:2s">🌸</div>
    <div class="petal" style="left:82%;animation-duration:7.5s;animation-delay:.3s">🌸</div>
    <div class="cdeco" style="top:20%;left:7%">&lt;&gt;</div>
    <div class="cdeco" style="top:24%;right:9%">&lt;&gt;</div>
    <div class="cdeco" style="bottom:22%;left:16%">&lt;&gt;</div>
    <div class="hdeco" style="top:34%;right:22%">♥ ♥</div>
    <div class="hdeco" style="bottom:30%;right:30%">♥</div>
  </div>
  <div class="gdg-bar">
    <img class="gdg-icon" src="data:image/png;base64,{b_gd}" alt="GDG"/>
    <div><div class="gdg-t1">Google Developer Groups on Campus</div>
    <div class="gdg-t2">Technological University of the Philippines – Manila</div></div>
  </div>
  <div class="s1-inner">
    <div class="s1-strip-wrap">
      <img class="s1-strip-img" src="data:image/png;base64,{b_st}"
           alt="Photo Strip Preview"/>
    </div>
    <div class="s1-content">
      <img class="sb-logo" src="data:image/png;base64,{b_lg}" alt="SheBuilds Photobooth"/>
      <button class="btn btn-pink" id="btn-start-1">START!</button>
    </div>
  </div>
</div>

<!-- ════════════ SCREEN 2 ════════════ -->
<div class="screen" id="screen-2">
  <div class="sbg">
    <div class="blob b1"></div><div class="blob b2"></div>
    <div class="petal" style="left:5%;animation-duration:8s;animation-delay:.4s">🌸</div>
    <div class="petal" style="left:89%;animation-duration:7s;animation-delay:1.2s">🌸</div>
    <div class="cdeco" style="top:20%;right:8%">&lt;&gt;</div>
    <div class="hdeco" style="bottom:16%;right:6%">♥ ♥</div>
  </div>
  <div class="gdg-bar">
    <img class="gdg-icon" src="data:image/png;base64,{b_gd}" alt="GDG"/>
    <div><div class="gdg-t1">Google Developer Groups on Campus</div>
    <div class="gdg-t2">Technological University of the Philippines – Manila</div></div>
  </div>
  <div class="s2-inner">
    <div class="s2-left">
      <div class="cam-wrap">
        <div class="cam-box">
          <video id="camera-video" autoplay playsinline muted></video>
          <canvas id="camera-canvas" style="display:none"></canvas>
          <div class="cdown-overlay" id="cdown-overlay">
            <div class="cdown-num" id="cdown-num">3</div>
          </div>
          <div class="flash-ov" id="flash-ov"></div>
        </div>
      </div>
      <div class="dot-bar">
        <div class="dot" id="dot-0"></div>
        <div class="dot" id="dot-1"></div>
        <div class="dot" id="dot-2"></div>
      </div>
      <div class="s2-status" id="s2-status">Press START to begin!</div>
      <div class="s2-btns">
        <button class="btn btn-pink"  id="btn-start-2">START</button>
        <button class="btn btn-green" id="btn-done" disabled>DONE</button>
      </div>
    </div>
    <div class="s2-strip-wrap">
      <div class="s2-strip">
        <div class="s2-slot" id="s2-slot-0">📷</div>
        <div class="s2-slot" id="s2-slot-1">📷</div>
        <div class="s2-slot" id="s2-slot-2">📷</div>
      </div>
    </div>
  </div>
</div>

<!-- ════════════ SCREEN 3 ════════════ -->
<div class="screen" id="screen-3">
  <div class="sbg">
    <div class="blob b1"></div><div class="blob b2"></div><div class="blob b3"></div>
    <div class="petal" style="left:4%;animation-duration:9s;animation-delay:0s">🌸</div>
    <div class="petal" style="left:52%;animation-duration:7s;animation-delay:1s">🌸</div>
    <div class="petal" style="left:80%;animation-duration:8s;animation-delay:.5s">🌸</div>
    <div class="cdeco" style="top:20%;left:6%">&lt;&gt;</div>
    <div class="hdeco" style="top:32%;right:8%">♥ ♥</div>
    <div class="hdeco" style="bottom:24%;left:10%">♥</div>
  </div>
  <div class="gdg-bar">
    <img class="gdg-icon" src="data:image/png;base64,{b_gd}" alt="GDG"/>
    <div><div class="gdg-t1">Google Developer Groups on Campus</div>
    <div class="gdg-t2">Technological University of the Philippines – Manila</div></div>
  </div>
  <div class="s3-inner">
    <div class="s3-strip-wrap">
      <img class="s3-strip-img" id="s3-strip-img"
           src="data:image/png;base64,{b_st}" alt="Your Photos"/>
    </div>
    <div class="s3-content">
      <img class="sb-logo" src="data:image/png;base64,{b_lg}" alt="SheBuilds Photobooth"
           style="width:clamp(200px,24vw,340px)"/>
      <span class="scan-label">📱 Scan to Download</span>
      <div class="qr-box" id="qr-box">
        <div class="qr-load">Generating<br>your QR...</div>
      </div>
      <div class="s3-btns">
        <button class="btn btn-outline" id="btn-take-again">TAKE AGAIN</button>
      </div>
    </div>
  </div>
</div>

<script>
  const $=id=>document.getElementById(id);
  const GIGI={{
    shy:     'data:image/png;base64,{b_sh}',
    dreamy:  'data:image/png;base64,{b_dr}',
    thumbsup:'data:image/png;base64,{b_tu}',
  }};
  function setGigi(p){{
    const wrap=$('gigi-wrap');
    $('gigi-img').src=GIGI[p];
    // Screen 2: smaller gigi bottom-right; S1/S3: big middle-right
    if(p==='dreamy'){{
      wrap.style.cssText='position:fixed;right:16px;bottom:0;top:auto;transform:none;width:160px;z-index:30;pointer-events:none;animation:bob2 3s ease-in-out infinite';
    }}else{{
      wrap.style.cssText='position:fixed;right:60px;top:50%;transform:translateY(-50%);width:260px;z-index:30;pointer-events:none;animation:bob 3s ease-in-out infinite';
    }}
  }}
  function showScreen(n){{
    document.querySelectorAll('.screen').forEach(s=>s.classList.remove('active'));
    $(`screen-${{n}}`).classList.add('active');
    if(n===1)setGigi('shy');
    if(n===2)setGigi('dreamy');
    if(n===3)setGigi('thumbsup');
  }}
  let stream=null,photos=[],shooting=false;
  async function startCam(){{
    try{{stream=await navigator.mediaDevices.getUserMedia({{video:{{facingMode:'user',width:{{ideal:1280}},height:{{ideal:720}}}},audio:false}});}}
    catch{{try{{stream=await navigator.mediaDevices.getUserMedia({{video:true,audio:false}});}}
    catch{{setStatus('⚠️ Camera not available.');return;}}}}
    $('camera-video').srcObject=stream;
  }}
  function stopCam(){{if(stream){{stream.getTracks().forEach(t=>t.stop());stream=null;}}}}
  function capture(){{
    const v=$('camera-video'),c=$('camera-canvas');
    c.width=v.videoWidth||640;c.height=v.videoHeight||480;
    const ctx=c.getContext('2d');
    ctx.translate(c.width,0);ctx.scale(-1,1);
    ctx.drawImage(v,0,0,c.width,c.height);
    return c.toDataURL('image/jpeg',.92);
  }}
  function flash(){{const e=$('flash-ov');e.classList.add('flash');setTimeout(()=>e.classList.remove('flash'),380);}}
  function setStatus(m){{$('s2-status').textContent=m}}
  function resetStrip(){{for(let i=0;i<3;i++){{$(`s2-slot-${{i}}`).innerHTML='📷';$(`dot-${{i}}`).classList.remove('on');}}}}
  const sleep=ms=>new Promise(r=>setTimeout(r,ms));
  async function countdown(s){{
    const ov=$('cdown-overlay'),num=$('cdown-num');
    ov.classList.add('visible');
    for(let n=s;n>=1;n--){{num.textContent=n;num.style.animation='none';num.offsetHeight;num.style.animation='';await sleep(1000);}}
    ov.classList.remove('visible');
  }}
  async function shoot(){{
    if(shooting)return;
    shooting=true;photos=[];resetStrip();$('btn-done').disabled=true;
    for(let i=0;i<3;i++){{
      setStatus(`📸 Photo ${{i+1}} of 3 — Get ready!`);
      await sleep(400);await countdown(3);setStatus('✨ Snap!');
      const url=capture();flash();photos.push(url);
      const slot=$(`s2-slot-${{i}}`);slot.innerHTML='';
      const img=document.createElement('img');img.src=url;slot.appendChild(img);
      $(`dot-${{i}}`).classList.add('on');
      if(i<2)await sleep(900);
    }}
    setStatus('🎉 All done! Click DONE or START again to retake.');
    $('btn-done').disabled=false;shooting=false;
  }}
  // Strip template + slot positions
  const STRIP_W=710, STRIP_H=2034;
  const SLOTS=[[50,51,659,532],[50,572,659,1053],[50,1093,659,1574]];
  const STRIP_B64='data:image/png;base64,{b_st}';

  function loadImg(src){{
    return new Promise((res,rej)=>{{
      const i=new Image();
      i.crossOrigin='anonymous';
      i.onload=()=>res(i);
      i.onerror=(e)=>rej(e);
      i.src=src;
    }});
  }}

  async function buildStrip(photoDataUrls){{
    const canvas=document.createElement('canvas');
    canvas.width=STRIP_W; canvas.height=STRIP_H;
    const ctx=canvas.getContext('2d');

    // Load and draw template
    const tpl=await loadImg(STRIP_B64);
    ctx.drawImage(tpl,0,0,STRIP_W,STRIP_H);

    // Draw each photo into its slot
    for(let i=0;i<3;i++){{
      const [x1,y1,x2,y2]=SLOTS[i];
      const sw=x2-x1, sh=y2-y1;
      const photo=await loadImg(photoDataUrls[i]);
      const scale=Math.max(sw/photo.naturalWidth, sh/photo.naturalHeight);
      const dw=photo.naturalWidth*scale, dh=photo.naturalHeight*scale;
      const ox=x1+(sw-dw)/2, oy=y1+(sh-dh)/2;
      ctx.save();
      ctx.beginPath(); ctx.rect(x1,y1,sw,sh); ctx.clip();
      ctx.drawImage(photo,ox,oy,dw,dh);
      ctx.restore();
    }}

    // Draw template on top so decorations overlay photos
    ctx.drawImage(tpl,0,0,STRIP_W,STRIP_H);
    return canvas.toDataURL('image/jpeg',0.92);
  }}

  async function done(){{
    if(photos.length<3){{setStatus('⚠️ Take all 3 photos first!');return;}}

    // Build strip BEFORE switching screens (photos still valid data URLs)
    $('btn-done').disabled=true;
    $('btn-start-2').disabled=true;
    setStatus('🎨 Building your strip...');

    let composited=null;
    try{{
      composited=await buildStrip(photos);
    }}catch(e){{
      console.error('Strip build error:',e);
    }}

    showScreen(3); stopCam();
    $('btn-done').disabled=false;
    $('btn-start-2').disabled=false;

    const si=$('s3-strip-img');
    if(composited){{
      si.src=composited;
      si.style.opacity='1';
    }}

    $('qr-box').innerHTML='<div class="qr-load">Generating<br>your QR...</div>';
    try{{
      const res=await fetch('/api/save-session',{{
        method:'POST',
        headers:{{'Content-Type':'application/json'}},
        body:JSON.stringify({{photos, compositedStrip:composited}})
      }});
      const d=await res.json();
      if(d.qrCode)$('qr-box').innerHTML=`<img src="${{d.qrCode}}" alt="QR"/>`;
      else $('qr-box').innerHTML='<div class="qr-load">Failed to generate QR.</div>';
    }}catch(e){{
      console.error(e);
      $('qr-box').innerHTML='<div class="qr-load">Error — check connection.</div>';
    }}
  }}
  $('btn-start-1').addEventListener('click',async()=>{{showScreen(2);shooting=false;photos=[];resetStrip();$('btn-done').disabled=true;setStatus('Press START to begin!');await startCam();}});
  $('btn-start-2').addEventListener('click',()=>shoot());
  $('btn-done').addEventListener('click',()=>{{if(!shooting)done();}});
  $('btn-take-again').addEventListener('click',async()=>{{photos=[];shooting=false;showScreen(2);resetStrip();$('btn-done').disabled=true;setStatus('Press START to begin!');await startCam();}});
</script>
</body>
</html>"""

if __name__ == "__main__":
    main()
