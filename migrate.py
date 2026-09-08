import os
import shutil
import glob

# Rename backend to app
if os.path.exists("backend") and not os.path.exists("app"):
    os.rename("backend", "app")

# Files to update
files_to_update = []
files_to_update.append("Dockerfile")
files_to_update.append("pyproject.toml")
files_to_update.extend(glob.glob("app/**/*.py", recursive=True))
files_to_update.extend(glob.glob("tests/**/*.py", recursive=True))

for filepath in files_to_update:
    if not os.path.exists(filepath):
        continue
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Specific replacements
    new_content = content.replace("backend.", "app.")
    new_content = new_content.replace("backend/", "app/")
    new_content = new_content.replace('packages = ["backend"]', 'packages = ["app"]')
    
    if new_content != content:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(new_content)
        print(f"Updated {filepath}")

# Create new directory structure
os.makedirs("app/api/routers", exist_ok=True)
os.makedirs("app/services", exist_ok=True)
os.makedirs("app/repositories", exist_ok=True)
os.makedirs("app/schemas", exist_ok=True)
os.makedirs("app/dependencies", exist_ok=True)

print("Migration script completed.")
