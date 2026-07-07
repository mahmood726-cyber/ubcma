"""Periphery extraction layer for the reg-vs-pub pilot.

Two EXISTING tools, wired in as offline, deterministic periphery components over
the Phase-1 full-text output:

  * rct_fulltext -- rct-extractor-v2  : structured RCT effects from OA full text.
  * km_ipd       -- KMDigitizer (Guyot): KM curve -> pseudo-IPD + HR trust gate.

Neither touches the network. Both read Phase-1's cached parsed full text (and, for
KM, local digitized figure drops), and emit provenance- + confidence-tagged
datapoints. Reconstructed survival is flagged and gated on a re-derived-vs-reported
HR check; mismatches are surfaced as discrepancies, never silently pooled.
"""
