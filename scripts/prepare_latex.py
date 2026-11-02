import requests,zipfile,io,json,hashlib
from pathlib import Path
root=Path('.tools/tectonic');root.mkdir(parents=True,exist_ok=True)
if not (root/'tectonic.exe').exists():
 release=requests.get('https://api.github.com/repos/tectonic-typesetting/tectonic/releases/tags/tectonic%400.17.0',timeout=30);release.raise_for_status();data=release.json()
 asset=next(a for a in data['assets'] if a['name']=='tectonic-0.17.0-x86_64-pc-windows-msvc.zip')
 response=requests.get(asset['browser_download_url'],timeout=90);response.raise_for_status();content=response.content
 archive=zipfile.ZipFile(io.BytesIO(content))
 binary=next(n for n in archive.namelist() if n.endswith('tectonic.exe'));(root/'tectonic.exe').write_bytes(archive.read(binary))
 (root/'manifest.json').write_text(json.dumps(dict(version='0.17.0',url=asset['browser_download_url'],archive_sha256=hashlib.sha256(content).hexdigest()),indent=2))
print('Compilador portable preparado')
