import subprocess
import os

env = os.environ.copy()
env['PYTHONIOENCODING'] = 'utf-8'
env['PYTHONUTF8'] = '1'

with open('submission/screenshots/demo_output.txt', 'w', encoding='utf-8') as f:
    subprocess.run(['.\\.venv\\Scripts\\python.exe', 'bonus/demo.py'], stdout=f, stderr=subprocess.STDOUT, text=True, env=env)
