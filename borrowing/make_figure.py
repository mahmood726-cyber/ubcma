import pandas as pd, numpy as np, json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
main=pd.read_csv("pilot_table.csv"); scr=pd.read_csv("pilot_scramble_table.csv")
boot=json.load(open("pilot_bootstrap.json")); bscr=json.load(open("pilot_scramble_bootstrap.json"))
TG=["GLP1","DPP4","SGLT2"]; M=["nma","borrow","shrink_mean"]; col={"nma":"#555","borrow":"#1f77b4","shrink_mean":"#d62728"}
fig,ax=plt.subplots(1,3,figsize=(15,4.6))
for a,rg in zip(ax[:2],["sparse","rich"]):
    sub=main[main.regime==rg]; x=np.arange(len(TG)); w=0.26
    for i,m in enumerate(M):
        vals=[sub[(sub.target==t)&(sub.method==m)].mciw0.values for t in TG]
        vals=[v[0] if len(v) else np.nan for v in vals]
        a.bar(x+(i-1)*w,vals,w,label=m,color=col[m])
    a.set_xticks(x); a.set_xticklabels(TG); a.set_title(f"MCIW0 by class — {rg.upper()} regime\n(lower=better; matched coverage)")
    a.set_ylabel("MCIW0 (HbA1c %)"); a.legend(fontsize=8)
# panel 3: dMCIW0 borrow_vs_nma with CIs, main vs scramble
a=ax[2]; rows=[]
for b in boot:
    if b["contrast"]=="borrow_vs_nma": rows.append((f"{b['target']}/{b['regime']}",b["mciw0_diff"],b["ci_lo"],b["ci_hi"],"real"))
for b in bscr:
    if b["contrast"]=="borrow_vs_nma": rows.append((f"{b['target']}/{b['regime']}",b["mciw0_diff"],b["ci_lo"],b["ci_hi"],"scramble"))
rows.sort(key=lambda r:r[0])
y=np.arange(len(rows))
for i,(lab,d,lo,hi,kind) in enumerate(rows):
    c="#1f77b4" if kind=="real" else "#aaaaaa"; off=0.18*(1 if kind=="scramble" else -1)
    a.errorbar(d,i+off,xerr=[[d-lo],[hi-d]],fmt="o",color=c,capsize=3,ms=5)
a.axvline(0,color="k",lw=0.8)
a.set_yticks(y); a.set_yticklabels([r[0] for r in rows],fontsize=8)
a.set_title("dMCIW0 borrow-vs-NMA (blue=real, grey=scramble)\n<0=win, >0=harm; 95% paired-bootstrap CI")
a.set_xlabel("dMCIW0 (HbA1c %)")
plt.tight_layout(); plt.savefig("fig_borrowing_pilot.png",dpi=130)
print("wrote fig_borrowing_pilot.png")
