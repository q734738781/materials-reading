"""Export reading cards into a static, PDF-free GitHub Pages site."""
import argparse, html, json, re, shutil, zlib, struct
from collections import Counter
from pathlib import Path
from urllib.parse import unquote, urlsplit
from markdown_it import MarkdownIt

ROOT=Path(__file__).resolve().parents[1]
TOPICS={'T1':'材料生成与逆向设计','T2':'合成与工艺','T3':'自主实验闭环','T4':'性质、表征与材料表示','T5':'电子结构学习','T6':'机器学习势训练与泛化','T7':'采样与高性能原子模拟','T8':'智能体技术与科研系统','T9':'非平衡态化学与微化工','T10':'跨尺度催化'}
md=MarkdownIt('commonmark',{'html':False,'breaks':False}).enable('table')
parser=argparse.ArgumentParser();parser.add_argument('--source',type=Path,required=True);parser.add_argument('--queue',type=Path)
args=parser.parse_args();source=args.source.resolve();dist=ROOT/'dist';dist.mkdir(exist_ok=True)
known={}
if args.queue:
 for x in json.loads(args.queue.read_text(encoding='utf-8'))['items'].values():
  if x.get('card') and x.get('primary_topic'):known[str(Path(x['card']).resolve()).casefold()]=x['primary_topic']

def topic_for(path,title,text):
 if '10.1021/jacs.6c12929' in text[:2500] or re.search(r'跨尺度催化|多尺度催化|multi.scale catalysis',title,re.I):return 'T10'
 if not re.search(r'message.passing potentials|active learning|interatomic|机器学习势',title,re.I) and re.search(r'非平衡|non.?equilibrium|微化工|微反应器|微流控|microreactor|microfluidic|耗散自组织',title+' '+path.stem,re.I):return 'T9'
 if str(path.resolve()).casefold() in known:return known[str(path.resolve()).casefold()]
 s=(title+' '+text[:2200]).lower()
 for topic,pattern in [('T8',r'agent|智能体|科研系统|procedural memory'),('T3',r'自主实验|self.driving|autonomous laborator|实验闭环'),('T5',r'wavefunction|electronic structure|电子结构|密度泛函|tight.binding|薛定谔|多参考'),('T6',r'interatomic|force.field|mlip|mlff|机器学习势|机器学习力场|势函数|神经网络势'),('T7',r'sampling|增强采样|molecular dynamics|分子动力学|原子模拟'),('T1',r'逆向设计|inverse design|generation|生成|diffusion model|扩散模型'),('T2',r'synthesis|合成|工艺'),('T4',r'.')]:
  if re.search(pattern,s):return topic

def clean(text):
 text=re.sub(r'<!--.*?-->','',text,flags=re.S)
 text=re.sub(r'(?m)^.*(?:实际阅读|原页码|已核验|已回读|读取版本|未读\s*SI|本地路径|(?<![A-Za-z])[A-Z]:[\\/]|file://).*(?:\n|$)','',text)
 text=re.sub(r'(?mi)^\s*(?:[-*]\s*)?(?:\*\*)?(?:PDF|文件|文件名|阅读范围|精读范围)(?:\*\*)?\s*[:：].*(?:\n|$)','',text)
 text=re.sub(r'`[^`\n]*\.pdf`','',text,flags=re.I)
 return text

def official(text):
 links=re.findall(r'https?://[^\s<>\)\]"，。]+',text)
 for link in links:
  if 'doi.org/' in link:return link.rstrip('；;*')
 for link in links:
  if 'arxiv.org/abs/' in link:return link
 hit=re.search(r'10\.\d{4,9}/[A-Za-z0-9._;()/+-]+',text[:4000])
 if hit:return 'https://doi.org/'+hit.group().rstrip(').；。')
 hit=re.search(r'\b(2[0-9][01][0-9]\.\d{4,5})(?:v\d+)?',text[:3000])
 return 'https://arxiv.org/abs/'+hit.group(1) if hit else (links[0] if links else '')

def frame(title,body,depth=0):
 pre='../' if depth else './'
 return '<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+html.escape(title)+' · AI for Materials 文献精读</title><meta name="description" content="AI for Materials、原子模拟与科研智能体的中文文献解读"><link rel="stylesheet" href="'+pre+'style.css"><link rel="icon" href="'+pre+'icon.svg" type="image/svg+xml"></head><body><header><a class="brand" href="'+pre+'index.html"><span class="mark">M</span><span>AI for Materials<small>文献精读 / RESEARCH NOTES</small></span></a><a class="header-link" href="'+pre+'index.html#library">浏览文献 <span>↗</span></a></header>'+body+'<footer><span>AI for Materials 文献精读</span><span>材料 · 模拟 · 智能体</span></footer></body></html>'

entries=[];assets={};skipped=[]
paths=sorted(source.rglob('*.md'),reverse=True)
seen=set()
for path in paths:
 text=path.read_text(encoding='utf-8-sig');title=re.search(r'^#\s+(.+)',text,re.M).group(1).strip()
 # Ignore collection indexes or workflow documents, never publish arbitrary directory contents.
 if len(text)<700 or re.search(r'^(?:README|索引|目录|日报汇总)',title,re.I):skipped.append(str(path.relative_to(source)));continue
 ref=official(text);identity=ref.lower() if ref else re.sub(r'\W','',title).lower()
 if identity in seen:skipped.append(str(path.relative_to(source)));continue
 seen.add(identity)
 datehit=re.search(r'(20\d{6})',str(path.relative_to(source)))
 rawdate=datehit.group(1) if datehit else '00000000';date=(rawdate[:4]+'-'+rawdate[4:6]+'-'+rawdate[6:]) if datehit else ''
 slug=rawdate+'-'+format(zlib.crc32(str(path.relative_to(source)).encode()),'08x')
 topic=topic_for(path,title,text)
 text=clean(text)
 text=re.sub(r'^#\s+.+\n','',text,count=1)
 math=[]
 def save_math(m):
  math.append(m.group(0));return 'MATHBLOCKTOKEN'+str(len(math)-1)+'ENDTOKEN'
 protected=re.sub(r'\\\[.*?\\\]|\\\(.*?\\\)|\$\$.*?\$\$|(?<!\$)\$[^\n$]+\$(?!\$)',save_math,text,flags=re.S)
 tokens=md.parse(protected)
 sections=[];seq=0;figures=0
 for i,t in enumerate(tokens):
  if t.type=='heading_open':
   seq+=1;t.attrSet('id','section-'+str(seq))
   if i+1<len(tokens):sections.append((t.tag,tokens[i+1].content,'section-'+str(seq)))
  if t.type!='inline' or not t.children:continue
  for child in t.children:
   if child.type=='link_open':
    href=child.attrGet('href') or ''
    if href.startswith(('http://','https://')):
     child.attrSet('target','_blank');child.attrSet('rel','noopener noreferrer')
    elif href.startswith('#'):pass
    else:child.attrSet('href',ref or '../index.html')
   if child.type=='image':
    href=child.attrGet('src') or '';u=urlsplit(href)
    if u.scheme in ('http','https'):
     child.attrSet('loading','lazy');continue
    img=(path.parent/unquote(u.path.replace('\\','/'))).resolve()
    if not img.is_relative_to(source) or img.suffix.lower() not in ('.png','.jpg','.jpeg','.webp','.gif','.svg') or not img.is_file():
     child.type='text';child.content='〔原图请见论文〕';child.children=None;continue
    rel='assets/'+slug+'/'+img.name
    assets[rel]=img;child.attrSet('src','../'+rel);child.attrSet('loading','lazy');figures+=1
    if img.suffix.lower()=='.png':
     with img.open('rb') as f:header=f.read(24)
     if header[:8]==b'\x89PNG\r\n\x1a\n':
      width,height=struct.unpack('>II',header[16:24]);child.attrSet('width',str(width));child.attrSet('height',str(height))
 bodyhtml=md.renderer.render(tokens,md.options,{})
 for n,formula in enumerate(math):bodyhtml=bodyhtml.replace('MATHBLOCKTOKEN'+str(n)+'ENDTOKEN',html.escape(formula))
 # Public metadata must never contain workstation paths or local PDF references.
 bodyhtml=re.sub(r'<a\b[^>]*>\s*(?:原文\s*)?PDF\s*</a>','',bodyhtml,flags=re.I)
 if re.search(r'(?:(?<![A-Za-z])[A-Z]:[\\/]+(?:Users|Desktop|Documents|迅雷下载|Anaconda|python_projects)|file://|mailto:|sk-or-v1-)',bodyhtml,re.I):raise RuntimeError('Public-data check failed: '+path.name)
 toc=''.join('<a href="#'+sid+'">'+html.escape(label)+'</a>' for tag,label,sid in sections if tag=='h2')
 meta='<span>'+html.escape(TOPICS[topic])+'</span><span>'+('收录 '+date if date else '专题精读')+'</span><span>'+str(max(1,round(len(text)/650)))+' 分钟阅读</span>'
 original='<a class="original" href="'+html.escape(ref,quote=True)+'" target="_blank" rel="noopener noreferrer">论文原文 ↗</a>' if ref else ''
 page=frame(title,'<main class="article-layout"><aside><a href="../index.html#library">← 返回文献库</a><nav aria-label="文章目录">'+toc+'</nav></aside><article><div class="eyebrow">RESEARCH NOTE / '+topic+'</div><h1>'+html.escape(title)+'</h1><div class="article-meta">'+meta+'</div>'+original+'<div class="prose">'+bodyhtml+'</div></article></main>'+'''<script>window.MathJax={tex:{inlineMath:[['$','$'],['\\\\(','\\\\)']],displayMath:[['$$','$$'],['\\\\[','\\\\]']]},options:{skipHtmlTags:['script','noscript','style','textarea','pre','code']}};</script><script defer src="https://cdn.jsdelivr.net/npm/mathjax@3.2.2/es5/tex-mml-chtml.js"></script>''',1)
 (dist/'notes').mkdir(exist_ok=True);(dist/'notes'/(slug+'.html')).write_text(page,encoding='utf-8')
 plain=re.sub(r'!\[[^\]]*\]\([^)]*\)|\[[^\]]*\]\([^)]*\)|[#*`>|]',' ',text)
 paras=[re.sub(r'\s+',' ',p).strip() for p in plain.split('\n\n')]
 excerpt=next((p for p in paras if len(p)>80 and not re.search('作者|DOI|论文|原文|原题|来源|出处|文献信息',p[:30])),next((p for p in paras if len(p)>60),''))[:160]
 entries.append(dict(id=slug,title=title,date=date,topic=topic,topicName=TOPICS[topic],excerpt=excerpt,url='notes/'+slug+'.html',original=ref,search=title+' '+plain[:16000],figures=figures))

for rel,img in assets.items():
 target=dist/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(img,target)
entries.sort(key=lambda x:(x['date'],x['title']),reverse=True)
(dist/'catalog.json').write_text(json.dumps(entries,ensure_ascii=False),encoding='utf-8')
data=json.dumps(entries,ensure_ascii=False).replace('<','\\u003c').replace('\u2028','\\u2028').replace('\u2029','\\u2029')
(dist/'catalog.js').write_text('window.CATALOG='+data+';',encoding='utf-8')
body='''<main><section class="hero"><div class="eyebrow">MATERIALS · SIMULATION · AGENTS</div><h1>读懂方法，<br>发现下一步研究。</h1><p>从材料设计到原子模拟，从自主实验到科研智能体。<br>沿着具体问题、方法与关键发现，理解值得借鉴的研究。</p><div class="stats"><div><strong>'''+str(len(entries))+'''</strong><span>篇文献解读</span></div><div><strong>'''+str(len(TOPICS))+'''</strong><span>个研究话题</span></div><div><strong>'''+entries[0]['date'][5:].replace('-',' / ')+'''</strong><span>最近收录</span></div></div><div class="hero-visual" aria-hidden="true"><svg viewBox="0 0 400 360"><g fill="none" stroke="#ced9cd" stroke-width="1.3"><path d="M80 100L200 42 320 100 320 245 200 310 80 245Z M80 100L200 170 320 100 M200 170V310 M200 42V170 M80 245L200 170 320 245"/><ellipse cx="200" cy="175" rx="170" ry="55" transform="rotate(-30 200 175)"/></g><g fill="#456c53"><circle cx="80" cy="100" r="10"/><circle cx="200" cy="42" r="9"/><circle cx="320" cy="100" r="13"/><circle cx="200" cy="170" r="19"/><circle cx="320" cy="245" r="9"/><circle cx="200" cy="310" r="12"/><circle cx="80" cy="245" r="13"/></g><circle cx="200" cy="170" r="31" fill="none" stroke="#456c53" stroke-opacity=".25"/><text x="25" y="340" font-size="10" fill="#839181" letter-spacing="3">STRUCTURE → METHOD → INSIGHT</text></svg></div></section><section id="library"><div class="library-head"><div><div class="eyebrow">THE READING LIBRARY</div><h2>文献库</h2></div><label class="search"><span>⌕</span><input id="search" type="search" placeholder="搜索论文、方法或关键词" aria-label="搜索论文"></label></div><div class="topics" id="topics" role="group" aria-label="话题筛选"></div><div class="result-line"><span id="result-count" aria-live="polite"></span><label>排序 <select id="sort" aria-label="排序"><option value="new">最新收录</option><option value="old">最早收录</option><option value="title">标题</option></select></label></div><div id="results" class="cards"></div><div class="pagination"><button id="more" type="button">继续浏览 ↓</button></div></section></main><script src="catalog.js"></script><script src="app.js"></script>'''
(dist/'index.html').write_text(frame('首页',body),encoding='utf-8')
(dist/'.nojekyll').touch()
stats=dict(cards=len(entries),images=len(assets),image_bytes=sum(p.stat().st_size for p in assets.values()),skipped=len(skipped),topics=dict(Counter(x['topic'] for x in entries)))
(ROOT/'export-summary.json').write_text(json.dumps(stats,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(stats,ensure_ascii=False))
