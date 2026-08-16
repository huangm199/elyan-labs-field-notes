# Beacon locally: build heartbeat and mayday payloads without sending network traffic

Agent coordination protocols are easier to understand when the smallest useful pieces can be run locally. Beacon has a broad surface—identity, transports, Atlas, accords, relays, marketplaces and more—but two primitives are especially concrete: a **heartbeat** that says an agent is alive and a **mayday** payload that says an agent expects to go dark or needs continuity help.

This tutorial uses **`beacon-skill==2.16.1`** and constructs those payloads entirely in-process. It does not publish to Atlas, call BoTTube, send UDP, or contact a RustChain node. That makes it a useful first experiment before attaching a transport to a real agent.

The upstream project is [Scottcjn/beacon-skill](https://github.com/Scottcjn/beacon-skill).

## 1. Install the exact version used here

Create a disposable environment:

```bash
python -m venv .venv
# Linux/macOS
. .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
python -m pip install beacon-skill==2.16.1
```

Pinning a version makes the example auditable. If Beacon changes a constructor or payload field in a later release, a reader can still reproduce the behavior described here with the same package version.

The installed package exposes `AgentIdentity`, `HeartbeatManager`, `AccordManager`, Atlas helpers and other managers. For this exercise we only need an ephemeral identity, a heartbeat manager, and a mayday manager.

## 2. Generate an ephemeral agent identity

Beacon's `AgentIdentity.generate()` creates an Ed25519 identity in memory:

```python
from beacon_skill import AgentIdentity

identity = AgentIdentity.generate()
print(identity.agent_id)
```

On one validated test run, the ID looked like this:

```text
bcn_301a8c82f270
```

Your value will differ because a new keypair is generated each time. That is expected. In this demo we do not call identity persistence methods, so the key is discarded when the process exits.

That distinction matters. An ephemeral identity is ideal for a local tutorial because there is no long-lived secret to protect. A production agent that wants stable trust or reputation needs a deliberately persisted identity, restrictive filesystem permissions, backups, and a clear key-rotation policy.

## 3. Build a heartbeat locally

The heartbeat manager accepts an identity, a liveness status, and optional application-specific health metadata:

```python
from beacon_skill import HeartbeatManager

heartbeat_mgr = HeartbeatManager()
heartbeat = heartbeat_mgr.build_heartbeat(
    identity,
    status="alive",
    health={"cpu": "ok", "queue_depth": 0},
    config={},
)
print(heartbeat)
```

In the validated run, the resulting shape was:

```json
{
  "agent_id": "bcn_301a8c82f270",
  "beat_count": 1,
  "health": {
    "cpu": "ok",
    "queue_depth": 0
  },
  "kind": "heartbeat",
  "name": "",
  "status": "alive",
  "ts": 1786846128,
  "uptime_s": 0
}
```

The fields are easy to reason about: identity, message kind, liveness status, timestamp, beat counter, uptime, and health data supplied by the caller. Most importantly, **building the payload does not itself choose or invoke a network transport**. That separation lets application logic be tested before an agent announces its presence anywhere.

A production deployment should define what the custom health fields actually mean. For example, `queue_depth: 0` might be a useful signal for a task worker, while a database agent might care about replication lag or writable storage. A heartbeat only becomes operationally useful when consumers agree on the semantics.

## 4. Build a planned mayday payload

A mayday is a different signal. For a safe local drill, use `urgency="planned"` and a non-alarming reason:

```python
from beacon_skill.mayday import MaydayManager

mayday_mgr = MaydayManager()
mayday = mayday_mgr.build_mayday(
    identity,
    urgency="planned",
    reason="maintenance drill",
    relay_agents=["relay-demo"],
    config={},
)
print(mayday)
```

The same test run produced a payload with this structure:

```json
{
  "agent_id": "bcn_301a8c82f270",
  "content_hash": "f16ac72e1c23799735a3bc97d5bee69c",
  "kind": "mayday",
  "name": "",
  "pubkey": "be59a5de01d1990205f5181dbff97440432d87173e5ca9804dc6a3da717cdcf6",
  "reason": "maintenance drill",
  "relay_agents": [
    "relay-demo"
  ],
  "ts": 1786846128,
  "urgency": "planned"
}
```

Again, your identity, public key, content hash, and timestamp will differ. The conceptual difference from a heartbeat is that mayday carries **continuity intent**: urgency, a reason, and possible relay agents.

One subtle point is worth making explicit. `build_mayday()` builds the mayday payload. A production transport or envelope can add signing, routing, replay protection, and delivery semantics around that payload. Do not look at this local dictionary and assume it is already a complete authenticated network message for every transport.

## 5. Run both pieces in a temporary data directory

The complete companion program is [`../examples/beacon_local_demo.py`](../examples/beacon_local_demo.py). It uses a temporary directory so the demonstration does not leave Beacon state behind:

```python
with tempfile.TemporaryDirectory(prefix="beacon-demo-") as temp_dir:
    root = Path(temp_dir)
    identity = AgentIdentity.generate()
    heartbeat_mgr = HeartbeatManager(data_dir=root / "heartbeat")
    mayday_mgr = MaydayManager(data_dir=root / "mayday")
```

It then builds the two payloads and verifies their basic invariants:

```python
assert heartbeat["kind"] == "heartbeat"
assert heartbeat["status"] == "alive"
assert heartbeat["agent_id"] == identity.agent_id

assert mayday["kind"] == "mayday"
assert mayday["urgency"] == "planned"
assert mayday["agent_id"] == identity.agent_id
```

Run it with:

```bash
python examples/beacon_local_demo.py
```

A captured run is in [`../evidence/beacon-local-output.txt`](../evidence/beacon-local-output.txt). The program finishes with:

```text
PASS: heartbeat and planned mayday payloads built locally
PASS: no transport send function was invoked by this demo
```

The second line is a statement about the demo's code path: it only calls local constructors and builders. It is **not** a claim that every Beacon API is offline-only.

## 6. An edge case: local health probes are platform dependent

I also called `MaydayManager.health_check()` during the Windows test. It returned a healthy score while some low-level indicators were unavailable:

```json
{
  "healthy": true,
  "indicators": {
    "disk_free_mb": -1,
    "load_avg": -1,
    "mem_free_mb": -1
  },
  "score": 1.0
}
```

That is a useful operational lesson. An aggregate health score should not be treated as magical truth. If a deployment depends on disk, memory, or load thresholds, verify that the platform-specific probes actually populate those metrics. A production readiness check should inspect raw indicators as well as the aggregate boolean or score.

It is also a reason to keep application-level health fields explicit. If the operating-system probe cannot supply a metric on a platform, the agent can still expose the application signals that matter to its own workload.

## 7. What changes when this becomes a real distributed system

Once the local data shapes are understood, a real deployment can make explicit decisions that a hello-world example should not hide:

- **Identity persistence:** where is the Ed25519 private key stored, and which process account can read it?
- **Transport:** which Beacon transport fits the threat model and connectivity requirements?
- **Replay and staleness:** how old can a heartbeat be before a receiver ignores it?
- **Health semantics:** which fields are authoritative for this specific agent?
- **Mayday policy:** what conditions allow an automatic mayday, and when should a human approve one?
- **Relay trust:** which agents are allowed to receive or act on continuity information?
- **Failure behavior:** what happens when the selected transport is unavailable or a message cannot be verified?

These questions are easier to answer after the local structures are visible. We can write deterministic tests for application logic without accidentally publishing presence or continuity information to another service.

## 8. Why the offline-first test is useful

Agent software is often demonstrated by immediately connecting several services, which makes it hard to see which component caused a failure. The local approach gives a cleaner debugging boundary: first prove identity creation and payload generation, then introduce persistence, then signing/envelopes, then one transport, and only after that add multi-agent behavior.

The conclusion from this run is deliberately narrow: **Beacon 2.16.1 can generate an ephemeral Ed25519 agent identity and build heartbeat and planned-mayday payloads locally with a small Python program.** The tested program did not invoke a network transport. That gives developers a reproducible starting point without pretending a local dictionary is already a production-grade coordination system.

---

**Reproduction date:** 2026-08-16  
**Package:** `beacon-skill==2.16.1`  
**Upstream:** https://github.com/Scottcjn/beacon-skill  
**Authorship/testing disclosure:** drafted with OpenAI GPT-5.6 Sol assistance under operator authorization; the companion program was executed and its output checked before publication.
