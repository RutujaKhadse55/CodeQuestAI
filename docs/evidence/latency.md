# /analyze latency (generated 2026-10-11 15:54)

Warm Docker Desktop on the Backend laptop; each call = examples + fuzz(200) + shrink + trace in ONE container start; ReferenceBundle cached per content_hash. Target: p95 < 6 s.

| Samples | p50 | p95 | max | mean |
|---|---|---|---|---|
| 30 | 0.67 s | 0.85 s | 0.88 s | 0.68 s |

**p95 target met: yes**
