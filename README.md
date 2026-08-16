# Elyan Labs Field Notes

Small, reproducible field notes about the Elyan Labs open-source stack. The emphasis is on commands that were actually executed, outputs that were checked, and boundaries that another developer can verify.

## Published tutorials

1. [ClawRTC without commitment: a Linux ARM64 dry-run preflight](articles/clawrtc-linux-arm64-preflight.md)
   - Runnable check: [`examples/clawrtc_preflight_check.py`](examples/clawrtc_preflight_check.py)
   - Captured run: [`evidence/clawrtc-preflight-output.txt`](evidence/clawrtc-preflight-output.txt)
2. [Beacon locally: build heartbeat and mayday payloads without sending network traffic](articles/beacon-local-heartbeat-mayday.md)
   - Runnable demo: [`examples/beacon_local_demo.py`](examples/beacon_local_demo.py)
   - Captured run: [`evidence/beacon-local-output.txt`](evidence/beacon-local-output.txt)

## Verification scope

The examples are intentionally narrow. They demonstrate package installation, local object creation, payload construction, and dry-run behavior. They do **not** claim mining profitability, production reliability, or network consensus behavior.

## Disclosure

Drafting and code review used OpenAI GPT-5.6 Sol under operator authorization. The commands and example programs linked above were executed and their outputs checked on 2026-08-16 before publication.
