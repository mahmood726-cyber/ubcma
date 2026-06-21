# codex_mahmood independent NMA verification

Command run from repo root:

```powershell
python nma/verify/codex_mahmood_nma.py
```

The verifier is standalone and reads only the committed CSV inputs/references in
`nma/reference/`. It uses the netmeta DL `tau2` values from each network's
`*_scalars.csv`, rebuilds study-level covariance blocks, solves the GLS NMA
normal equations with Moore-Penrose inverses, and compares random-effects league
tables to the netmeta reference CSVs.

| network | tau2 | max abs TE error | TE max cell | max abs seTE error | seTE max cell | verdict |
|---|---:|---:|---|---:|---|---|
| smoking | 0.598875258924702 | 4.99916774643e-11 | A,B | 4.55333548643e-11 | C,D | PASS |
| senn2013 | 0.108716923142419 | 4.78596051678e-11 | acar,rosi | 4.80432915673e-11 | acar,sulf | PASS |

Both networks are below the target tolerance of `1e-6`.
