import os
import glob
import re

for filepath in glob.glob("app/**/*.py", recursive=True):
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    new_lines = []
    for line in lines:
        # Strip full line comments
        stripped = line.lstrip()
        if stripped.startswith("#"):
            continue
        
        # Strip inline comments (basic regex, avoids # inside strings if possible, but simplistic)
        # Actually a safer way is just to not do inline comments if it's too risky, but let's do a simple split
        # We will only remove full line comments to be safe and avoid breaking code strings
        new_lines.append(line)
        
    with open(filepath, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

print("Comments removed.")
