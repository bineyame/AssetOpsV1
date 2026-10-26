"""Compare original vs final evidence.json pairs. usage: compare.py <old.json> <new.json> -> JSON list on stdout"""
import json,sys,re
UUID=re.compile(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}',re.I)
CODE=re.compile(r'\b[A-Z]{2,}(?:_[A-Z0-9]+)+\b')
norm=lambda s: UUID.sub('<uuid>',s) if isinstance(s,str) else s
def key(p): return (p['screen'],p.get('case'),p['viewport'].split('x')[0])
def pan(a):
    return [(x['title'],x['h'],x['rows'],tuple(x['columns']),tuple(norm(l) for l in x['links']),tuple(x['chips']),tuple(x['disclosures'])) for x in a['panels']]
def vocab(a):
    out=[]
    txts=a['titles']+[l for x in a['panels'] for l in x['links']+x['chips']]
    for t in txts:
        if UUID.search(t) or CODE.search(t): out.append(t[:80])
    return out
def diff(o,n):
    d=[]
    if o['titles']!=n['titles']: d.append(f"titles {o['titles']} -> {n['titles']}")
    po,pn=pan(o),pan(n)
    for i,(a,b) in enumerate(zip(po,pn)):
        if a[0]!=b[0]: continue
        t=a[0]
        if abs(a[1]-b[1])>max(8,0.1*a[1]): d.append(f"[{t}] height {a[1]}->{b[1]}")
        if a[2]!=b[2]: d.append(f"[{t}] rows {a[2]}->{b[2]}")
        if a[3]!=b[3]: d.append(f"[{t}] columns {list(a[3])}->{list(b[3])}")
        if a[4]!=b[4]: d.append(f"[{t}] links {list(a[4])[:8]}->{list(b[4])[:8]}")
        if a[5]!=b[5]: d.append(f"[{t}] chips {list(a[5])[:6]}->{list(b[5])[:6]}")
        if a[6]!=b[6]: d.append(f"[{t}] disclosures {list(a[6])}->{list(b[6])}")
    if o['overflowX']!=n['overflowX']: d.append(f"overflowX {o['overflowX']}->{n['overflowX']}")
    for k in ('proseSizes',):
        if o.get(k)!=n.get(k): d.append(f"{k} {o.get(k)}->{n.get(k)}")
    for k in ('h1','h2','prose','td','th'):
        a,b=o.get(k),n.get(k)
        if a and b:
            for f in ('size','family','weight','color'):
                if a.get(f)!=b.get(f): d.append(f"{k}.{f} {a.get(f)}->{b.get(f)}")
            if k=='h1' and a.get('text')!=b.get('text'): d.append(f"h1 text {a.get('text')!r}->{b.get('text')!r}")
        elif bool(a)!=bool(b): d.append(f"{k} presence {bool(a)}->{bool(b)}")
    if abs((o.get('firstPanelY') or 0)-(n.get('firstPanelY') or 0))>8: d.append(f"firstPanelY {o.get('firstPanelY')}->{n.get('firstPanelY')}")
    if abs(o['pageHeight']-n['pageHeight'])>0.1*o['pageHeight']: d.append(f"pageHeight {o['pageHeight']}->{n['pageHeight']}")
    if o.get('clipped')!=n.get('clipped'): d.append(f"clipped {o.get('clipped')}->{n.get('clipped')}")
    if json.dumps(o.get('innerScroll'))!=json.dumps(n.get('innerScroll')): d.append(f"innerScroll {o.get('innerScroll')}->{n.get('innerScroll')}")
    if json.dumps(o.get('tabs'))!=json.dumps(n.get('tabs')): d.append(f"tabs {o.get('tabs')}->{n.get('tabs')}")
    so,sn=o.get('side'),n.get('side')
    if so and sn and (so['w'],so['bg'])!=(sn['w'],sn['bg']): d.append(f"rail {so}->{sn}")
    if o.get('pageEndNote')!=n.get('pageEndNote') and (o.get('pageEndNote') or {}).get('text')!=(n.get('pageEndNote') or {}).get('text'): d.append(f"pageEndNote {(o.get('pageEndNote') or {}).get('text')!r}->{(n.get('pageEndNote') or {}).get('text')!r}")
    return d
def main(oldp,newp):
    old={key(p):p for p in json.load(open(oldp))['pairs']}
    res=[]
    for p in json.load(open(newp))['pairs']:
        k=key(p); q=old.get(k)
        r={'screen':p['screen'],'case':p.get('case'),'width':k[2],'new_app_titles':p['app']['titles'],'mock_titles':p['mock']['titles'],'vocab_new':vocab(p['app']),'overflowX':p['app']['overflowX']}
        if not q: r['gap']='no original pair'; res.append(r); continue
        r['app_diffs']=diff(q['app'],p['app']); r['mock_diffs']=diff(q['mock'],p['mock'])
        r['old_app_titles']=q['app']['titles']; r['vocab_old']=vocab(q['app'])
        # cap: panel height ratio app/mock
        ratios=[]
        mh={x['title']:x['h'] for x in p['mock']['panels']}
        for x in p['app']['panels']:
            m=mh.get(x['title'])
            if m: ratios.append((x['title'],round(x['h']/m,2)))
        r['ratios_over_1.3']=[t for t in ratios if t[1]>1.3]
        r['dark_h1y_old_new']=(q['app'].get('h1') or {}).get('y'),(p['app'].get('h1') or {}).get('y')
        r['app_image']=p['app_image']; r['mock_image']=p['mock_image']
        omh={x['title']:x['h'] for x in q['mock']['panels']}
        oldr={x['title']:round(x['h']/omh[x['title']],2) for x in q['app']['panels'] if omh.get(x['title'])}
        newr=dict(ratios)
        r['ratio_worse']=[(t,oldr[t],v) for t,v in newr.items() if v>1.3 and v>oldr.get(t,1.0)+0.1]
        sig=[]
        oa,na=q['app'],p['app']
        if (oa.get('h1') or {}).get('text')!=(na.get('h1') or {}).get('text'): sig.append('h1 text changed')
        if p['viewport'].startswith('390') and (oa.get('h1') or {}).get('y',0)-(na.get('h1') or {}).get('y',0)>=30: sig.append('390 header band shorter')
        if any(str(i.get('cls','')).startswith('site-tabs') for i in oa.get('innerScroll',[])) and not any(str(i.get('cls','')).startswith('site-tabs') for i in na.get('innerScroll',[])): sig.append('tab row no longer scrolls')
        if 'MOCK DEVIATION' in ((na.get('pageEndNote') or {}).get('text') or '') and 'MOCK DEVIATION' not in ((oa.get('pageEndNote') or {}).get('text') or ''): sig.append('MOCK DEVIATION label shown')
        if oa['panelP']['sizes'].get('14px',0)>na['panelP']['sizes'].get('14px',0): sig.append('14px prose reduced')
        if any(t.get('label')=='Breadcrumb' for t in na.get('tabs',[])) and not any(t.get('label')=='Breadcrumb' for t in oa.get('tabs',[])): sig.append('breadcrumb added')
        for t,v in oldr.items():
            if v>1.3 and newr.get(t,v)<v-0.1: sig.append(f'{t} ratio {v}->{newr.get(t)}')
        r['fix_signals']=sig
        r['regress']=[]
        if na['overflowX']>0 and oa['overflowX']<=0: r['regress'].append('new horizontal overflow')
        if set(r['vocab_new'])-set(r['vocab_old']): r['regress'].append('new raw vocabulary: '+str(sorted(set(r['vocab_new'])-set(r['vocab_old']))[:3]))
        if r['ratio_worse']: r['regress'].append('cap exceeded '+str(r['ratio_worse']))
        if set(na['titles'])!=set(oa['titles']): r['regress'].append('panel set changed (review)')
        if na.get('clipped') and na['clipped']!=oa.get('clipped'): r['regress'].append('clipped text changed: '+str(na['clipped'])[:100])
        if r['mock_diffs']: r['regress'].append('mock measure changed')
        res.append(r)
    return res
if __name__=='__main__': print(json.dumps(main(*sys.argv[1:3]),indent=1))
