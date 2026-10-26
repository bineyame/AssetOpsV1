"""compare3.py old.json new.json : compare2 + inner-overflow check (batch 08 lesson).
Flags (REGRESSION candidates): hscroll entries (cls,panel) present in new but not in old; clipped entries new vs old;
any hscroll/clipped on a 390 pair listed in 'inner' for visual review."""
import json, sys
sys.path.insert(0, __import__('os').path.dirname(__file__))
import compare2 as c2

def sig(l):
    return {(x.get('cls'), x.get('panel') or x.get('text','')[:30]) for x in (l or [])}

def main(oldp, newp):
    res = c2.main(oldp, newp)
    old = {c2.key(p): p for p in c2.load(oldp)['pairs']}
    new = {c2.key(p): p for p in c2.load(newp)['pairs']}
    for r in res:
        k = (r['screen'], r['case'], r['width'])
        n = new[k]['app']
        q = old.get(k)
        o = q['app'] if q else {}
        nh = sig(n.get('hscroll')) - sig(o.get('hscroll'))
        nc = sig(n.get('clipped')) - sig(o.get('clipped'))
        r['inner_new_hscroll'] = [x for x in (n.get('hscroll') or []) if (x.get('cls'), x.get('panel')) in nh]
        r['inner_new_clipped'] = [x for x in (n.get('clipped') or []) if (x.get('cls'), x.get('text','')[:30]) in nc]
        r['inner_all_hscroll'] = n.get('hscroll')
        r['inner_all_clipped'] = n.get('clipped')
        if 'regress' in r:
            if r['inner_new_hscroll']:
                r['regress'].append('NEW inner horizontal scroller: ' + str(r['inner_new_hscroll'])[:160])
            if r['inner_new_clipped'] and not any(x.startswith('clipped text changed') for x in r['regress']):
                r['regress'].append('NEW clipped: ' + str(r['inner_new_clipped'])[:160])
    return res

if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    print(json.dumps(main(sys.argv[1], sys.argv[2]), indent=1, ensure_ascii=False))
