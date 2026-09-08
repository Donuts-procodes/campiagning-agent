import os

root_dirs = ['app', 'tests']

for d in root_dirs:
    for root, dirs, files in os.walk(d):
        for f in files:
            if f.endswith('.py'):
                filepath = os.path.join(root, f)
                with open(filepath, 'r', encoding='utf-8') as file:
                    content = file.read()
                
                content = content.replace('from app.', 'from campaign_agent.')
                content = content.replace('import app.', 'import campaign_agent.')
                content = content.replace('from app import ', 'from campaign_agent import ')
                content = content.replace('"app.', '"campaign_agent.')
                content = content.replace("'app.", "'campaign_agent.")
                content = content.replace('app.main:app', 'campaign_agent.main:app')
                content = content.replace('app.main:api_router', 'campaign_agent.main:api_router')
                
                with open(filepath, 'w', encoding='utf-8') as file:
                    file.write(content)

with open('pyproject.toml', 'r', encoding='utf-8') as f:
    content = f.read()
    content = content.replace('packages = ["app"]', 'packages = ["campaign_agent"]')
with open('pyproject.toml', 'w', encoding='utf-8') as f:
    f.write(content)

try:
    os.rename('app', 'campaign_agent')
except FileExistsError:
    pass
print("Refactoring complete.")
