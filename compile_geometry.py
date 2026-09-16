"""Compile pinned solver output into a deterministic planar cell complex."""
import hashlib, json, math
from pathlib import Path

ROOT=Path(__file__).parent; src=ROOT/'geometry/source.json'; raw=src.read_bytes(); data=json.loads(raw)
SOURCE={'repository':'TheHardikDewra/sri-yantra','commit':'1da047f4641a9ea95457080801f2438e634d668a','path':'public/data/sri-yantra.json','sha256':hashlib.sha256(raw).hexdigest(),'license':'MIT'}
RINGS={1:(4,'chaturdasara'),3:(5,'bahirdasara'),5:(6,'antardasara'),7:(7,'ashtakona'),9:(8,'trikona')}
CHiodo={
 'authority':'Alessandro Chiodo, On the construction of the Sri Yantra, C. R. Math. 359 (2021), 377-397',
 'doi':'10.5802/crmath.163',
 'scope':'minimal concurrency conditions defining a four-parameter family up to similarity',
 'condition_i':{'shared_circumcircle':['t03','t07']},
 'condition_ii':[['t08','t01'],['t06','t02'],['t09','t03'],['t01','t06'],['t05','t07'],['t04','t08'],['t02','t09']],
 'condition_iii':[['t01','t02','t07'],['t02','t03','t07'],['t01','t03','t08'],['t01','t04','t06'],['t01','t05','t09'],['t04','t06','t09'],['t02','t07','t09'],['t03','t07','t08'],['t03','t08','t09'],['t04','t04','t08'],['t05','t05','t06'],['t02','t06','t06']]
}
TOL=1e-9
def q(p): return (round(p[0]/TOL),round(p[1]/TOL))
def cross(a,b,p): return (b[0]-a[0])*(p[1]-a[1])-(b[1]-a[1])*(p[0]-a[0])
def on_segment(a,b,p):
    scale=max(1.0,math.dist(a,b))
    return abs(cross(a,b,p))<TOL*scale and min(a[0],b[0])-TOL<=p[0]<=max(a[0],b[0])+TOL and min(a[1],b[1])-TOL<=p[1]<=max(a[1],b[1])+TOL
def parameter(a,b,p):
    dx,dy=b[0]-a[0],b[1]-a[1]; den=dx*dx+dy*dy
    return ((p[0]-a[0])*dx+(p[1]-a[1])*dy)/den

out={'schema':'sri-cell-complex-v3','authority':CHiodo,'implementation':SOURCE,'profiles':{}}
for profile,original in data['variants'].items():
    tri={t['i']:t for t in original['triangles']}
    def baw(i):
        t=tri[i];return t['base_y'],t['apex_y'],t['half_width']
    b3,a3,w3=baw(3);b7,a7,w7=baw(7)
    c3=(w3*w3+b3*b3-a3*a3)/(2*(b3-a3));c7=(w7*w7+b7*b7-a7*a7)/(2*(b7-a7))
    checks=[abs(c3-c7),abs(abs(a3-c3)-abs(a7-c7))]
    for first,second in CHiodo['condition_ii']:
        i,j=int(first[1:]),int(second[1:]);checks.append(abs(tri[i]['apex_y']-tri[j]['base_y']))
    for down,base,up in CHiodo['condition_iii']:
        i,j,k=int(down[1:]),int(base[1:]),int(up[1:]);y=tri[j]['base_y']
        xi=tri[i]['half_width']*(y-tri[i]['apex_y'])/(tri[i]['base_y']-tri[i]['apex_y'])
        xk=tri[k]['half_width']*(y-tri[k]['apex_y'])/(tri[k]['base_y']-tri[k]['apex_y'])
        checks.append(abs(xi-xk))
    chiodo_float64={'checks':len(checks),'maximum_residual':max(checks),'tolerance':1e-12,'pass':max(checks)<1e-12}
    assert chiodo_float64['pass'],chiodo_float64
    raw_cells=[]
    for oi,c in enumerate(original['cells']):
        pts=[tuple(p) for p in c['points']]; cx=sum(p[0] for p in pts)/len(pts); cy=sum(p[1] for p in pts)/len(pts)
        raw_cells.append({'original_index':oi,'points':pts,'depth':c['depth'],'sides':c['sides'],'area':c['area'],'canonical':bool(c['in_yantra']),'centroid':[cx,cy]})
    unique={q(p):p for c in raw_cells for p in c['points']}
    ordered=sorted(unique.values(),key=lambda p:(-p[1],p[0]))
    vertices=[{'id':f'{profile}:VERTEX:{i:02d}','point':list(p),'parent_incidence':[],'native_types':[]} for i,p in enumerate(ordered,1)]
    vid={q(v['point']):v['id'] for v in vertices}
    for depth,(av,ring) in RINGS.items():
        group=[c for c in raw_cells if c['canonical'] and c['depth']==depth]
        group.sort(key=lambda c:((math.atan2(c['centroid'][0],c['centroid'][1])+2*math.pi)%(2*math.pi),c['centroid'][0]))
        for n,c in enumerate(group,1):c['id']=f'{profile}:A{av}:CELL:{n:02d}';c['ring']=ring
    other=[c for c in raw_cells if not c['canonical']]
    other.sort(key=lambda c:(c['depth'],(math.atan2(c['centroid'][0],c['centroid'][1])+2*math.pi)%(2*math.pi),c['centroid'][0]))
    for n,c in enumerate(other,1):c['id']=f'{profile}:AUX:CELL:{n:02d}';c['ring']='auxiliary'
    edge_cells={}; cell_edges={}
    for c in raw_cells:
        atoms=[]
        for a,b in zip(c['points'],c['points'][1:]+c['points'][:1]):
            cuts=sorted((tuple(v['point']) for v in vertices if on_segment(a,b,tuple(v['point']))),key=lambda p:parameter(a,b,p))
            for u,v in zip(cuts,cuts[1:]):
                if math.dist(u,v)>TOL:
                    key=tuple(sorted((vid[q(u)],vid[q(v)])));atoms.append(key);edge_cells.setdefault(key,set()).add(c['id'])
        cell_edges[c['id']]=sorted(set(atoms))
    edge_keys=sorted(edge_cells);edges=[];eid={}
    parent_sides=[]
    for t in original['triangles']:
        pts=[tuple(p) for p in t['points']]
        for role,a,b in [('base',pts[0],pts[1]),('leg_right',pts[1],pts[2]),('leg_left',pts[2],pts[0])]:parent_sides.append({'triangle':f't{t["i"]:02d}','direction':t['direction'],'role':role,'a':a,'b':b})
    for n,key in enumerate(edge_keys,1):
        a,b=(tuple(next(v['point'] for v in vertices if v['id']==i)) for i in key)
        provenance=[{k:s[k] for k in ('triangle','direction','role')} for s in parent_sides if on_segment(s['a'],s['b'],a) and on_segment(s['a'],s['b'],b)]
        id=f'{profile}:EDGE:{n:03d}';eid[key]=id;edges.append({'id':id,'vertices':list(key),'cells':sorted(edge_cells[key]),'generated_by':provenance})
    vertex_cells={v['id']:set() for v in vertices}
    for c in raw_cells:
        c['vertices']=sorted({vid[q(p)] for p in c['points']});c['edges']=[eid[e] for e in cell_edges[c['id']]]
        for v in c['vertices']:vertex_cells[v].add(c['id'])
    for v in vertices:
        p=tuple(v['point']);inc=[]
        for s in parent_sides:
            if on_segment(s['a'],s['b'],p):inc.append({k:s[k] for k in ('triangle','direction','role')})
        types=[]
        for t in original['triangles']:
            pts=[tuple(x) for x in t['points']];label=f't{t["i"]:02d}'
            if math.dist(p,pts[2])<TOL:types.append({'type':'apex','triangle':label})
            midpoint=((pts[0][0]+pts[1][0])/2,(pts[0][1]+pts[1][1])/2)
            if math.dist(p,midpoint)<TOL:types.append({'type':'base_point','triangle':label})
        roles={(i['direction'],i['role'].split('_')[0]) for i in inc}
        if ('down','leg') in roles and ('up','leg') in roles and any(r=='base' for _,r in roles):types.append({'type':'triple_concurrency'})
        elif len({i['triangle'] for i in inc})>1:types.append({'type':'intersection'})
        v['parent_incidence']=inc;v['native_types']=types
    edge_adj={c['id']:set() for c in raw_cells}
    for e in edges:
        if len(e['cells'])==2:
            a,b=e['cells'];edge_adj[a].add(b);edge_adj[b].add(a)
    for c in raw_cells:
        c['edge_adjacent']=sorted(edge_adj[c['id']]);c['vertex_touching']=sorted(set().union(*(vertex_cells[v] for v in c['vertices']))-{c['id']})
        c['points']=[list(p) for p in c['points']]
    V,E,F=len(vertices),len(edges),len(raw_cells)
    assert (V,E,F)==(69,142,74),(V,E,F)
    assert E-V+1==F
    canonical=[c for c in raw_cells if c['canonical']]
    assert len(canonical)==43 and {d:sum(c['depth']==d for c in canonical) for d in RINGS}=={1:14,3:10,5:10,7:8,9:1}
    parents=[]
    for t in original['triangles']:
        x=dict(t);x['id']=f'{profile}:PARENT:T{t["i"]:02d}';parents.append(x)
    label='Huet parameter realization of Chiodo conditions' if profile=='huet' else 'Rational experimental realization (upstream label: traditional)'
    out['profiles'][profile]={'label':label,'parameters':original['parameters'],'layout':original['layout'],'avaranas':original['avaranas'],'bindu':{'id':f'{profile}:A9:POINT:01','point':original['bindu']},'parents':parents,'vertices':vertices,'edges':edges,'cells':sorted(raw_cells,key=lambda c:c['id']),'canonical_face_ids':sorted(c['id'] for c in canonical),'verification':{**original['verification'],'chiodo_float64':chiodo_float64,'compiled_topology':{'vertices':V,'edges':E,'bounded_cells':F,'canonical_triangles':43,'euler_pass':True}}}
(ROOT/'geometry/compiled.json').write_text(json.dumps(out,separators=(',',':')))
print('Compiled '+', '.join(f'{k}: V={len(v["vertices"])} E={len(v["edges"])} F={len(v["cells"])} canonical={len(v["canonical_face_ids"])}' for k,v in out['profiles'].items()))
