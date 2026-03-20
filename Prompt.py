/usr/bin/python3 - "$KMVAR_localConfigPath" "$KMVAR_localHtmlPath" <<'PY'
import json, sys, os, html, re

VERSION = "v9.6"
config_path = sys.argv[1]
html_path   = sys.argv[2]

# --- ERROR CATCHING & COMMENT-AWARE LOADER ---
try:
    with open(config_path, "r", encoding="utf-8") as f:
        raw_lines = f.readlines()

    clean_lines = []
    for line in raw_lines:
        line = line.replace('\xa0', ' ')
        stripped = line.lstrip()
        if stripped.startswith('//') or stripped.startswith(';'):
            continue
        clean_lines.append(line)

    cfg = json.loads("\n".join(clean_lines))

except Exception as e:
    err = f"""<!doctype html><html><head><meta charset="utf-8"><title>JSON Error</title>
    <style>body{{font-family:system-ui;background:#ffebeb;color:#333;padding:24px;}}
    pre{{background:#fff;padding:12px;border:1px solid #fcc;border-radius:6px;font-size:12px;white-space:pre-wrap;}}
    button{{margin-top:15px;padding:6px 16px;cursor:pointer;border-radius:6px;border:1px solid #ccc;background:#fff;}}</style></head>
    <body data-kmwindow="SCREENVISIBLE(Main,MidX)-250,SCREENVISIBLE(Main,MidY)-125,500,250">
    <h2 style="color:#c00;margin-top:0;font-size:16px;">⚠️ JSON Syntax Error</h2>
    <p style="font-size:13px;">There is a typo in your configuration file:</p><pre>{html.escape(str(e))}</pre>
    <button id="cb" onclick="window.KeyboardMaestro.Cancel('Cancel')">Close</button>
    <script>document.getElementById('cb').focus();document.addEventListener('keydown',e=>{{if(e.key==='Escape'||e.key==='Enter')window.KeyboardMaestro.Cancel('Cancel');}});</script>
    </body></html>"""
    hp = os.path.expanduser(html_path)
    os.makedirs(os.path.dirname(hp), exist_ok=True)
    with open(hp, "w", encoding="utf-8") as out: out.write(err)
    sys.exit(0)

# --- KM VARIABLE SUBSTITUTION ---
km_envs = {k.lower(): v for k, v in os.environ.items() if k.startswith('KMVAR_')}
def replace_km_vars(text):
    if not isinstance(text, str): return text
    t = re.sub(r'%Variable%([A-Za-z0-9_]+)%', lambda m: km_envs.get(f"kmvar_{m.group(1).lower()}", m.group(0)), text, flags=re.IGNORECASE)
    return re.sub(r'%([A-Za-z0-9_]+)%?', lambda m: km_envs.get(f"kmvar_{m.group(1).lower()}", m.group(0)), t)

def process_node(node):
    if isinstance(node, dict): return {k: process_node(v) for k, v in node.items()}
    if isinstance(node, list): return [process_node(v) for v in node]
    if isinstance(node, str): return replace_km_vars(node)
    return node

cfg = process_node(cfg)

# --- CONFIGURATION ---
json_prompt, json_version = cfg.get("prompt", "Untitled"), cfg.get("version", "?.?")
message, title = cfg.get("message", ""), cfg.get("title", "Choose")
default_id, cancel_id = cfg.get("default", ""), cfg.get("cancel", "")
km_bg = os.environ.get("KMVAR_localColor", "").strip()
bg_color = cfg.get("color", "").strip() or (km_bg if km_bg else "#f2f2f2")

# --- PROCESS ROWS & BUTTONS ---
normalized_rows, all_active_buttons = [], []
has_labels = False

for r in cfg.get("rows", []):
    row_btns = r.get("buttons", []) if isinstance(r, dict) else r
    lbl = r.get("label", "").strip() if isinstance(r, dict) else ""
    if lbl: has_labels = True
    v_btns = []

    for b in row_btns:
        b_type, b_key = b.get("type", "button").lower(), b.get("key", "").strip()
        if "label" not in b: b["label"] = b.get("name", "???")
        v_btns.append(b)
        if b_type in ("hidden", "button") and b_key: all_active_buttons.append(b)

    if v_btns or lbl:
        r_data = {"label": lbl, "buttons": v_btns, "line_before": "", "line_after": "", "line_color": ""}
        if isinstance(r, dict):
            r_data.update({"line_before": r.get("line-before", ""), "line_after": r.get("line-after", ""), "line_color": r.get("line-color", "")})
        normalized_rows.append(r_data)

# --- GEOMETRY CALCULATIONS ---
CHAR_W, MIN_BTN_W, PAD_X = 8.0, 60, 10
max_lbl_len = max([len(b.get("label", "")) for r in normalized_rows for b in r["buttons"] if b.get("type", "button").lower() != "input"] + [0])
BTN_W = max(int((max_lbl_len * CHAR_W) + PAD_X), MIN_BTN_W)

LBL_COL_W, LBL_GAP = (int(max([len(r["label"]) for r in normalized_rows] + [0]) * 8.5) + 5, 12) if has_labels else (0, 0)
max_btn_area_w = 0
line_count = sum(1 for r in normalized_rows if r["line_before"]) + sum(1 for r in normalized_rows if r["line_after"])

for r in normalized_rows:
    cur_w = sum(int(str(b["width"]).replace('px','')) if b.get("type","button").lower()=="input" and "width" in b else BTN_W for b in r["buttons"])
    if len(r["buttons"]) > 1: cur_w += (len(r["buttons"]) - 1) * 6
    max_btn_area_w = max(max_btn_area_w, cur_w)

win_w = max(30 + LBL_COL_W + LBL_GAP + max_btn_area_w, len(title)*10 + len(message)*8 + len(f"{json_prompt} {json_version} {VERSION}")*7 + 80, 280)
win_h = 24 + 34 + (len(normalized_rows) * 30) + (max(0, len(normalized_rows) - 1) * 8) + (line_count * 14)
km_window_geometry = f"SCREENVISIBLE(Main,MidX)-{int(win_w/2)},SCREENVISIBLE(Main,MidY)-{int(win_h/2)},{int(win_w)},{int(win_h)}"

# --- KEY MAPPING ---
key_behavior = {}
for b in all_active_buttons:
    b_name, b_param = b.get("name", "???"), b.get("param", "")
    for part in [p.strip() for p in b.get("key","").split(',') if p.strip()]:
        mods = set()
        rem = part
        while True:
            m = re.match(r"^(command|cmd|⌘|option|opt|alt|⌥|control|ctrl|⌃)[\-\+\s]*", rem, re.IGNORECASE)
            if not m: break
            rm = m.group(1).lower()
            if rm in ('command','cmd','⌘'): mods.add('cmd-')
            elif rm in ('option','opt','alt','⌥'): mods.add('opt-')
            elif rm in ('control','ctrl','⌃'): mods.add('ctrl-')
            rem = rem[m.end():]

        pfx = ("cmd-" if "cmd-" in mods else "") + ("ctrl-" if "ctrl-" in mods else "") + ("opt-" if "opt-" in mods else "")
        base_key = rem
        nm = re.match(r"^(keypad|numpad|num)[\-\s]*", base_key, re.IGNORECASE)
        is_num = bool(nm)
        if nm: base_key = base_key[nm.end():]

        rng_m = re.match(r"^([A-Za-z0-9])-([A-Za-z0-9])$", base_key)
        if rng_m:
            s, e = rng_m.group(1), rng_m.group(2)
            rng = range(int(min(s,e)), int(max(s,e))+1) if s.isdigit() and e.isdigit() else range(ord(min(s,e)), ord(max(s,e))+1)
            for i in rng: key_behavior[f"{pfx}{'num' if is_num else ''}{i if s.isdigit() else chr(i)}"] = {"baseName": b_name, "param": b_param}
        else:
            key_behavior[f"{pfx}{'num' if is_num else ''}{base_key}"] = {"baseName": b_name, "param": b_param}
            if base_key.lower() == "esc": key_behavior[f"{pfx}escape"] = {"baseName": b_name, "param": b_param}

html_out = f"""<!doctype html><html><head><meta charset="utf-8"><title>{html.escape(title)}</title>
<style>
body{{margin:0;padding:12px 15px;box-sizing:border-box;font-family:-apple-system,system-ui;font-size:13px;background:{bg_color};overflow:hidden;}}
.hr{{display:flex;justify-content:space-between;align-items:baseline;margin-bottom:12px;width:100%;gap:16px;}}
.hl{{display:flex;gap:12px;align-items:baseline;overflow:hidden;flex:1;min-width:0;}}
.t{{font-weight:600;font-size:14px;white-space:nowrap;}}
.dbg{{color:#d73a49;font-weight:bold;font-size:11px;display:none;background:#ffebeb;padding:2px 6px;border-radius:4px;border:1px solid #fcc;margin-left:8px;}}
.m{{opacity:0.85;font-size:12px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}}
.hr-r{{text-align:right;font-size:11px;opacity:0.5;white-space:nowrap;flex-shrink:0;}}
#c{{display:flex;flex-direction:column;width:100%;}}
.r{{display:flex;align-items:stretch;gap:6px;margin-bottom:8px;width:100%;}}
.rl{{width:{LBL_COL_W}px;margin-right:{LBL_GAP}px;font-style:italic;opacity:0.7;text-align:right;flex-shrink:0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;display:flex;align-items:center;justify-content:flex-end;}}
.s{{width:100%;margin:2px 0 10px 0;border:0;flex-shrink:0;}}
.s.thin{{border-top:1px solid rgba(0,0,0,0.15);}}
.s.thick{{border-top:2px solid rgba(0,0,0,0.25);}}
.s.dotted{{border-top:1px dotted rgba(0,0,0,0.3);}}
.i{{width:{BTN_W}px;flex:0 0 {BTN_W}px;min-height:30px;display:flex;justify-content:center;align-items:center;text-align:center;box-sizing:border-box;font-size:13px;}}
button.i{{cursor:pointer;border-radius:6px;border:1px solid rgba(0,0,0,0.2);background:#fff;padding:0 2px;white-space:nowrap;}}
button#db{{background:#1f6feb!important;color:#fff!important;border-color:#1f6feb!important;}}
button:focus{{outline:2px solid rgba(31,111,235,0.6);outline-offset:1px;z-index:10;}}
input.i{{background:#fff;border:1px solid rgba(0,0,0,0.2);border-radius:6px;padding:0 8px;color:#333;text-align:left;outline:none;transition:.15s;}}
input.i:focus{{border-color:#1f6feb;box-shadow:0 0 0 2px rgba(31,111,235,0.3);z-index:10;}}
.p{{background:transparent;border:none;color:inherit;cursor:default;white-space:normal;word-wrap:break-word;line-height:1.1;padding:0 2px;}}
.inv{{visibility:hidden;pointer-events:none;}}
.fb{{font-weight:bold;}} .fi{{font-style:italic;}} .fbi{{font-weight:bold;font-style:italic;}}
</style></head><body data-kmwindow="{km_window_geometry}">
<div class="hr"><div class="hl"><div class="t">{html.escape(title)}<span id="dbg-badge" class="dbg">DEBUG MODE</span></div><div class="m">{html.escape(message)}</div></div>
<div class="hr-r">{html.escape(json_prompt)} [v{html.escape(json_version)}] &nbsp; {VERSION}</div></div><div id="c"></div>
<script>
const rs={json.dumps(normalized_rows, ensure_ascii=False)}, did={json.dumps(default_id)}, cid={json.dumps(cancel_id)}, kb={json.dumps(key_behavior)};

let isDebug = false;

function KMInit() {{
  if(window.KeyboardMaestro) {{
    isDebug = (window.KeyboardMaestro.GetVariable('Local_PromptDebug') === 'Y' || window.KeyboardMaestro.GetVariable('localPromptDebug') === 'Y');
    if(isDebug) {{
      let b = document.getElementById('dbg-badge');
      if(b) b.style.display = 'inline-block';
    }}
  }}
}}

function sub(i,m,k,p){{
  if(window.KeyboardMaestro){{
    let dbgVars = "";
    document.querySelectorAll('input[data-in="1"]').forEach(inp=>{{
      if(inp.id) {{
        window.KeyboardMaestro.SetVariable(inp.id,inp.value);
        if(isDebug) dbgVars += inp.id + ": " + inp.value + "\\n";
      }}
    }});

    if(isDebug && dbgVars !== "") {{
      window.KeyboardMaestro.SetVariable('localPromptDebugVars', dbgVars.trim());
    }}

    window.KeyboardMaestro.Submit(`${{i}}:${{m||""}}:${{k||""}}:${{p||""}}`);
  }}
}}
const ct=document.getElementById('c');
function cl(st,co){{let d=document.createElement('div');d.className='s '+st;if(co)d.style.borderTopColor=co;ct.appendChild(d);}}
rs.forEach(r=>{{
  if(r.line_before)cl(r.line_before,r.line_color);
  let rd=document.createElement('div');rd.className='r';
  if({'true' if has_labels else 'false'}){{let l=document.createElement('div');l.className='rl';l.textContent=r.label||"";rd.appendChild(l);}}
  r.buttons.forEach(b=>{{
    let t=(b.type||"button").toLowerCase(), fc=b.font==="both"?"fbi":b.font==="bold"?"fb":b.font==="italics"?"fi":"";
    if(t==="phrase"){{let s=document.createElement('div');s.className=`i p ${{fc}}`;s.textContent=b.label;rd.appendChild(s);}}
    else if(t==="hidden"){{let s=document.createElement('button');s.className=`i inv`;s.textContent=b.label;rd.appendChild(s);}}
    else if(t==="input"){{
      let ip=document.createElement('input');ip.type='text';ip.className=`i ${{fc}}`;ip.id=b.name||'i_'+Math.random();ip.value=b.default||"";ip.dataset.in="1";
      if(b.width){{ip.style.width=b.width+'px';ip.style.flex=`0 0 ${{b.width}}px`;}}rd.appendChild(ip);
    }}else{{
      let bt=document.createElement('button');bt.className=`i ${{fc}}`;bt.textContent=b.label;bt.tabIndex=-1;
      if(b.color){{bt.style.borderColor=b.color;bt.style.borderWidth="2px";}}
      bt.onclick=(e)=>{{
        let m="";if(e.ctrlKey)m+="⌃";if(e.altKey)m+="⌥";if(e.shiftKey)m+="⇧";if(e.metaKey)m+="⌘";
        sub(b.name,m,"",b.param);
      }};
      if(b.name===did)bt.id='db';rd.appendChild(bt);
    }}
  }});
  ct.appendChild(rd);if(r.line_after)cl(r.line_after,r.line_color);
}});
let df=document.getElementById('db')||ct.querySelector('button:not(.inv)');if(df)df.focus();
document.addEventListener('keydown',e=>{{
  let k=e.key, kl=k.toLowerCase(), ac=document.activeElement;
  if(ac&&ac.tagName==='INPUT'){{
    if(kl==='escape'||kl==='enter'){{e.preventDefault();ac.blur();return;}}
    if(kl==='tab')return; return;
  }}
  if(kl==='escape'){{e.preventDefault();if(cid)sub(cid,"","escape","");else window.KeyboardMaestro.Cancel('Cancel');return;}}
  if(kl==='enter'&&e.code!=='NumpadEnter'){{
    if(did){{e.preventDefault();let m="";if(e.ctrlKey)m+="⌃";if(e.altKey)m+="⌥";if(e.shiftKey)m+="⇧";if(e.metaKey)m+="⌘";sub(did,m,"enter","");return;}}
  }}
  let px="";if(e.metaKey)px+="cmd-";if(e.ctrlKey)px+="ctrl-";if(e.altKey)px+="opt-";
  let bh=null, fk=k;
  if(e.code&&e.code.startsWith('Numpad')){{let d=e.code.slice(6);if(kb[px+"num"+d]){{bh=kb[px+"num"+d];fk=d;}}}}
  if(!bh){{
    bh=kb[px+k]||kb[k]||kb[kl];
    if(!bh&&e.code){{
      let ph=null;if(e.code.startsWith('Digit'))ph=e.code.slice(5);else if(e.code.startsWith('Numpad'))ph=e.code.slice(6);else if(e.code.startsWith('Key'))ph=e.code.slice(3).toLowerCase();
      if(ph){{bh=kb[px+ph]||kb[ph];if(bh)fk=ph;}}
    }}
  }}
  if(bh){{
    e.preventDefault();let m="";if(e.ctrlKey)m+="⌃";if(e.altKey)m+="⌥";if(e.shiftKey)m+="⇧";if(e.metaKey)m+="⌘";sub(bh.baseName,m,fk,bh.param);
  }} else if(isDebug && !['Meta','Control','Alt','Shift','CapsLock','Tab'].includes(k)) {{
    e.preventDefault();let m="";if(e.ctrlKey)m+="⌃";if(e.altKey)m+="⌥";if(e.shiftKey)m+="⇧";if(e.metaKey)m+="⌘";sub("NO MATCH",m,k,"");
  }}
}});
</script></body></html>"""

hp = os.path.expanduser(html_path)
os.makedirs(os.path.dirname(hp), exist_ok=True)
with open(hp, "w", encoding="utf-8") as out: out.write(html_out)
PY
