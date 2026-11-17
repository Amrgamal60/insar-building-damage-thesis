---
name: gpu-allowed
description: User permits installing GPU dependencies and using the local CUDA GPU for heavy compute
metadata:
  node_type: memory
  type: user
  originSessionId: 0e738ef5-b527-4bcd-85f1-62fb477ec0b7
  modified: 2026-10-08T05:47:30.884Z
---

The user said (2026-10-08) that whenever GPU use would help, Claude may download the needed dependencies and use it; CUDA is installed. The machine has an NVIDIA GeForce RTX 2080 Super Max-Q (8 GB, driver 595.91.07).

**Why:** heavy steps in the NYC replication (999-draw variogram nulls, block bootstraps) can be slow on CPU.
**How to apply:** for heavy numeric work, GPU libraries (e.g. CuPy, cuML, PyTorch) may be installed into the project venv without asking. Results must stay identical in method to the frozen plan [[nyc-replication-frozen]]; the GPU is only a speed-up, never a change of model or null.
