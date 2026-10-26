import json,collections,re,sys
sys.stdout.reconfigure(encoding='utf-8')
UU=re.compile(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}',re.I)
d=json.load(open(sys.argv[1],encoding='utf-8'))
C=collections.defaultdict(list);H=collections.defaultdict(list)
for r in d:
  for x in r['clipped']:
    C[(r['batch'],r['screen'],x.get('cls'),x.get('tag'),UU.sub('<u>',(x.get('text') or ''))[:45])].append((r['case'],r['width'],x.get('sw'),x.get('cw'),x.get('sh'),x.get('ch')))
  for x in r['hscroll']:
    H[(r['batch'],r['screen'],x.get('cls'),x.get('panel'))].append((r['case'],r['width'],x.get('sw'),x.get('cw')))
print('CLIPPED distinct',len(C))
for k,v in sorted(C.items(),key=str): print(k,len(v),v[:3])
print('HSCROLL distinct',len(H))
for k,v in sorted(H.items(),key=str): print(k,len(v),v[:3])
print('ovX>0',[(r['screen'],r['case'],r['width'],r['overflowX']) for r in d if r['overflowX']>0])
print('clipped len10',[(r['screen'],r['case'],r['width']) for r in d if len(r['clipped'])>=10])
print('hscroll len10',[(r['screen'],r['case'],r['width']) for r in d if len(r['hscroll'])>=10])
