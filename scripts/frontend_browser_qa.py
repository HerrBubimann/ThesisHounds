"""Local synthetic browser QA. Uses installed Chrome and CDP; never real documents."""

import argparse
import asyncio
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

import websockets

ROOT = Path(__file__).resolve().parents[1]


def seed_synthetic_review(document_id="synthetic-demo"):
    """Only our temporary mock backend; no fixture grants in the actual repository."""

    def api(method, path, payload=None):
        data = json.dumps(payload).encode() if payload is not None else None
        request = urllib.request.Request(
            "http://127.0.0.1:8000" + path,
            data=data,
            method=method,
            headers={"Content-Type": "application/json"},
        )
        return json.load(urllib.request.urlopen(request, timeout=20))

    record = api(
        "POST",
        "/api/v1/assessments",
        {
            "work_type": "PA1",
            "profile_confirmed": True,
            "profile_id": "pa1-example",
            "document_id": document_id,
        },
    )
    path = "/api/v1/assessments/" + record["id"]
    api(
        "POST",
        path + "/human-review",
        {
            "release": True,
            "criteria": [
                {
                    "criterion_id": c["id"],
                    "judgment": "MIXED",
                    "observations": "Synthetische Browserprüfung: beobachtete Textstelle.",
                    "rationale": "Synthetische menschliche Bewertung für die Oberflächenprüfung.",
                }
                for c in record["profile"]["criteria"]
            ],
        },
    )
    api("POST", path + "/ai-review")
    for _ in range(100):
        state = api("GET", path)
        if state["ai_state"] != "RUNNING":
            break
        time.sleep(0.1)
    if state["ai_state"] != "COMPLETED":
        raise RuntimeError("Synthetic mock review did not complete")
    api("POST", path + "/release", {"confirmed": True})


async def capture(port, output, stage, pdf_smoke=False):
    targets = await asyncio.to_thread(
        lambda: json.load(urllib.request.urlopen(f"http://127.0.0.1:{port}/json"))
    )
    page = next(p for p in targets if p["type"] == "page")
    async with websockets.connect(page["webSocketDebuggerUrl"], max_size=20_000_000) as ws:
        counter = 0
        origins = set()

        async def call(method, params=None):
            nonlocal counter
            counter += 1
            message_id = counter
            await ws.send(json.dumps({"id": message_id, "method": method, "params": params or {}}))
            while True:
                message = json.loads(await ws.recv())
                if message.get("method") == "Network.requestWillBeSent":
                    url = message["params"]["request"]["url"]
                    if url.startswith(("http:", "https:", "ws:", "wss:")):
                        from urllib.parse import urlsplit

                        parts = urlsplit(url)
                        origins.add(f"{parts.scheme}://{parts.netloc}")
                if message.get("id") == message_id:
                    if "error" in message:
                        raise RuntimeError(message["error"]["message"])
                    return message.get("result", {})

        await call("Network.enable")
        await call("Page.enable")
        await call("Page.navigate", {"url": "http://127.0.0.1:8501"})
        for _ in range(100):
            result = await call(
                "Runtime.evaluate", {"expression": "document.body.innerText", "returnByValue": True}
            )
            if (
                "ThesisHounds" in result.get("result", {}).get("value", "")
                and "Dashboard" in result["result"]["value"]
            ):
                break
            await asyncio.sleep(0.2)
        await asyncio.sleep(2)
        import base64

        async def shot(name, width, height):
            await call(
                "Emulation.setDeviceMetricsOverride",
                {"width": width, "height": height, "deviceScaleFactor": 1, "mobile": False},
            )
            await asyncio.sleep(0.7)
            result = await call(
                "Page.captureScreenshot", {"format": "png", "captureBeyondViewport": False}
            )
            (output / f"{stage}-{name}.png").write_bytes(base64.b64decode(result["data"]))
            return await call(
                "Runtime.evaluate",
                {
                    "expression": "JSON.stringify({width:innerWidth,"
                    "scroll:document.documentElement.scrollWidth,buttons:"
                    "[...document.querySelectorAll('button')]"
                    ".filter(b=>b.innerText.trim()).map(b=>b.innerText.trim()).slice(0,30)})",
                    "returnByValue": True,
                },
            )

        evidence = {"desktop": await shot("dashboard-desktop", 1440, 1000)}
        evidence["tablet"] = await shot("dashboard-tablet", 820, 1100)
        evidence["mobile"] = await shot("dashboard-mobile", 390, 844)
        if stage != "before":
            await call(
                "Emulation.setDeviceMetricsOverride",
                {"width": 1440, "height": 1000, "deviceScaleFactor": 1, "mobile": False},
            )
            for title, name in [
                ("Neue Begutachtung", "wizard"),
                ("DHBW-Richtlinien", "knowledge"),
                ("Security Center", "security"),
            ]:
                if title == "Security Center":
                    await call(
                        "Runtime.evaluate",
                        {
                            "expression": "[...document.querySelectorAll('summary')]"
                            ".find(b=>b.innerText.includes('Technik & Verwaltung'))?.click()"
                        },
                    )
                    await asyncio.sleep(0.3)
                await call(
                    "Runtime.evaluate",
                    {
                        "expression": "[...document.querySelectorAll('button')]"
                        f".find(b=>b.innerText.trim()==={json.dumps(title)})?.click()"
                    },
                )
                await asyncio.sleep(1.5)
                await shot(name, 1440, 1000)
            for title in ("Meine Begutachtungen", "Öffnen"):
                await call(
                    "Runtime.evaluate",
                    {
                        "expression": "[...document.querySelectorAll('button')]"
                        f".find(b=>b.innerText.trim()==={json.dumps(title)})?.click()"
                    },
                )
                await asyncio.sleep(1)
            await shot("review", 1440, 1000)
            await call(
                "Runtime.evaluate",
                {
                    "expression": "[...document.querySelectorAll('label')]"
                    ".find(b=>b.innerText.trim()==='Drei Spalten')?.click()"
                },
            )
            await asyncio.sleep(0.8)
            await call(
                "Runtime.evaluate",
                {
                    "expression": "[...document.querySelectorAll('h3')]"
                    ".find(b=>b.innerText.includes('Wissenschaftlicher Arbeitsbereich'))"
                    "?.scrollIntoView({block:'start'})"
                },
            )
            await shot("review-columns", 1440, 1000)
            if pdf_smoke:
                await call(
                    "Runtime.evaluate",
                    {
                        "expression": "(()=>{let e=[...document.querySelectorAll('p')]"
                        ".find(p=>p.innerText==='Original-PDF anzeigen'"
                        "&&p.getClientRects().length);"
                        "while(e&&!e.querySelector('input'))e=e.parentElement;"
                        "if(!e)throw Error('PDF toggle not found');"
                        "e.querySelector('input').click();return true})()"
                    },
                )
                await asyncio.sleep(3)
                evidence["pdf_canvas"] = await call(
                    "Runtime.evaluate",
                    {
                        "expression": "(()=>{function count(root){"
                        "let n=root.querySelectorAll('canvas').length;"
                        "for(const e of root.querySelectorAll('*'))"
                        "if(e.shadowRoot)n+=count(e.shadowRoot);"
                        "return n}return count(document)})()",
                        "returnByValue": True,
                    },
                )
                if evidence["pdf_canvas"].get("result", {}).get("value", 0) < 1:
                    raise RuntimeError("PDF viewer did not render a canvas")
                await call(
                    "Runtime.evaluate",
                    {
                        "expression": "[...document.querySelectorAll('p')]"
                        ".find(b=>b.innerText==='Original-PDF anzeigen')"
                        "?.scrollIntoView({block:'start'})"
                    },
                )
                await shot("original-pdf", 1440, 1000)
            await call(
                "Input.dispatchKeyEvent",
                {"type": "keyDown", "key": "Tab", "code": "Tab", "windowsVirtualKeyCode": 9},
            )
            await call(
                "Input.dispatchKeyEvent",
                {"type": "keyUp", "key": "Tab", "code": "Tab", "windowsVirtualKeyCode": 9},
            )
            evidence["keyboard_focus"] = await call(
                "Runtime.evaluate",
                {
                    "expression": "JSON.stringify({tag:document.activeElement.tagName,"
                    "label:document.activeElement.getAttribute('aria-label'),"
                    "outline:getComputedStyle(document.activeElement).outlineStyle})",
                    "returnByValue": True,
                },
            )
        evidence["network_origins"] = sorted(origins)
        (output / f"{stage}-browser-checks.json").write_text(
            json.dumps(evidence, indent=2), encoding="utf-8"
        )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", choices=["before", "after"], required=True)
    parser.add_argument(
        "--pdf-smoke",
        action="store_true",
        help="Use generated test-only PDF and temporary synthetic approvals",
    )
    args = parser.parse_args()
    for port in (8000, 8501, 9333):
        with socket.socket() as sock:
            if sock.connect_ex(("127.0.0.1", port)) == 0:
                raise SystemExit(f"Port {port} already occupied; no existing service touched.")
    temporary = Path(tempfile.mkdtemp(prefix="thesishounds-frontend-qa-"))
    output = ROOT / "reports" / "frontend"
    if args.pdf_smoke:
        output /= "pdf-smoke"
    output.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ)
    env.update(
        PYTHONPATH=str(ROOT / "backend") + os.pathsep + str(ROOT),
        BACKEND_URL="http://127.0.0.1:8000",
        STREAMLIT_BROWSER_GATHER_USAGE_STATS="false",
    )
    processes = []
    flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    chrome = Path("C:/Program Files/Google/Chrome/Application/chrome.exe")
    try:
        config_dir = ROOT / "config"
        pilot_settings = "pilot_document_dir=None,"
        pilot_id = "synthetic-demo"
        if args.pdf_smoke:
            sys.path.insert(0, str(ROOT))
            sys.path.insert(0, str(ROOT / "backend"))
            from tests.fixtures.pilot import pilot_setup

            config_dir, catalog, pilot_id = pilot_setup(temporary)
            pilot_settings = (
                "pilot_profile_id='pa1-example',pilot_document_dir=Path("
                + repr(str(catalog))
                + "),"
            )
        backend = (
            "from app.main import create_app; from app.config import Settings;"
            " import uvicorn; from pathlib import Path; "
            "uvicorn.run(create_app(Settings(_env_file=None, "
            "security_mode='DEVELOPMENT',inference_mode='mock',deployment_mode='local',ollama_base_url='http://127.0.0.1:11434',"
            " config_dir=Path("
            + repr(str(config_dir))
            + "),document_store_dir=Path("
            + repr(str(temporary / "documents"))
            + "),"
            + pilot_settings
            + "public_metadata_dir=None,"
            "local_embedding_manifest_dir=None,citation_style_dir=None,"
            "enable_public_research=False,enable_internal_research=False,"
            "enable_ai_scoring=False,enable_local_language_tool=False)),"
            "host='127.0.0.1',port=8000,access_log=False,log_level='critical')"
        )
        for command, cwd in [
            ([sys.executable, "-c", backend], ROOT),
            (
                [
                    sys.executable,
                    "-m",
                    "streamlit",
                    "run",
                    str(ROOT / "frontend/app.py"),
                    "--server.address=127.0.0.1",
                    "--server.port=8501",
                ],
                ROOT / "frontend",
            ),
        ]:
            processes.append(
                subprocess.Popen(
                    command,
                    cwd=cwd,
                    env=env,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=flags,
                )
            )
        for _ in range(100):
            try:
                urllib.request.urlopen("http://127.0.0.1:8501/_stcore/health", timeout=1).read()
                urllib.request.urlopen("http://127.0.0.1:8000/health", timeout=1).read()
                break
            except OSError:
                time.sleep(0.2)
        if args.stage == "after":
            seed_synthetic_review(pilot_id)
        processes.append(
            subprocess.Popen(
                [
                    str(chrome),
                    "--headless=new",
                    "--disable-gpu",
                    "--no-first-run",
                    "--disable-background-networking",
                    "--disable-component-update",
                    "--disable-sync",
                    "--remote-debugging-address=127.0.0.1",
                    "--remote-debugging-port=9333",
                    f"--user-data-dir={temporary / 'chrome'}",
                    "about:blank",
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=flags,
            )
        )
        for _ in range(100):
            try:
                urllib.request.urlopen("http://127.0.0.1:9333/json", timeout=1).read()
                break
            except OSError:
                time.sleep(0.1)
        asyncio.run(capture(9333, output, args.stage, args.pdf_smoke))
        print(f"Synthetic browser evidence: {output}")
    finally:
        for process in reversed(processes):
            if os.name == "nt":
                subprocess.run(
                    ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=False,
                    creationflags=flags,
                )
            else:
                process.terminate()
            process.wait(timeout=15)
        if temporary.resolve().parent == Path(
            tempfile.gettempdir()
        ).resolve() and temporary.name.startswith("thesishounds-frontend-qa-"):
            shutil.rmtree(temporary, ignore_errors=True)


if __name__ == "__main__":
    main()
