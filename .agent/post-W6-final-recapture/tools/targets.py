import json,sys
# usage: targets.py <evidence.json>  -> prints "screen:case=url" per unique pair (shell-quoted lines)
d=json.load(open(sys.argv[1])); seen=[]
for p in d['pairs']:
    k=(p['screen'],p['case'],p['app_url'])
    if k not in seen: seen.append(k)
for s,c,u in seen: print(f"{s}:{c}={u}" if c else f"{s}={u}")
