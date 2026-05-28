from pathlib import Path
import shutil

project_dir = Path(__file__).parent
server_js = project_dir / "server.js"
public_dir = project_dir / "public"

# -------------------------
# FAILSAFE BACKUPS
# -------------------------

backup_dir = project_dir / "backup_before_strip_replace"
backup_dir.mkdir(exist_ok=True)

server_backup = backup_dir / "server.js.bak"
shutil.copy(server_js, server_backup)

public_backup = backup_dir / "public_backup"

if public_dir.exists() and not public_backup.exists():
    shutil.copytree(public_dir, public_backup)

print("Backup created successfully.")

# -------------------------
# COPY DESIGN
# -------------------------

source_design = project_dir / "Photostrip (1).png"
target_design = public_dir / "custom_strip.png"

shutil.copy(source_design, target_design)

# -------------------------
# MODIFY server.js
# -------------------------

content = server_js.read_text(encoding="utf-8")

start = content.find("const stripHtml = `")
end = content.find(
    'fs.writeFileSync(path.join(sessionDir, "strip.html"), stripHtml);'
)

if start == -1 or end == -1:
    raise Exception("Could not find stripHtml block inside server.js")

new_block = r"""const stripHtml = `<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8"/>
<title>SheBuilds Photobooth Strip</title>

<style>
*{
  margin:0;
  padding:0;
  box-sizing:border-box;
}

body{
  display:flex;
  justify-content:center;
  align-items:center;
  background:#f3d9e8;
  padding:20px;
}

.strip{
  position:relative;
  width:720px;
  height:2048px;
  background:url('custom_strip.png') no-repeat center center;
  background-size:cover;
}

.photo{
  position:absolute;
  left:49px;
  width:641px;
  height:482px;
  object-fit:cover;
  border-radius:2px;
}

.p1{ top:52px; }
.p2{ top:573px; }
.p3{ top:1095px; }

</style>
</head>

<body>
<div class="strip">
  <img class="photo p1" src="photo_1.jpg"/>
  <img class="photo p2" src="photo_2.jpg"/>
  <img class="photo p3" src="photo_3.jpg"/>
</div>
</body>
</html>`;
"""

updated = content[:start] + new_block + "\n    " + content[end:]

server_js.write_text(updated, encoding="utf-8")

print("Done! Photostrip design replaced successfully.")

print("\nIf something breaks, restore using:")
print("copy backup_before_strip_replace\\server.js.bak server.js")