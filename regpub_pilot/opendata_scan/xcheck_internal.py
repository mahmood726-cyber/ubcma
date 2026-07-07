"""Independent recomputation: fresh single-PMID live queries, no cache, different code path."""
import json, urllib.request, urllib.parse, time
PMIDS="17101640,17109671,17300593,17563345,17595249,17682120,17987126,18292985,18776118,18931095,18957505,19037628,19094067,19279300,19509014,19650754,19691426,19910942,20084363,20199136,20350322,20457158,20480132,20547525,21159786,21299393,21411512,21457567,21550951,21781152,22002336,22018074,22114787,22124605,22234149,22672586,22686415,22844471,23020253,23273975".split(",")
oa=epmc=found=0; missing=[]
for p in PMIDS:
    u="https://www.ebi.ac.uk/europepmc/webservices/rest/search?"+urllib.parse.urlencode(
        {"query":f"EXT_ID:{p} AND SRC:MED","resultType":"core","format":"json"})
    req=urllib.request.Request(u,headers={"User-Agent":"xcheck/0.1"})
    d=json.loads(urllib.request.urlopen(req,timeout=60).read())
    res=d.get("resultList",{}).get("result",[])
    if not res: missing.append(p); continue
    r=res[0]; found+=1
    if r.get("isOpenAccess")=="Y": oa+=1
    if r.get("inEPMC")=="Y": epmc+=1
    time.sleep(0.34)
print(f"n=40 found={found} OA={oa} ({round(100*oa/40,1)}%) inEPMC={epmc} ({round(100*epmc/40,1)}%) missing={missing}")
