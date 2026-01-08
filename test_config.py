"""config.jsonの検証テスト"""
import json

try:
    with open('config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    print('✓ Config is valid!')
    print(f'  Total pages: {config.get("total_pages")}')
    print(f'  Output dir: {config.get("output_dir")}')
    print(f'  Page delay: {config.get("page_delay")}s')
    print(f'  Fullscreen: {config.get("fullscreen")}')
    print(f'  Page turn direction: {config.get("page_turn_direction")}')
    
except Exception as e:
    print(f'✗ Error: {e}')
