"""Apply compare3 inner-overflow logic (sig of hscroll by (cls,panel), clipped by (cls,text[:30])) to batches 01-07."""
import json,sys,os,re
sys.stdout.reconfigure(encoding='utf-8')
A='C:/Users/assef/Bineyame/AssetOpsV1-plan2/.agent'
NEW=A+'/post-W6-final-recapture'; OLD=A+'/post-W6-audit'
UU=re.compile(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}',re.I)
def load(p): return json.loads(open(p,encoding='utf-8',errors='replace').read().replace('\ufffd','·'))
parts={'01':[(x,x) for x in ['empty','populated','s601b','s602b','s701']],
 '02':[(x,x) for x in ['part-dispatch','part-evidence','part-evidence-record','part-health','part-mini']],
 '03':[(x,x) for x in ['part-s404','part-s404-late','part-s405','part-s408-mixed','part-s408-owner']],
 '04':[(x,x) for x in ['s601b','s602b','s602b-guardrail']],
 '05':[('s602b-case-'+c,'part-s602b-cases/'+c) for c in ['guardrail','inconclusive','target_miss','withdrawn']]+[('s602b-replay','part-s602b-replay'),('s603','part-s603')],
 '06':[(x,x) for x in ['backup-failed','excursion','normal']],
 '07':[(x,x) for x in ['part-excursion','part-normal']]}
def key(p): return (p['screen'],p.get('case'),p['viewport'].split('x')[0])
def norm(a,b01):
    if b01:
        cl=[{'cls':None,'text':t} if isinstance(t,str) else t for t in a.get('clipped') or []]
        hs=[{'cls':(x.get('cls') if isinstance(x,dict) else None),'panel':(x.get('panel') if isinstance(x,dict) else str(x))} | (x if isinstance(x,dict) else {}) for x in a.get('innerScroll') or []]
        return cl,hs
    return a.get('clipped') or [], a.get('hscroll') or []
def sh(l): return {(x.get('cls'),x.get('panel') or x.get('text','')[:30]) for x in l}
def sc(l): return {(x.get('cls'),UU.sub('<u>',x.get('text','') or '')[:30]) for x in l}
out=[]
for b,pl in parts.items():
    for np_,op in pl:
        n=load(f'{NEW}/batch-{b}/{np_}/evidence.json'); 
        try: o={key(p):p for p in load(f'{OLD}/batch-{b}/{op}/evidence.json')['pairs']}
        except Exception as e: o={}; print('NO OLD',b,op,e)
        for p in n['pairs']:
            k=key(p); q=o.get(k)
            ncl,nhs=norm(p['app'],b=='01'); ocl,ohs=norm(q['app'],b=='01') if q else ([],[])
            newh=[x for x in nhs if (x.get('cls'),x.get('panel') or x.get('text','')[:30]) in sh(nhs)-sh(ohs)]
            newc=[x for x in ncl if (x.get('cls'),UU.sub('<u>',x.get('text','') or '')[:30]) in sc(ncl)-sc(ocl)]
            out.append(dict(batch=b,part=np_,screen=k[0],case=k[1],width=k[2],img=p['app_image'],overflowX=p['app']['overflowX'],
              frozen=bool(q),clipped=ncl,hscroll=nhs,new_clipped=newc,new_hscroll=newh,pageH=p['app'].get('pageH') or p['app'].get('pageHeight')))
json.dump(out,open(sys.argv[1],'w',encoding='utf-8'),indent=1,ensure_ascii=False)
print(len(out),'pairs')
for r in out:
    if r['new_clipped'] or r['new_hscroll'] or r['overflowX']>0 or not r['frozen']:
        print(r['batch'],r['part'],r['screen'],r['case'],r['width'],'ovX',r['overflowX'],'frozen',r['frozen'],'NEWCLIP',[(x.get('cls'),(x.get('text') or '')[:50],x.get('sw'),x.get('cw'),x.get('sh'),x.get('ch')) for x in r['new_clipped']],'NEWH',[(x.get('cls'),x.get('panel'),x.get('sw'),x.get('cw')) for x in r['new_hscroll']])
