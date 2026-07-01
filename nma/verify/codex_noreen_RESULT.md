# codex_noreen independent NMA verification

Command run from repo root:

```text
python nma/verify/codex_noreen_nma.py
```

The verifier uses the DL `tau2` values from the committed netmeta scalar CSVs
and compares random-effects league `TE` and `seTE` matrices against the
committed netmeta reference CSVs.

| network | netmeta DL tau2 | max abs TE error | TE cell | max abs seTE error | seTE cell |
| --- | ---: | ---: | --- | ---: | --- |
| smoking | 0.598875258924702 | 4.99918995089388e-11 | A vs B | 4.55332993531954e-11 | C vs D |
| senn2013 | 0.108716923142419 | 4.78576622775506e-11 | acar vs rosi | 4.80433470784192e-11 | sulf vs acar |

Both networks are below the `1e-6` target.
