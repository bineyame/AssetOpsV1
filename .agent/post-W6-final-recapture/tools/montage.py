import sys
from PIL import Image
out=sys.argv[1]; ims=[Image.open(p).convert('RGB') for p in sys.argv[2:]]
h=max(i.height for i in ims); W=sum(i.width for i in ims)+10*(len(ims)-1)
c=Image.new('RGB',(W,h),'white'); x=0
for i in ims: c.paste(i,(x,0)); x+=i.width+10
c.save(out)
