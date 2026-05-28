#!/usr/bin/env python3
"""
Fixes the already-generated public/index.html directly — no need to rerun update_ui.py.
The broken GIGI JS object has literal {b_sh}, {b_dr}, {b_tu} instead of real base64 data
because of a missing double-brace bug in the f-string template.

This script:
  1. Reads the broken index.html
  2. Re-processes only the 3 affected images (shy, dreamy, thumbsup) + logo
  3. Patches just those broken lines in-place
  4. Writes back — no full rebuild needed
"""
import base64, io, re, shutil, sys
from pathlib import Path

try:
    from PIL import Image, ImageFilter
    import numpy as np
except ImportError:
    print("Missing deps. Run: pip install Pillow numpy")
    sys.exit(1)

BASE        = Path(__file__).parent
HTML_FILE   = BASE / "public" / "index.html"
BACKUP_FILE = BASE / "public" / "index.html.bak2"

IMG_SHY      = BASE / "gigi_shy_old.png"
IMG_DREAMY   = BASE / "gigi_dreamy_old.png"
IMG_THUMBSUP = BASE / "gigi_thumbsup_old.png"
IMG_LOGO     = BASE / "shebuilds_logo_final.png"

def remove_black_bg_smooth(path, resize_width=None, threshold=30):
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
    if not HTML_FILE.exists():
        print("❌  public/index.html not found. Run update_ui.py first.")
        sys.exit(1)

    missing = [p for p in [IMG_SHY, IMG_DREAMY, IMG_THUMBSUP, IMG_LOGO] if not p.exists()]
    if missing:
        print("❌  Missing images:", [p.name for p in missing])
        sys.exit(1)

    print("🌸  Fixing public/index.html (no full rebuild needed)")
    print("─" * 42)
    print("🖌️   Processing 4 images...")

    sh = remove_black_bg_smooth(IMG_SHY,       resize_width=380)
    dr = remove_black_bg_floodfill(IMG_DREAMY, resize_width=500)
    tu = remove_black_bg_smooth(IMG_THUMBSUP,  resize_width=500)
    lg = load_as_is(IMG_LOGO,                  resize_width=620)

    for label, data in [("shy",sh),("dreamy",dr),("thumbsup",tu),("logo",lg)]:
        print(f"    {label:<12}: {len(data)//1024} KB")

    b_sh = b64(sh)
    b_dr = b64(dr)
    b_tu = b64(tu)
    b_lg = b64(lg)

    shutil.copy(HTML_FILE, BACKUP_FILE)
    print(f"💾  Backed up → index.html.bak2")

    html = HTML_FILE.read_text(encoding="utf-8")

    # Fix broken GIGI JS object (literal placeholders -> real base64)
    html = re.sub(r"shy:\s*'data:image/png;base64,\{b_sh\}'",
                  f"shy:     'data:image/png;base64,{b_sh}'", html)
    html = re.sub(r"dreamy:\s*'data:image/png;base64,\{b_dr\}'",
                  f"dreamy:  'data:image/png;base64,{b_dr}'", html)
    html = re.sub(r"thumbsup:'data:image/png;base64,\{b_tu\}'",
                  f"thumbsup:'data:image/png;base64,{b_tu}'", html)

    # Fix logo src (re-embed with load_as_is version)
    html = re.sub(r'(<img class="sb-logo"[^>]*src=")data:image/png;base64,[A-Za-z0-9+/=]+"',
                  f'\\1data:image/png;base64,{b_lg}"', html)

    HTML_FILE.write_text(html, encoding="utf-8")
    print("\n✅  Done! Refresh http://localhost:3000")

if __name__ == "__main__":
    main()
