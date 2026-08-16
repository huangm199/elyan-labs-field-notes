# ClawRTC without commitment: a Linux ARM64 dry-run preflight

When a tool says it will inspect hardware, create a local environment, contact a network, and potentially earn a token, the first useful question is not “how much can it earn?” It is “what exactly will it do to this machine?” ClawRTC has a useful answer built into its CLI: `clawrtc install --dry-run`.

This note documents a reproducible preflight of **ClawRTC 1.9.0** on Linux ARM64. I ran it on a Linux `aarch64` host on 2026-08-16. The goal was deliberately modest: install the Python package in an isolated virtual environment, ask the installer to explain itself, and verify that dry-run mode does not create the normal `~/.clawrtc` install directory inside a temporary home directory.

The upstream project is [Scottcjn/Rustchain](https://github.com/Scottcjn/Rustchain). ClawRTC is the packaged miner/client entry point for RustChain's Proof-of-Antiquity ecosystem. This article is about installation transparency, **not** a profitability test and not an endorsement of a token price.

## 1. Start in a disposable Python environment

On a Linux host with Python 3 available:

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install clawrtc==1.9.0
clawrtc --version
```

Pinning the version matters. A tutorial that silently follows “latest” can become wrong the next time a package changes its CLI. The run documented here used version `1.9.0`.

The CLI exposes a security-oriented preview command directly in its help text:

```bash
clawrtc install --dry-run --wallet field-notes-demo
```

The `field-notes-demo` string is only a harmless placeholder in this dry-run. The command did not create a miner wallet or begin mining.

## 2. What the dry run reported

The captured output is committed in [`../evidence/clawrtc-preflight-output.txt`](../evidence/clawrtc-preflight-output.txt). The important lines from my run were:

```text
[clawrtc] Platform: Linux | Arch: aarch64

What ClawRTC will do:

1. Extract   Two Python scripts bundled with this package:
   - fingerprint_checks.py  (hardware detection)
   - miner.py               (attestation client)

2. Install   A Python virtual environment in ~/.clawrtc/
   with one dependency: 'requests' (HTTP library)

3. Attest    When started, the miner contacts the RustChain network
   every few minutes to prove your hardware is real.

4. Collect   Hardware fingerprint data sent during attestation:
   - CPU model, architecture, vendor
   - Clock timing variance
   - Cache latency profile
   - VM detection flags

[clawrtc] DRY RUN — no files extracted, no services created.
```

That separation is useful. The preview tells us what **would** happen after installation without actually starting the attestation loop. It also gives a concrete data checklist to evaluate before deciding whether real mining belongs on a particular machine.

A second observation is platform support. The same package was also probed on Windows. `clawrtc install --dry-run` reported Windows/AMD64 and then stopped with “Unsupported platform: Windows. Use Linux or macOS.” That is better behavior than silently installing a partially supported service. For a Windows user, a Linux server or supported Linux/macOS host is the appropriate place to evaluate the miner rather than forcing the installation path.

## 3. Turn the preview into a regression check

Reading terminal output is useful, but we can make the “dry run did not install” claim testable. The companion script [`../examples/clawrtc_preflight_check.py`](../examples/clawrtc_preflight_check.py) creates a temporary home directory, runs the preview there, and checks three things:

1. the command exits successfully;
2. the output explicitly contains `DRY RUN`;
3. `.clawrtc` was not created inside that temporary home.

Run it from the same virtual environment:

```bash
python examples/clawrtc_preflight_check.py
```

The core is intentionally small:

```python
with tempfile.TemporaryDirectory(prefix="clawrtc-home-") as temp_home:
    env = os.environ.copy()
    env["HOME"] = temp_home

    proc = subprocess.run(
        ["clawrtc", "install", "--dry-run", "--wallet", "field-notes-demo"],
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )

    install_dir = Path(temp_home) / ".clawrtc"
    assert proc.returncode == 0
    assert "DRY RUN" in proc.stdout
    assert not install_dir.exists()
```

On the tested Linux ARM64 host the result was:

```text
PASS: clawrtc dry-run returned 0
PASS: output explicitly reported DRY RUN
PASS: temporary ~/.clawrtc was not created
platform_line: [clawrtc] Platform: Linux | Arch: aarch64
```

This does not mathematically prove that every possible filesystem location is untouched. It verifies the behavior that matters for the documented installer path, in a fresh temporary home, and makes the evidence repeatable.

## 4. What I would inspect before a real install

A dry run should be the beginning of review, not the end. The preview itself points to the bundled `miner.py` and `fingerprint_checks.py`. Because ClawRTC is distributed as Python code, a cautious operator can inspect the installed package before starting a service:

```bash
python -c "import clawrtc, pathlib; print(pathlib.Path(clawrtc.__file__).parent)"
pip show clawrtc
```

Then compare the implementation with the upstream [RustChain repository](https://github.com/Scottcjn/Rustchain). I would specifically verify the node URL, the exact fingerprint fields, service creation behavior, retry intervals, and how wallet keys are stored before allowing a long-running process.

ClawRTC also advertises `clawrtc install --verify` for bundled-file hashes. A reasonable deployment checklist is therefore:

```bash
clawrtc install --dry-run --wallet YOUR_WALLET
clawrtc install --verify
# inspect source/package files
# only then decide whether to install/start
```

Do not paste private wallet keys into shell history, GitHub issues, screenshots, or logs. A bounty claim needs a **public RTC address**, not a private key.

## 5. Why this kind of preflight matters for agent software

Agent tooling increasingly performs actions instead of only producing text. That changes the standard for “hello world.” A responsible first run should reveal side effects: files, services, outbound endpoints, credentials, and data collection. ClawRTC's dry-run mode is valuable because it makes those side effects inspectable before activation.

The test above also illustrates a pattern that applies beyond RustChain. When evaluating an agent-facing package, create a disposable environment, pin the version, redirect state to a temporary directory when possible, run the least-privileged preview, capture output, and turn important claims into assertions. That gives maintainers and users evidence that is stronger than a screenshot of a successful command.

For this specific run, the evidence supports a limited conclusion: **ClawRTC 1.9.0's Linux ARM64 installer preview identified its intended actions and, in the tested temporary-home scenario, did not create the normal installation directory.** It does not prove anything about future versions, mining returns, or the behavior after `clawrtc start`.

That narrow conclusion is intentional. Reproducible field notes are more useful when they distinguish what was actually tested from what remains a hypothesis.

---

**Reproduction date:** 2026-08-16  
**Package:** `clawrtc==1.9.0`  
**Upstream:** https://github.com/Scottcjn/Rustchain  
**Authorship/testing disclosure:** drafted with OpenAI GPT-5.6 Sol assistance under operator authorization; commands were executed and outputs checked before publication.
