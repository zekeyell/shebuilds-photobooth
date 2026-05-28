#!/usr/bin/env python3
"""
Fixes two bugs in update_ui.py:
  1. Single braces {b_sh}, {b_dr}, {b_tu} in f-string -> not substituted (images blank)
  2. shebuilds logo processed with remove_black_bg_smooth -> use load_as_is instead
Run from: C:\\dev\\shebuilds-photobooth\\
"""
from pathlib import Path

target = Path(__file__).parent / "update_ui.py"
text   = target.read_text(encoding="utf-8")
orig   = text

# Fix 1: single braces in GIGI JS object -> double braces
text = text.replace(
    "    shy:     'data:image/png;base64,{b_sh}',",
    "    shy:     'data:image/png;base64,{{b_sh}}',",
)
text = text.replace(
    "    dreamy:  'data:image/png;base64,{b_dr}',",
    "    dreamy:  'data:image/png;base64,{{b_dr}}',",
)
text = text.replace(
    "    thumbsup:'data:image/png;base64,{b_tu}',",
    "    thumbsup:'data:image/png;base64,{{b_tu}}',",
)

# Fix 2: logo — use load_as_is instead of remove_black_bg_smooth
text = text.replace(
    "    lg = remove_black_bg_smooth(IMG_LOGO,      resize_width=620)",
    "    lg = load_as_is(IMG_LOGO,                  resize_width=620)",
)

# Fix 3: dreamy path
text = text.replace(
    'IMG_DREAMY   = SCRIPT_DIR / "gigi_dreamy_fixed2.png"   # fixed eyes',
    'IMG_DREAMY   = SCRIPT_DIR / "gigi_dreamy_old.png"',
)
text = text.replace(
    '"gigi_dreamy_fixed2.png":  IMG_DREAMY,',
    '"gigi_dreamy_old.png":     IMG_DREAMY,',
)

if text == orig:
    print("No changes made — already fixed or pattern not found.")
else:
    target.write_text(text, encoding="utf-8")
    print("Fixed update_ui.py:")
    print("  - GIGI JS object now uses double braces for b_sh, b_dr, b_tu")
    print("  - shebuilds logo now uses load_as_is")
    print("  - dreamy image path corrected to gigi_dreamy_old.png")
    print("\nNow run:  python update_ui.py")
