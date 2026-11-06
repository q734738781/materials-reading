"""Validate the exact public artifact, including subpath-safe links and PDF exclusion."""
import json,re
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import unquote,urlsplit
root=Path(__file__).resolve().parents[1]/'dist'
errors=[]
class Check(HTMLParser):
 def handle_starttag(self,tag,attrs):
  for key,value in attrs:
   if key not in ('href','src') or not value or value.startswith(('https://','http://','#','data:')):continue
   if value.startswith('/'):errors.append((self.path.name,'root URL is unsafe for project Pages',value))
   dest=(self.path.parent/unquote(urlsplit(value).path)).resolve()
   if not dest.is_file():errors.append((self.path.name,'broken link',value))
for p in root.rglob('*.html'):
 text=p.read_text(encoding='utf-8');h=Check();h.path=p;h.feed(text)
 if re.search(r'(?<![A-Za-z])[A-Z]:[\\/]+(?:Users|Desktop|迅雷下载)|file://|sk-or-v1-',text,re.I):errors.append((p.name,'private local reference'))
 if 'MATHBLOCKTOKEN' in text:errors.append((p.name,'unexpanded equation'))
for p in root.rglob('*'):
 if p.is_file() and p.suffix.lower() not in ('.html','.css','.js','.json','.svg','.png','.jpg','.jpeg','.webp','.gif') and p.name!='.nojekyll':errors.append((p.name,'unexpected file type'))
catalog=json.loads((root/'catalog.json').read_text(encoding='utf-8'))
assert len({x['id'] for x in catalog})==len(catalog)
assert all((root/x['url']).is_file() for x in catalog)
assert not errors,errors[:10]
print(f'PASS: {len(catalog)} cards; all local links resolve; no PDF/private paths; project-subpath compatible.')
