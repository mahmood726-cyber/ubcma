# Appendix A — MinerU Install/Verify + GPU Preflight (commands only, nothing installed)

> **Do not run these as part of writing this spec.** They are the exact steps for a later
> session to stand up MinerU on a cluster node. Commands are given for **Windows/PowerShell**
> (the cluster's primary shell) with Linux equivalents noted. Verify against the live MinerU
> README at install time — pin versions then.

## GPU preflight (run FIRST, on each candidate node) {#gpu-preflight}

This gates whether a node can (a) run MinerU's VLM path and (b) later host Baidu Unlimited OCR.
MinerU's **pipeline** path needs no GPU, so a node failing this is still usable for CPU extraction.

```powershell
# NVIDIA GPU + VRAM present?
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv
# Decision:
#   no NVIDIA GPU            -> CPU pipeline only (fine for MinerU default; NO Baidu weights)
#   >=2-8 GB VRAM            -> MinerU VLM path OK
#   >=12-16 GB VRAM          -> also a candidate host for Baidu Unlimited OCR (3B/500M-active)
```

**Known state (2026-07-06):** the node this spec was written on reports **no NVIDIA GPU**, and no
cluster-hardware inventory exists on disk. Run the preflight on all three cluster PCs and record
the results before pulling any model weights. **Do not download Baidu weights until a node shows
≥~12 GB VRAM here** (per the no-wasteful-pull rule).

## MinerU install (CPU pipeline — the free default, no GPU needed)

Isolate in a venv; MinerU supports **Python 3.10–3.12 on Windows** (3.10–3.13 Linux).

```powershell
# from the node, in the project area
python --version                      # confirm 3.10-3.12
python -m venv F:\ubcma\.venv-mineru
F:\ubcma\.venv-mineru\Scripts\Activate.ps1
python -m pip install -U pip
pip install -U "mineru[all]"          # pulls MinerU + models on first run
```

Linux equivalent: `python3 -m venv .venv-mineru && source .venv-mineru/bin/activate && pip install -U "mineru[all]"`.
Docker (Linux / Windows WSL2) is also supported per the README if a container is preferred.

## Verify (smoke test — must finish well under the 300 s verify bound)

```powershell
# 1. CLI resolves
mineru --help

# 2. Extract one known PDF to markdown+JSON via the CPU pipeline backend
#    (-b pipeline forces the non-VLM, GPU-free path)
mineru -p F:\ubcma\specs\doc-extraction\_smoke\sample.pdf -o F:\ubcma\specs\doc-extraction\_smoke\out -b pipeline

# 3. Confirm structured outputs exist and carry page-level structure
Get-ChildItem F:\ubcma\specs\doc-extraction\_smoke\out -Recurse -Include *.md,*.json
```

**Pass criteria for the smoke test:**
- `*.md` and a `*_content_list.json` (or equivalent) are produced;
- the JSON preserves **reading order and page indices** (needed for the source-page provenance
  gate in [`02`](02-recommended-architecture.md));
- at least one table from `sample.pdf` renders as structured HTML/JSON, not flattened prose.

Use a **real ground-truthed trial PDF** as `sample.pdf` (one already in the audit set) so the
smoke test doubles as the first data point for the digit-exact bake-off.

## Optional: MinerU VLM path (only on a GPU node)

The `pipeline` backend above is the recommended default. If a node passed the GPU preflight and
you want to A/B the 1.2B `MinerU2.5-Pro` VLM path in the bake-off, invoke MinerU's VLM backend
per the current README (backend flag/name has changed across MinerU versions — **read the live
README at install time; do not assume the flag from this spec**). Both paths must clear the same
digit-exact bar before either is trusted for unattended numeric extraction.

## Not covered here (deliberately)
- **Baidu Unlimited OCR install** — deferred until the GPU preflight confirms a host node; it runs
  via Transformers / SGLang (vLLM/ModelScope claimed but unverified). Spec its install in a
  follow-up once a GPU node exists.
- **Mistral OCR 4** — cloud API; no local install. Needs an API key + the $4/1k-pages budget
  line; self-host is enterprise-license-only.
