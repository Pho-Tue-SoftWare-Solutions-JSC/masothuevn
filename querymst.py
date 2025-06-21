import requests
import os

if os.path.exists("output.txt"):
    os.remove("output.txt")

f = open('input.txt', 'r')

o = open('output.txt', 'a')

l = "https://masothue.com/Ajax/Search"

for line in f:
    #print(line)
    payload={'q': int(line), 'type': 'auto', 'token' : '', 'force-search': 0}
    r = requests.post(l, data=payload, allow_redirects=True)
    str = r.text
    #print(str)
    x=''
    pos = str.find('\/')
    if (pos >= 0):
        while (str[pos+2].isdigit()):
            x+=str[pos+2]
            pos=pos+1
        #print(x)
        o.write(x)
        o.write('\n')
    else:
        o.write('\n')
f.close()
o.close()