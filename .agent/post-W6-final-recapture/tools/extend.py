"""One-off: patch compare.py with regression / fix-signal logic."""
p = 'C:/Users/assef/Bineyame/AssetOpsV1-plan2/.agent/post-W6-final-recapture/tools/compare.py'
s = open(p).read()
anchor = "        r['app_image']=p['app_image']; r['mock_image']=p['mock_image']\n"
add = anchor + r'''        omh={x['title']:x['h'] for x in q['mock']['panels']}
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
'''
assert anchor in s
open(p, 'w').write(s.replace(anchor, add))
