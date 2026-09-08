import os
import shutil

os.makedirs('src', exist_ok=True)

mapping = {
    'campaign_agent/agents': 'src/agents',
    'campaign_agent/integrations': 'src/connectors',
    'campaign_agent/core': 'src/core',
    'campaign_agent/schemas': 'src/models',
    'campaign_agent/workflows': 'src/pipelines',
    'campaign_agent/tools': 'src/plugins',
    'campaign_agent/api/routers': 'src/routers',
    'campaign_agent/api/gateway.py': 'src/gateway.py',
    'tests': 'src/tests'
}

for src_path, dest_path in mapping.items():
    if os.path.exists(src_path):
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        shutil.move(src_path, dest_path)

for root, dirs, files in os.walk('src'):
    for f in files:
        if f.endswith('.py'):
            filepath = os.path.join(root, f)
            with open(filepath, 'r', encoding='utf-8') as file:
                content = file.read()
            
            content = content.replace('from campaign_agent.', 'from src.')
            content = content.replace('import campaign_agent.', 'import src.')
            content = content.replace('from campaign_agent import ', 'from src import ')
            content = content.replace('"campaign_agent.', '"src.')
            content = content.replace("'campaign_agent.", "'src.")
            
            content = content.replace('src.integrations', 'src.connectors')
            content = content.replace('src.schemas', 'src.models')
            content = content.replace('src.workflows', 'src.pipelines')
            content = content.replace('src.tools', 'src.plugins')
            content = content.replace('src.api.routers', 'src.routers')
            content = content.replace('src.api.gateway', 'src.gateway')
            
            with open(filepath, 'w', encoding='utf-8') as file:
                file.write(content)

if os.path.exists('campaign_agent'):
    shutil.rmtree('campaign_agent')

print("Refactoring complete.")
