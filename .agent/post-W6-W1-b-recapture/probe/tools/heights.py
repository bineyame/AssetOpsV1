import json,sys
for d in sys.argv[1:]:
    e=json.load(open(d+'/evidence.json'))
    for p in e['pairs']:
        a=p['app']; ps=a['panels']
        print(d.split('/')[-1], p.get('case'), p.get('widthLabel') or p.get('w') or [k for k in p if 'idth' in k], a['overflowX'], [(x.get('title') or x.get('t'), round(x.get('h') or x.get('height') or 0)) for x in ps])
