# -*- coding: utf-8 -*-
import urllib.request, json, time
B = 'http://127.0.0.1:8000'
def get(p, raw=False):
    with urllib.request.urlopen(B+p, timeout=5) as r:
        d = r.read()
        return (r.status, d if raw else d.decode('utf-8'))
for attempt in range(10):
    try:
        get('/api/files'); break
    except Exception:
        time.sleep(0.4)
st, html = get('/')
print('GET /                ', st, 'editor.html bytes=', len(html), 'tem <title>=', '<title>' in html)
st, j = get('/api/files'); files = json.loads(j)['files']
print('GET /api/files       ', st, len(files), 'arquivos:', files[:3], '...')
st, j = get('/api/scans'); scans = json.loads(j)['scans']
print('GET /api/scans       ', st, len(scans), 'scans. 1o:', scans[0] if scans else None)
st, j = get('/api/file?name='+files[0]); d = json.loads(j)
print('GET /api/file        ', st, files[0], 'content bytes=', len(d['content']))
st, img = get('/scan/'+scans[0], raw=True)
print('GET /scan/<img>      ', st, 'jpg bytes=', len(img), 'JPEG=', img[:2]==b'\xff\xd8')
st, j = get('/api/map')
print('GET /api/map         ', st, j[:40])
print('\nOK — servidor respondendo.')
