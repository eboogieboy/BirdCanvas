from pathlib import Path

root = Path("code")

replacements = {
    'Path("output")': 'OUTPUT_DIR',
    'Path("data")': 'DATA_DIR',
    'Path("backups")': 'BACKUP_DIR',
}

imports = {
    "OUTPUT_DIR": "from paths import OUTPUT_DIR",
    "DATA_DIR": "from paths import DATA_DIR",
    "BACKUP_DIR": "from paths import BACKUP_DIR",
}

for file in root.glob("*.py"):
    if file.name in ("paths.py", "server.py"):
        continue

    text = file.read_text()

    changed = False
    needed = []

    for old, new in replacements.items():
        if old in text:
            text = text.replace(old, new)
            changed = True
            needed.append(new)

    if changed:
        lines = text.splitlines()

        existing = {
            line.strip()
            for line in lines
            if line.startswith("from paths import")
        }

        insert_at = 0
        for i, line in enumerate(lines):
            if line.startswith("from ") or line.startswith("import "):
                insert_at = i + 1

        for symbol in sorted(set(needed)):
            imp = imports[symbol]
            if imp not in existing:
                lines.insert(insert_at, imp)
                insert_at += 1

        file.write_text("\n".join(lines) + "\n")
        print(file.name)
