from pathlib import Path
p=Path('benchmark_runner.py');s=p.read_text(encoding='utf-8-sig');s=s.replace("logs=subprocess.check_output", "Path(out/'window.json').write_text(json.dumps({'start':epoch,'end':end}))\n logs=subprocess.check_output")
p.write_text(s,encoding='utf8')
# Keep generated helpers out of the user-facing root inventory.
Path('.gitignore').write_text('.venv/\n__pycache__/\n*.pyc\nresultados/orders.jsonl\n')
