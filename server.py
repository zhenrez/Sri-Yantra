"""Local-only static workbench and SQLite overlay API; no external dependencies."""
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
import argparse, json, sqlite3, urllib.parse, uuid

ROOT = Path(__file__).parent
DB = ROOT / 'workbench.sqlite3'
def connection():
    db = sqlite3.connect(DB)
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA foreign_keys=ON')
    return db
def init():
    with connection() as db:
        db.executescript('''CREATE TABLE IF NOT EXISTS overlays(id TEXT PRIMARY KEY,name TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS entities(id TEXT PRIMARY KEY,name TEXT NOT NULL,tradition TEXT NOT NULL DEFAULT 'unspecified',UNIQUE(name,tradition));
        CREATE TABLE IF NOT EXISTS placements(id TEXT PRIMARY KEY,overlay_id TEXT NOT NULL REFERENCES overlays(id),entity_id TEXT NOT NULL REFERENCES entities(id),profile TEXT NOT NULL,feature_id TEXT NOT NULL,role TEXT NOT NULL,status TEXT NOT NULL,source TEXT NOT NULL DEFAULT '',reason TEXT NOT NULL DEFAULT '',confidence REAL,created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS relation_events(id TEXT PRIMARY KEY,overlay_id TEXT NOT NULL REFERENCES overlays(id),kind TEXT NOT NULL,profile TEXT NOT NULL,feature_id TEXT,reason TEXT NOT NULL DEFAULT '');
        CREATE TABLE IF NOT EXISTS event_participants(event_id TEXT NOT NULL REFERENCES relation_events(id) ON DELETE CASCADE,entity_id TEXT NOT NULL REFERENCES entities(id),role TEXT NOT NULL,PRIMARY KEY(event_id,entity_id,role));
        CREATE INDEX IF NOT EXISTS placements_by_feature ON placements(profile,feature_id);
        CREATE INDEX IF NOT EXISTS placements_by_overlay ON placements(overlay_id);''')
        columns={row['name'] for row in db.execute('PRAGMA table_info(relation_events)')}
        if 'profile' not in columns:db.execute("ALTER TABLE relation_events ADD COLUMN profile TEXT NOT NULL DEFAULT ''")
        for id,name in [('traditional','Traditional guide'),('trial-a','Trial A'),('trial-b','Trial B')]:db.execute('INSERT OR IGNORE INTO overlays VALUES (?,?)',(id,name))

class Handler(SimpleHTTPRequestHandler):
    def __init__(self,*args,**kwargs):super().__init__(*args,directory=str(ROOT),**kwargs)
    def send_json(self,code,value):
        body=json.dumps(value,ensure_ascii=False).encode('utf-8');self.send_response(code);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('X-Content-Type-Options','nosniff');self.send_header('Cache-Control','no-store');self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
    def payload(self):
        try:length=int(self.headers.get('Content-Length','0'))
        except ValueError:self.send_json(400,{'error':'Invalid Content-Length'});return None
        if length<1:self.send_json(400,{'error':'JSON body required'});return None
        if length>100000:self.send_json(413,{'error':'Payload too large'});return None
        try:value=json.loads(self.rfile.read(length))
        except Exception:self.send_json(400,{'error':'Invalid JSON'});return None
        if not isinstance(value,dict):self.send_json(400,{'error':'JSON object required'});return None
        return value
    def do_GET(self):
        path=urllib.parse.urlsplit(self.path).path
        if path=='/api/state':
            with connection() as db:
                self.send_json(200,{k:[dict(row) for row in db.execute('SELECT * FROM '+k+' ORDER BY '+('event_id,entity_id,role' if k=='event_participants' else 'id'))] for k in ('overlays','entities','placements','relation_events','event_participants')})
        elif path=='/api/native':
            def read(path): return json.loads((ROOT/path).read_text())
            self.send_json(200,{
                'ledger':read('native/ledger.json'),
                'provenance':read('native/provenance-map.json'),
                'protocol':read('preregistration/sri-native-protocol-v1.json'),
                'exposure':read('preregistration/sri-exposure-ledger-v1.json'),
                'architecture':read('preregistration/research-architecture-v1.json'),
                'seal':read('preregistration/sri-native-seal-v1.json')
            })
        elif path in ('/','/index.html','/geometry/compiled.json'):
            self.path=path;super().do_GET()
        else:self.send_json(404,{'error':'Not found'})
    def do_HEAD(self):
        path=urllib.parse.urlsplit(self.path).path
        if path in ('/','/index.html','/geometry/compiled.json'):
            self.path=path;super().do_HEAD()
        else:self.send_error(404)
    def do_POST(self):
        if self.path not in ('/api/placements','/api/events'):return self.send_json(404,{'error':'Unknown endpoint'})
        p=self.payload()
        if p is None:return
        geometry=json.loads((ROOT/'geometry/compiled.json').read_text())
        with connection() as db:
            if not db.execute('SELECT 1 FROM overlays WHERE id=?',(p.get('overlay'),)).fetchone():return self.send_json(400,{'error':'Unknown overlay'})
            if self.path=='/api/placements':
                profile=p.get('profile');feature=p.get('feature');name=str(p.get('entity','')).strip()
                if profile not in geometry['profiles'] or feature not in {x['id'] for x in geometry['profiles'][profile]['cells']} or not name:return self.send_json(400,{'error':'Invalid feature or entity'})
                status=p.get('status','exploratory');role=p.get('role','candidate');source=str(p.get('source','')).strip()[:1000]
                if status not in ('exploratory','source-backed','unknown') or role not in ('occupant','class','candidate','action','relationship'):return self.send_json(400,{'error':'Invalid role or status'})
                if status=='source-backed' and not source:return self.send_json(400,{'error':'Source-backed placements require a source or passage'})
                tradition=str(p.get('tradition','unspecified')).strip()[:100] or 'unspecified';row=db.execute('SELECT id FROM entities WHERE name=? AND tradition=?',(name,tradition)).fetchone()
                eid=row['id'] if row else str(uuid.uuid4())
                if not row:db.execute('INSERT INTO entities(id,name,tradition) VALUES (?,?,?)',(eid,name,tradition))
                pid=str(uuid.uuid4());db.execute('INSERT INTO placements(id,overlay_id,entity_id,profile,feature_id,role,status,source,reason,confidence) VALUES (?,?,?,?,?,?,?,?,?,?)',(pid,p['overlay'],eid,profile,feature,role,status,source,str(p.get('reason',''))[:3000],None));self.send_json(201,{'id':pid})
            else:
                inputs=[str(x).strip() for x in p.get('inputs',[])];result=str(p.get('result','')).strip();profile=p.get('profile');feature=p.get('feature')
                if len(inputs)!=2 or not all(inputs) or not result or profile not in geometry['profiles'] or feature not in {x['id'] for x in geometry['profiles'][profile]['cells']}:return self.send_json(400,{'error':'Provide two inputs, one result and a valid face'})
                event=str(uuid.uuid4());db.execute('INSERT INTO relation_events(id,overlay_id,kind,profile,feature_id,reason) VALUES (?,?,?,?,?,?)',(event,p['overlay'],'proposed_generation',profile,feature,str(p.get('reason',''))[:3000]))
                tradition=str(p.get('tradition','unspecified')).strip()[:100] or 'unspecified'
                for name,role in zip(inputs+[result],['input-a','input-b','result']):
                    row=db.execute('SELECT id FROM entities WHERE name=? AND tradition=?',(name,tradition)).fetchone();eid=row['id'] if row else str(uuid.uuid4())
                    if not row:db.execute('INSERT INTO entities(id,name,tradition) VALUES (?,?,?)',(eid,name,tradition))
                    db.execute('INSERT INTO event_participants VALUES (?,?,?)',(event,eid,role))
                self.send_json(201,{'id':event})
    def do_DELETE(self):
        parts=urllib.parse.urlparse(self.path).path.split('/')
        if len(parts)!=4 or parts[1:3]!=['api','placements']:return self.send_json(404,{'error':'Unknown endpoint'})
        with connection() as db:
            cur=db.execute('DELETE FROM placements WHERE id=?',(parts[3],))
            self.send_json(200 if cur.rowcount else 404,{'deleted':bool(cur.rowcount)})

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--port',type=int,default=8765);args=ap.parse_args()
    init();print(f'Śrī workbench: http://127.0.0.1:{args.port}',flush=True)
    ThreadingHTTPServer(('127.0.0.1',args.port),Handler).serve_forever()
