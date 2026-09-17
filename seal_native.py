"""Create a reproducible manifest for the native dataset and protocol."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).parent
targets=['geometry/compiled.json','native/ledger.json','native/provenance-map.json','preregistration/sri-native-protocol-v1.json','preregistration/sri-exposure-ledger-v1.json','preregistration/research-architecture-v1.json']
entries=[]
for name in targets:
    b=(ROOT/name).read_bytes();entries.append({'path':name,'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)})
payload={'schema':'sri-native-seal-v1','scope':'native Sri dataset; excludes SUN comparison results','entries':entries}
canonical=json.dumps(payload,sort_keys=True,separators=(',',':')).encode();payload['manifest_sha256']=hashlib.sha256(canonical).hexdigest()
target=ROOT/'preregistration/sri-native-seal-v1.json';temporary=target.with_suffix('.json.tmp')
temporary.write_text(json.dumps(payload,indent=2)+'\n',encoding='utf-8');temporary.replace(target)
print(payload['manifest_sha256'])
