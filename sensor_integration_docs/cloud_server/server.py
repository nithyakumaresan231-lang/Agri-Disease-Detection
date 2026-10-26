#!/usr/bin/env python3
"""POLY HOUSE cloud server (runs on the laptop).

Receives HTTP uploads from the gateway device, stores every snapshot in
MySQL, and lets you control each relay ON/OFF individually from a web
panel served on this laptop.

Endpoints:
  GET  /                    -> relay control web panel
  GET  /api/commands        -> device polls for commands (from commands.json)
  GET  /api/status          -> latest payload + current commands
  POST /api/relay/control   -> {slave_id, address, state} control one relay
  POST /api/relay/clear     -> remove all pending commands
  POST /api/data            -> device uploads sensor data (stored in MySQL)
  POST /api/ack             -> device reports command results (logged)

Relay control works by writing a relay_control command into commands.json.
The device polls GET /api/commands every poll_interval seconds, executes
the command, and POSTs the result back to /api/ack.

Run:
  py server.py
"""

import os
import json
import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "mysql_config.json")
COMMANDS_FILE = os.path.join(BASE_DIR, "commands.json")

DEFAULT_CONFIG = {
    "host": "127.0.0.1",
    "port": 3306,
    "user": "root",
    "password": "YOUR_MYSQL_ROOT_PASSWORD",
    "database": "polyhouse",
    "http_port": 5000,
    "bind": "0.0.0.0",
}

# Physical relay map (matches the device output layout):
#   slave 1 = coil 0-7  -> FAN1, FAN2, FOGGER, HONEYCOMB, OUT5-8
#   slave 2 = coil 8-11 -> PUMP1, PUMP2, PUMP3, PUMP4
RELAYS = [
    {"slave": 1, "addr": 0, "name": "FAN1"},
    {"slave": 1, "addr": 1, "name": "FAN2"},
    {"slave": 1, "addr": 2, "name": "FOGGER"},
    {"slave": 1, "addr": 3, "name": "HONEYCOMB"},
    {"slave": 1, "addr": 4, "name": "OUT5"},
    {"slave": 1, "addr": 5, "name": "OUT6"},
    {"slave": 1, "addr": 6, "name": "OUT7"},
    {"slave": 1, "addr": 7, "name": "OUT8"},
    {"slave": 2, "addr": 0, "name": "PUMP1"},
    {"slave": 2, "addr": 1, "name": "PUMP2"},
    {"slave": 2, "addr": 2, "name": "PUMP3"},
    {"slave": 2, "addr": 3, "name": "PUMP4"},
]


def load_config():
    cfg = dict(DEFAULT_CONFIG)
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r") as f:
                cfg.update(json.load(f))
    except Exception as e:
        print(f"[SERVER] config load error: {e}")
    # Allow environment variable override for port
    env_port = os.getenv("HTTP_PORT") or os.getenv("PORT")
    if env_port:
        try:
            cfg["http_port"] = int(env_port)
        except ValueError:
            pass
    return cfg


def now():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def read_commands():
    try:
        with open(COMMANDS_FILE, "r") as f:
            data = json.load(f)
        return data.get("commands", []) or []
    except Exception:
        return []


def write_commands(commands):
    with open(COMMANDS_FILE, "w") as f:
        json.dump({"commands": commands}, f, indent=2)


def mysql_connect():
    import pymysql
    cfg = load_config()
    return pymysql.connect(
        host=cfg["host"],
        port=int(cfg["port"]),
        user=cfg["user"],
        password=cfg["password"],
        database=cfg["database"],
        charset="utf8mb4",
        connect_timeout=5,
    )


def latest_payload():
    """Return the newest device_data payload dict, or None."""
    try:
        conn = mysql_connect()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT payload FROM device_data ORDER BY id DESC LIMIT 1"
                )
                row = cur.fetchone()
            return json.loads(row[0]) if row and row[0] else None
        finally:
            conn.close()
    except Exception:
        return None


PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>POLY HOUSE - Relay Control</title>
<style>
  body{font-family:Segoe UI,Arial,sans-serif;margin:0;background:#0f1720;color:#e8f0e8;}
  h1{margin:0;padding:18px 24px;background:#14532d;color:#fff;font-size:20px;}
  .wrap{max-width:900px;margin:20px auto;padding:0 16px;}
  .group{background:#16202b;border:1px solid #22303d;border-radius:10px;padding:16px;margin-bottom:18px;}
  .group h2{margin:0 0 12px;font-size:15px;color:#86efac;}
  .relay{display:flex;align-items:center;justify-content:space-between;padding:10px 12px;border-bottom:1px solid #22303d;}
  .relay:last-child{border-bottom:none;}
  .rname{font-weight:600;}
  .raddr{color:#7a8b98;font-size:12px;margin-left:8px;}
  .state{font-size:12px;padding:3px 9px;border-radius:10px;margin-right:12px;}
  .st-on{background:#14532d;color:#86efac;}
  .st-off{background:#3f1d1d;color:#fca5a5;}
  .st-unknown{background:#31373d;color:#9aa5ad;}
  .mode{font-size:11px;font-weight:700;padding:3px 9px;border-radius:10px;margin-right:10px;}
  .mode-auto{background:#1e3a5f;color:#93c5fd;}
  .mode-manual{background:#5b4a1a;color:#fde68a;}
  button{cursor:pointer;border:none;border-radius:6px;padding:7px 18px;font-weight:700;font-size:13px;}
  .btn-on{background:#16a34a;color:#fff;}
  .btn-on:hover{background:#15803d;}
  .btn-off{background:#7f1d1d;color:#fff;}
  .btn-off:hover{background:#991b1b;}
  .msg{margin:10px 0;padding:10px 14px;border-radius:8px;font-size:13px;display:none;}
  .msg.ok{background:#14532d;color:#86efac;}
  .msg.err{background:#3f1d1d;color:#fca5a5;}
  .foot{color:#7a8b98;font-size:12px;padding:0 16px 24px;max-width:900px;margin:0 auto;}
  .clear{background:#31373d;color:#e8f0e8;margin-top:6px;}
</style>
</head>
<body>
<h1>&#127808; POLY HOUSE - Relay Control</h1>
<div class="wrap">
  <div id="msg" class="msg"></div>
  <div id="groups"></div>
</div>
<div class="foot">Relay command device ku anupum (10s poll). Current state latest upload ah edutha display.</div>
<script>
const RELAYS = %RELAYS%;

function el(name, text){ const e=document.createElement('div'); e.className=name; e.textContent=text; return e; }

function show(msg, ok){
  const m=document.getElementById('msg');
  m.className='msg '+(ok?'ok':'err');
  m.textContent=msg;
  m.style.display='block';
  setTimeout(()=>{m.style.display='none';}, 4000);
}

async function send(r, state){
  const payload = (r.slave_id != null)
    ? {slave_id:r.slave_id, address:r.address, state:state}
    : {name:r.name, state:state};
  try{
    const resp=await fetch('/api/relay/control',{
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify(payload)
    });
    const d=await resp.json();
    if(d.status==='ok') show((r.name||('relay slave '+r.slave_id+' addr '+r.address))+' -> '+(state?'ON':'OFF')+' sent to device','ok');
    else show('Error: '+(d.message||'unknown'),false);
  }catch(e){ show('Failed: '+e,false); }
}

function render(relayList){
  const wrap=document.getElementById('groups');
  wrap.innerHTML='';
  const list=relayList||[];
  if(list.length && list[0].slave_id!=null){
    // fallback: physical relay map still has slave/addr -> group by slave
    const groups={};
    list.forEach(r=>{ (groups[r.slave_id]=groups[r.slave_id]||[]).push(r); });
    Object.keys(groups).sort().forEach(slave=>{
      const g=el('group','');
      const h=document.createElement('h2');
      h.textContent='Slave '+slave+' (Modbus '+slave+')';
      g.appendChild(h);
      groups[slave].forEach(r=>addRow(g,r));
      wrap.appendChild(g);
    });
  } else {
    // device relay_status: name + state + mode only (no slave/addr)
    const g=el('group','');
    const h=document.createElement('h2');
    h.textContent='Configured Relays';
    g.appendChild(h);
    list.forEach(r=>addRow(g,r));
    wrap.appendChild(g);
  }
  const clr=document.createElement('button'); clr.className='clear'; clr.textContent='Clear all pending commands';
  clr.onclick=async()=>{ await fetch('/api/relay/clear',{method:'POST'}); show('Commands cleared','ok'); };
  wrap.appendChild(clr);
}

function addRow(g,r){
  const row=el('relay','');
  const left=el('rname',r.name);
  if(r.slave_id!=null) left.innerHTML='<span class="rname">'+r.name+'</span><span class="raddr">slave '+r.slave_id+' / coil '+r.address+'</span>';
  const right=el('rright','');
  right.style.display='flex';
  right.style.alignItems='center';
  const modeEl=el('mode '+(r.control_mode==='manual'?'mode-manual':'mode-auto'),
                  r.control_mode==='manual'?'MANUAL':'AUTO');
  const stEl=el('state '+(r.state===true?'st-on':r.state===false?'st-off':'st-unknown'),
                r.state===true?'ON':r.state===false?'OFF':'--');
  const on=document.createElement('button'); on.className='btn-on'; on.textContent='ON';
  on.onclick=()=>send(r,true);
  const off=document.createElement('button'); off.className='btn-off'; off.textContent='OFF';
  off.onclick=()=>send(r,false);
  right.appendChild(modeEl); right.appendChild(stEl); right.appendChild(on); right.appendChild(off);
  row.appendChild(left); row.appendChild(right);
  g.appendChild(row);
}

async function refresh(){
  try{
    const r=await fetch('/api/status');
    const d=await r.json();
    let list=null;
    if(d.latest && Array.isArray(d.latest.relay_status) && d.latest.relay_status.length){
      list=d.latest.relay_status;
    }
    if(!list){ // no upload yet: fall back to the physical relay map
      list=RELAYS.map(x=>({name:x.name, slave_id:x.slave, address:x.addr, state:null, control_mode:''}));
    }
    render(list);
  }catch(e){ render(null); }
}

refresh();
setInterval(refresh, 5000);
</script>
</body>
</html>"""


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        print(f"[{now()}] {self.command} {self.path} -> {fmt % args}")

    def _send_json(self, code, obj):
        body = json.dumps(obj, default=str).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self, html):
        body = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self):
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length else b""
        try:
            return json.loads(raw.decode("utf-8"))
        except Exception:
            return {}

    def do_GET(self):
        path = self.path.split("?")[0]
        if path == "/":
            self._send_html(PAGE.replace("%RELAYS%", json.dumps(RELAYS)))
        elif path.startswith("/api/commands"):
            self._send_json(200, {"commands": read_commands()})
        elif path.startswith("/api/status"):
            self._send_json(200, {"status": "ok", "latest": latest_payload(), "current_commands": read_commands()})
        else:
            self._send_json(404, {"status": "error", "message": "not found"})

    def do_POST(self):
        path = self.path.split("?")[0]
        body = self._read_json()
        if path.startswith("/api/relay/control"):
            self._relay_control(body)
        elif path.startswith("/api/commands"):
            self._write_commands_api(body)
        elif path.startswith("/api/relay/clear"):
            write_commands([])
            print("  [CMD] all commands cleared")
            self._send_json(200, {"status": "ok"})
        elif path.startswith("/api/data"):
            self._save_data(body)
        elif path.startswith("/api/ack"):
            self._save_ack(body)
        else:
            self._send_json(404, {"status": "error", "message": "not found"})

    def _write_commands_api(self, body):
        """POST /api/commands - write commands for the device to execute.

        Accepts either:
          {"commands": [ {...}, {...} ]}   -> write exactly these
          { ...single command dict... }     -> wrap it into a list
        The device picks the commands up on its next poll.
        """
        if "commands" in body and isinstance(body["commands"], list):
            commands = body["commands"]
        elif "command" in body:
            commands = [body]
        elif "cmd" in body:
            commands = [body]
        else:
            self._send_json(400, {"status": "error", "message": "send {\"commands\": [...]} or a single command object"})
            return
        write_commands(commands)
        print(f"  [CMD] {len(commands)} command(s) queued for device")
        self._send_json(200, {"status": "ok", "queued": len(commands), "commands": commands})

    def _relay_control(self, body):
        name = str(body.get("name") or body.get("relay_name") or "").strip()
        try:
            slave = int(body.get("slave_id") or body.get("slave") or 0)
            addr = int(body.get("address") or body.get("addr") or 0)
        except (TypeError, ValueError):
            slave, addr = 0, 0
        state = bool(body.get("state", True))
        req = "web-" + datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        if name:
            write_commands([{
                "command": "relay_control",
                "name": name,
                "state": state,
                "request_id": req,
            }])
            desc = f"relay '{name}' -> {'ON' if state else 'OFF'}"
        else:
            if not slave:
                self._send_json(400, {"status": "error", "message": "name or slave_id + address required"})
                return
            write_commands([{
                "command": "relay_control",
                "slave_id": slave,
                "address": addr,
                "state": state,
                "request_id": req,
            }])
            desc = f"relay slave {slave} addr {addr} -> {'ON' if state else 'OFF'}"
        print(f"  [CMD] {desc} queued")
        self._send_json(200, {"status": "ok", "message": desc})

    def _save_data(self, body):
        payload = json.dumps(body, default=str)
        try:
            conn = mysql_connect()
            try:
                with conn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO device_data (device_id, customer_id, ts, payload) VALUES (%s, %s, %s, %s)",
                        (str(body.get("device_id", "")), str(body.get("customer_id", "")),
                         str(body.get("timestamp", "")), payload),
                    )
                conn.commit()
            finally:
                conn.close()
            print(f"  [DATA] saved from {body.get('device_id', '?')}")
            self._send_json(200, {"status": "ok", "message": "data stored"})
        except Exception as e:
            print(f"  [DATA] MYSQL ERROR: {e}")
            self._send_json(500, {"status": "error", "message": str(e)})

    def _save_ack(self, body):
        payload = json.dumps(body, default=str)
        try:
            conn = mysql_connect()
            try:
                with conn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO commands_log (device_id, ts, payload) VALUES (%s, %s, %s)",
                        (str(body.get("device_id", "")), str(body.get("timestamp", "")), payload),
                    )
                conn.commit()
            finally:
                conn.close()
            self._clear_acked_commands(body)
            print(f"  [ACK] results from {body.get('device_id', '?')}")
            self._send_json(200, {"status": "ok"})
        except Exception as e:
            print(f"  [ACK] MYSQL ERROR: {e}")
            self._send_json(500, {"status": "error", "message": str(e)})

    def _clear_acked_commands(self, body):
        """Remove commands from commands.json once the device has acked them.

        The device polls /api/commands every few seconds; if a command is
        never removed it gets replayed forever, which re-applies the same
        relay state every poll and fights manual changes made on the device
        dashboard. Clearing on ack (rather than on delivery) keeps
        at-least-once delivery if the device is offline mid-command.
        """
        acked = set()
        results = body.get("results") or []
        for r in results:
            if isinstance(r, dict) and r.get("request_id"):
                acked.add(str(r["request_id"]))
        if body.get("request_id"):
            acked.add(str(body["request_id"]))
        pending = read_commands()
        if not pending:
            return
        if acked:
            pending = [c for c in pending if str(c.get("request_id") or "") not in acked]
        else:
            pending = []
        write_commands(pending)


def main():
    cfg = load_config()
    host, port = cfg["bind"], int(cfg["http_port"])
    print(f"[SERVER] POLY HOUSE cloud server")
    print(f"[SERVER] MySQL target : {cfg['user']}@{cfg['host']}:{cfg['port']}/{cfg['database']}")
    print(f"[SERVER] Control panel: http://127.0.0.1:{port}   (laptop: http://{host}:{port})")
    ThreadingHTTPServer((host, port), Handler).serve_forever()


if __name__ == "__main__":
    main()
