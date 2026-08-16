#!/usr/bin/env python3
"""Build Beacon heartbeat and planned-mayday payloads locally."""
from __future__ import annotations

import json
from pathlib import Path
import tempfile

from beacon_skill import AgentIdentity, HeartbeatManager
from beacon_skill.mayday import MaydayManager


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="beacon-demo-") as temp_dir:
        root = Path(temp_dir)
        identity = AgentIdentity.generate()
        heartbeat_mgr = HeartbeatManager(data_dir=root / "heartbeat")
        mayday_mgr = MaydayManager(data_dir=root / "mayday")

        heartbeat = heartbeat_mgr.build_heartbeat(
            identity,
            status="alive",
            health={"cpu": "ok", "queue_depth": 0},
            config={},
        )
        mayday = mayday_mgr.build_mayday(
            identity,
            urgency="planned",
            reason="maintenance drill",
            relay_agents=["relay-demo"],
            config={},
        )

        assert heartbeat["kind"] == "heartbeat"
        assert heartbeat["status"] == "alive"
        assert heartbeat["agent_id"] == identity.agent_id
        assert mayday["kind"] == "mayday"
        assert mayday["urgency"] == "planned"
        assert mayday["agent_id"] == identity.agent_id

        print("agent_id", identity.agent_id)
        print("heartbeat", json.dumps(heartbeat, indent=2, sort_keys=True))
        print("mayday", json.dumps(mayday, indent=2, sort_keys=True))
        print("health", json.dumps(mayday_mgr.health_check(), indent=2, sort_keys=True))
        print("PASS: heartbeat and planned mayday payloads built locally")
        print("PASS: no transport send function was invoked by this demo")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
