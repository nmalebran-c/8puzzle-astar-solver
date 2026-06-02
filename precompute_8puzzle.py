#!/usr/bin/env python3
"""
precompute_8puzzle.py
Pre-computa el espacio de estados del 8-puzzle y genera 8puzzle_visualizacion.html
con carga instantánea, nodos coloreados por profundidad BFS e inspección de estados.

Uso:
    python precompute_8puzzle.py
"""
import math, base64, struct, time, sys
from collections import deque


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    print("=== 8-Puzzle: Pre-computo del Espacio de Estados ===\n")

    # ── 1. BFS ────────────────────────────────────────────────────────────
    print("1/4  BFS desde estado objetivo...", end=" ", flush=True)
    t0 = time.perf_counter()

    NB = [
        [1, 3], [0, 2, 4], [1, 5],
        [0, 4, 6], [1, 3, 5, 7], [2, 4, 8],
        [3, 7], [4, 6, 8], [5, 7],
    ]

    goal = (1, 2, 3, 4, 5, 6, 7, 8, 0)
    state_to_id: dict[tuple, int] = {goal: 0}
    id_to_state: list[tuple] = [goal]
    id_to_dist:  list[int]   = [0]
    edges_a: list[int] = []
    edges_b: list[int] = []
    diameter = 0

    queue: deque[tuple[tuple, int, int]] = deque()
    queue.append((goal, 0, 8))  # (state, id, blank_pos)

    while queue:
        state, sid, blank = queue.popleft()
        d = id_to_dist[sid]
        sl = list(state)

        for sw in NB[blank]:
            sl[blank], sl[sw] = sl[sw], sl[blank]
            ns = tuple(sl)
            sl[blank], sl[sw] = sl[sw], sl[blank]

            if ns not in state_to_id:
                nid = len(id_to_state)
                state_to_id[ns] = nid
                id_to_state.append(ns)
                nd = d + 1
                id_to_dist.append(nd)
                if nd > diameter:
                    diameter = nd
                queue.append((ns, nid, sw))
            else:
                nid = state_to_id[ns]

            if sid < nid:
                edges_a.append(sid)
                edges_b.append(nid)

    N = len(id_to_state)
    E = len(edges_a)
    print(f"N={N:,}  E={E:,}  diam={diameter}  ({time.perf_counter()-t0:.1f}s)")

    # ── 2. LAYOUT RADIAL POR PROFUNDIDAD ──────────────────────────────────
    print("2/4  Layout radial...", end=" ", flush=True)
    t1 = time.perf_counter()
    RBASE = 180.0
    level_seen = [0] * (diameter + 1)
    pos_x: list[float] = []
    pos_y: list[float] = []
    for i in range(N):
        d = id_to_dist[i]
        seen = level_seen[d]
        level_seen[d] += 1
        r = RBASE * math.sqrt(d + 0.5) + math.sin(seen * 1.7 + d * 2.3) * 8
        ang = (seen * 0.61803398875 % 1.0) * math.tau
        pos_x.append(math.cos(ang) * r)
        pos_y.append(math.sin(ang) * r)
    print(f"({time.perf_counter()-t1:.1f}s)")

    # ── 3. SERIALIZACIÓN BASE64 ───────────────────────────────────────────
    print("3/4  Empaquetando datos...", end=" ", flush=True)
    t2 = time.perf_counter()

    def b64(data: bytes) -> str:
        return base64.b64encode(data).decode()

    states_flat = bytearray()
    for s in id_to_state:
        states_flat.extend(s)

    px_b64 = b64(struct.pack(f"<{N}f", *pos_x))
    py_b64 = b64(struct.pack(f"<{N}f", *pos_y))
    di_b64 = b64(bytes(id_to_dist))
    st_b64 = b64(bytes(states_flat))
    ea_b64 = b64(struct.pack(f"<{E}I", *edges_a))
    eb_b64 = b64(struct.pack(f"<{E}I", *edges_b))

    kb = (len(px_b64)+len(py_b64)+len(di_b64)+len(st_b64)+len(ea_b64)+len(eb_b64)) // 1024
    print(f"~{kb:,} KB ({time.perf_counter()-t2:.1f}s)")

    # ── 4. GENERAR HTML ───────────────────────────────────────────────────
    print("4/4  Generando HTML...", end=" ", flush=True)
    html = build_html(N, E, diameter, px_b64, py_b64, di_b64, st_b64, ea_b64, eb_b64)
    out = "8puzzle_visualizacion.html"
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"-> {out} ({len(html)//1024:,} KB)\n")
    print("Listo. Abre 8puzzle_visualizacion.html en tu navegador.")


# ── Colores por profundidad (hue 220°→0°) ────────────────────────────────────
def _depth_colors(diameter: int) -> list[str]:
    colors = []
    for d in range(diameter + 1):
        t = d / max(diameter, 1)
        hue = int(220 - t * 220)
        colors.append(f"hsl({hue},85%,58%)")
    return colors


def build_html(N, E, diameter, px_b64, py_b64, di_b64, st_b64, ea_b64, eb_b64) -> str:
    import json
    colors_js = json.dumps(_depth_colors(diameter))

    return f"""<!DOCTYPE html>
<html lang="es" data-theme="dark">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>8-Puzzle · Espacio de Estados (pre-computado)</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
:root{{
  --bg0:#07090f;--bg1:#0d1120;--bg2:#111827;--bg3:#1a2236;
  --border:rgba(255,255,255,.07);--border-m:rgba(255,255,255,.11);--border-h:rgba(255,255,255,.2);
  --accent:#818cf8;--accent-d:#6366f1;--accent-bg:rgba(99,102,241,.12);--accent-bd:rgba(99,102,241,.35);
  --success:#34d399;--warn:#fbbf24;--danger:#f87171;
  --t1:#f1f5f9;--t2:#94a3b8;--t3:#475569;
  --edge:rgba(148,163,184,.15);--canvas-bg:#080b14;
  --panel-bg:#0d1120;--tile-bg:#1e293b;--tile-empty:#0d1120;
}}
[data-theme="light"]{{
  --bg0:#f0f2f5;--bg1:#e8ecf1;--bg2:#fff;--bg3:#f4f6f9;
  --border:rgba(0,0,0,.07);--border-m:rgba(0,0,0,.11);--border-h:rgba(0,0,0,.2);
  --accent:#6366f1;--accent-d:#4f46e5;--accent-bg:rgba(99,102,241,.08);--accent-bd:rgba(99,102,241,.3);
  --success:#059669;--warn:#d97706;--danger:#dc2626;
  --t1:#0f172a;--t2:#64748b;--t3:#94a3b8;
  --edge:rgba(71,85,105,.2);--canvas-bg:#fff;
  --panel-bg:#f0f2f5;--tile-bg:#e2e8f0;--tile-empty:#f0f2f5;
}}
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:'Inter',-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
      background:var(--bg0);color:var(--t1);min-height:100vh;-webkit-font-smoothing:antialiased}}
.page{{max-width:1400px;margin:0 auto;padding:1.5rem 1.25rem 2.5rem}}

/* ── Header ── */
.header{{display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:1rem;gap:1rem}}
.htitle{{font-size:clamp(1.15rem,2.5vw,1.6rem);font-weight:700;letter-spacing:-.03em;
         display:flex;align-items:center;gap:10px;flex-wrap:wrap}}
.badge{{display:inline-flex;align-items:center;gap:5px;font-size:10px;font-weight:700;
        letter-spacing:.09em;text-transform:uppercase;padding:3px 9px;border-radius:20px;
        border:1px solid var(--accent-bd);background:var(--accent-bg);color:var(--accent)}}
.hsub{{font-size:12.5px;color:var(--t2);margin-top:3px}}
.hbtns{{display:flex;gap:6px;flex-shrink:0}}

/* ── Metric cards ── */
.metrics{{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-bottom:1rem}}
.mcard{{background:var(--bg2);border:1px solid var(--border);border-radius:10px;
        padding:.75rem .9rem;transition:border-color .2s}}
.mcard:hover{{border-color:var(--border-m)}}
.micon{{width:22px;height:22px;border-radius:6px;display:flex;align-items:center;
        justify-content:center;margin-bottom:5px;font-size:11px}}
.ic-a{{background:var(--accent-bg);color:var(--accent)}}
.ic-b{{background:rgba(59,130,246,.12);color:#60a5fa}}
.ic-c{{background:rgba(251,191,36,.12);color:#fbbf24}}
.ic-d{{background:rgba(52,211,153,.1);color:#34d399}}
.mlbl{{font-size:10px;color:var(--t2);font-weight:500;margin-bottom:2px}}
.mval{{font-size:20px;font-weight:700;font-family:'JetBrains Mono',monospace;color:var(--t1);line-height:1}}

/* ── Main layout ── */
.main{{display:grid;grid-template-columns:1fr 280px;gap:10px;align-items:start}}
@media(max-width:900px){{.main{{grid-template-columns:1fr}}}}

/* ── Canvas card ── */
.ccard{{background:var(--bg2);border:1px solid var(--border);border-radius:16px;overflow:hidden}}
.chead{{padding:.75rem 1rem;border-bottom:1px solid var(--border);display:flex;
        align-items:center;justify-content:space-between;flex-wrap:wrap;gap:6px}}
.clbl{{font-size:10px;font-weight:600;text-transform:uppercase;letter-spacing:.09em;
       color:var(--t3);display:flex;align-items:center;gap:6px}}

.controls{{padding:.65rem .9rem;border-bottom:1px solid var(--border);
           display:flex;flex-wrap:wrap;gap:6px;align-items:center}}
.btn{{display:inline-flex;align-items:center;gap:5px;padding:6px 12px;
      font-family:'Inter',sans-serif;font-size:12.5px;font-weight:500;
      border-radius:8px;border:1px solid var(--border-m);background:var(--bg3);
      color:var(--t1);cursor:pointer;transition:all .15s;white-space:nowrap;line-height:1}}
.btn:hover:not(:disabled){{background:var(--bg1);border-color:var(--border-h)}}
.btn:active:not(:disabled){{transform:scale(.95)}}
.btn-primary{{background:var(--accent-d);border-color:var(--accent-d);color:#fff}}
.btn-ghost{{background:transparent;color:var(--t2)}}
.btn-ghost:hover:not(:disabled){{background:var(--bg3);color:var(--t1)}}
.vd{{width:1px;height:20px;background:var(--border-m);margin:0 1px}}
.tog{{display:flex;background:var(--bg3);border:1px solid var(--border);
      border-radius:8px;overflow:hidden}}
.tog .btn{{border:none;border-radius:0;padding:5px 10px;font-size:11.5px;background:transparent}}
.tog .btn.on{{background:var(--accent-bg);color:var(--accent)}}

.canvas-wrap{{position:relative;background:var(--canvas-bg);height:min(68vh,780px)}}
#gc{{display:block;width:100%;height:100%;cursor:grab}}
#gc:active{{cursor:grabbing}}
.hint{{position:absolute;bottom:8px;left:10px;font-size:10.5px;
       font-family:'JetBrains Mono',monospace;color:var(--t3);
       background:rgba(0,0,0,.4);padding:3px 8px;border-radius:5px;
       backdrop-filter:blur(8px);pointer-events:none}}
[data-theme="light"] .hint{{background:rgba(255,255,255,.75);color:var(--t2)}}

/* ── Side panel ── */
.panel{{background:var(--panel-bg);border:1px solid var(--border);
        border-radius:14px;padding:1rem;display:flex;flex-direction:column;gap:10px;
        position:sticky;top:1rem}}
.plbl{{font-size:10px;font-weight:700;text-transform:uppercase;
       letter-spacing:.09em;color:var(--t3);margin-bottom:2px}}
.pval{{font-size:13px;font-family:'JetBrains Mono',monospace;color:var(--t1)}}
.pnone{{font-size:12px;color:var(--t3);font-style:italic;text-align:center;padding:1.5rem 0}}

/* Puzzle grid */
.pgrid{{display:grid;grid-template-columns:repeat(3,1fr);gap:4px;margin-top:4px}}
.ptile{{height:48px;border-radius:6px;background:var(--tile-bg);border:1px solid var(--border-m);
        display:flex;align-items:center;justify-content:center;
        font-size:18px;font-weight:700;font-family:'JetBrains Mono',monospace;
        color:var(--t1);transition:background .2s}}
.ptile.empty{{background:var(--tile-empty);border-style:dashed;color:var(--t3)}}
.ptile.goal-pos{{background:rgba(52,211,153,.15);border-color:rgba(52,211,153,.4);color:#34d399}}

/* Depth legend */
.legend{{display:flex;flex-direction:column;gap:3px}}
.leg-row{{display:flex;align-items:center;gap:6px;font-size:11px;color:var(--t2)}}
.leg-dot{{width:10px;height:10px;border-radius:50%;flex-shrink:0}}
.leg-bar{{height:8px;border-radius:4px;flex:1}}

/* Depth filter */
.dfilter{{display:flex;flex-direction:column;gap:5px}}
.range-row{{display:flex;align-items:center;gap:6px;font-size:11.5px;color:var(--t2)}}
.range-row input[type=range]{{flex:1;accent-color:var(--accent)}}
.range-row span{{font-family:'JetBrains Mono',monospace;min-width:22px;text-align:right}}

/* Search */
.search-wrap{{display:flex;gap:5px}}
.search-inp{{flex:1;padding:6px 9px;font-size:12px;font-family:'JetBrains Mono',monospace;
             background:var(--bg3);border:1px solid var(--border-m);border-radius:7px;
             color:var(--t1);outline:none;transition:border-color .2s}}
.search-inp:focus{{border-color:var(--accent-bd)}}
.search-inp.found{{border-color:var(--success)}}
.search-inp.notfound{{border-color:var(--danger)}}

/* Status bar */
.sbar{{padding:.45rem .9rem;background:var(--bg1);border-bottom:1px solid var(--border);
       font-size:11.5px;font-family:'JetBrains Mono',monospace;
       color:var(--success);min-height:28px;display:flex;align-items:center;gap:7px}}

@media(max-width:640px){{
  .metrics{{grid-template-columns:1fr 1fr}}
  .page{{padding:1rem .75rem 2rem}}
}}
</style>
</head>
<body>
<div class="page">

<header class="header">
  <div>
    <div class="htitle">
      Espacio de Estados · 8-Puzzle
      <span class="badge">Pre-computado · Instantáneo</span>
    </div>
    <div class="hsub">9!/2 = 181,440 estados resolubles · datos embebidos, carga inmediata</div>
  </div>
  <div class="hbtns">
    <button class="btn btn-ghost" id="btn-theme" title="Cambiar tema">
      <svg id="theme-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
      </svg>
    </button>
  </div>
</header>

<div class="metrics">
  <div class="mcard"><div class="micon ic-a">⬡</div><div class="mlbl">Estados (nodos)</div><div class="mval">{N:,}</div></div>
  <div class="mcard"><div class="micon ic-b">╌</div><div class="mlbl">Transiciones (aristas)</div><div class="mval">{E:,}</div></div>
  <div class="mcard"><div class="micon ic-c">◎</div><div class="mlbl">Diámetro máx.</div><div class="mval">{diameter}</div></div>
  <div class="mcard"><div class="micon ic-d">⚡</div><div class="mlbl">Tiempo de carga</div><div class="mval" id="m-load">—</div></div>
</div>

<div class="main">
  <!-- Canvas -->
  <div class="ccard">
    <div class="chead">
      <span class="clbl">Grafo del espacio de estados</span>
      <span style="font-size:11px;color:var(--t3);font-family:'JetBrains Mono',monospace" id="vis-info">—</span>
    </div>
    <div class="controls">
      <button class="btn btn-ghost" id="btn-fit">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M3 7V3h4M21 7V3h-4M3 17v4h4M21 17v4h-4"/></svg>
        Ajustar
      </button>
      <div class="vd"></div>
      <div class="tog">
        <button class="btn on" id="t-edges">Aristas</button>
        <button class="btn on" id="t-nodes">Nodos</button>
        <button class="btn on" id="t-color">Color</button>
      </div>
      <div class="vd"></div>
      <span style="font-size:11px;color:var(--t3);font-family:'JetBrains Mono',monospace">Rueda: zoom · Arrastrar: pan · Clic: inspeccionar</span>
    </div>
    <div class="sbar" id="sbar">Listo · {N:,} estados · {E:,} aristas</div>
    <div class="canvas-wrap">
      <canvas id="gc"></canvas>
      <div class="hint" id="hint">zoom 1.0×</div>
    </div>
  </div>

  <!-- Side panel -->
  <div class="panel" id="panel">
    <div>
      <div class="plbl">Filtro por profundidad BFS</div>
      <div class="dfilter">
        <div class="range-row">
          <span style="color:var(--t3)">Mín</span>
          <input type="range" id="dmin" min="0" max="{diameter}" value="0" step="1">
          <span id="dmin-val">0</span>
        </div>
        <div class="range-row">
          <span style="color:var(--t3)">Máx</span>
          <input type="range" id="dmax" min="0" max="{diameter}" value="{diameter}" step="1">
          <span id="dmax-val">{diameter}</span>
        </div>
      </div>
    </div>

    <div>
      <div class="plbl">Buscar estado</div>
      <div style="font-size:10.5px;color:var(--t3);margin-bottom:4px">9 dígitos separados por espacios (0 = hueco)</div>
      <div class="search-wrap">
        <input class="search-inp" id="search-inp" type="text" placeholder="1 2 3 4 5 6 7 8 0" maxlength="17">
        <button class="btn" id="btn-search">Ir</button>
      </div>
    </div>

    <div>
      <div class="plbl">Estado seleccionado</div>
      <div id="state-info"><div class="pnone">Haz clic en un nodo del grafo</div></div>
    </div>

    <div>
      <div class="plbl">Leyenda de profundidad</div>
      <div class="legend" id="legend"></div>
    </div>
  </div>
</div>

</div><!-- .page -->

<script>
/* ── DATOS PRE-COMPUTADOS ───────────────────────────────────────────────── */
const N={N}, E={E}, DIAM={diameter};
const DEPTH_COLORS={colors_js};

const _px="{px_b64}",_py="{py_b64}",_di="{di_b64}",_st="{st_b64}",_ea="{ea_b64}",_eb="{eb_b64}";

function b64ToBuffer(b64,Type){{
  const bin=atob(b64), buf=new ArrayBuffer(bin.length), u8=new Uint8Array(buf);
  for(let i=0;i<bin.length;i++) u8[i]=bin.charCodeAt(i);
  return new Type(buf);
}}

const t0=performance.now();
const posX=b64ToBuffer(_px,Float32Array);
const posY=b64ToBuffer(_py,Float32Array);
const dist=b64ToBuffer(_di,Uint8Array);
const states=b64ToBuffer(_st,Uint8Array);   // N*9 bytes, stride 9
const edgesA=b64ToBuffer(_ea,Uint32Array);
const edgesB=b64ToBuffer(_eb,Uint32Array);
const loadMs=(performance.now()-t0).toFixed(0);
document.getElementById('m-load').textContent=loadMs+'ms';

/* ── TEMA ── */
const html=document.documentElement;
let dark=true;
const MOON='<path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>';
const SUN='<circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>';
document.getElementById('btn-theme').addEventListener('click',()=>{{
  dark=!dark;
  html.setAttribute('data-theme',dark?'dark':'light');
  document.getElementById('theme-icon').innerHTML=dark?MOON:SUN;
  readColors(); scheduleDraw();
}});

/* ── FILTRO PROFUNDIDAD ── */
let dMin=0, dMax=DIAM;
const dminEl=document.getElementById('dmin'), dmaxEl=document.getElementById('dmax');
const dminV=document.getElementById('dmin-val'), dmaxV=document.getElementById('dmax-val');
dminEl.addEventListener('input',()=>{{
  dMin=+dminEl.value;
  if(dMin>dMax){{dMax=dMin;dmaxEl.value=dMax;dmaxV.textContent=dMax;}}
  dminV.textContent=dMin; updateVisInfo(); scheduleDraw();
}});
dmaxEl.addEventListener('input',()=>{{
  dMax=+dmaxEl.value;
  if(dMax<dMin){{dMin=dMax;dminEl.value=dMin;dminV.textContent=dMin;}}
  dmaxV.textContent=dMax; updateVisInfo(); scheduleDraw();
}});

function updateVisInfo(){{
  let cnt=0; for(let i=0;i<N;i++) if(dist[i]>=dMin&&dist[i]<=dMax) cnt++;
  document.getElementById('vis-info').textContent=`mostrando ${{cnt.toLocaleString('es-CL')}} nodos`;
}}

/* ── LEYENDA ── */
(function buildLegend(){{
  const lg=document.getElementById('legend');
  const step=Math.max(1,Math.floor(DIAM/8));
  for(let d=0;d<=DIAM;d+=step){{
    const row=document.createElement('div'); row.className='leg-row';
    row.innerHTML=`<div class="leg-dot" style="background:${{DEPTH_COLORS[d]}}"></div>
                   <span>Prof. ${{d}}</span>`;
    lg.appendChild(row);
  }}
}})();

/* ── CANVAS ── */
const canvas=document.getElementById('gc');
const ctx=canvas.getContext('2d',{{alpha:false}});
let CW=0,CH=0,DPR=1;
let view={{x:0,y:0,scale:1}};
let needsDraw=true;
let COL={{}};

function readColors(){{
  const cs=getComputedStyle(document.body);
  COL.bg=cs.getPropertyValue('--canvas-bg').trim();
  COL.edge=cs.getPropertyValue('--edge').trim();
}}
readColors();

let showEdges=true,showNodes=true,useColor=true;
let selectedNode=-1,highlightNode=-1;

function resize(){{
  const wrap=canvas.parentElement;
  DPR=window.devicePixelRatio||1;
  CW=wrap.clientWidth; CH=wrap.clientHeight;
  canvas.width=CW*DPR; canvas.height=CH*DPR;
  canvas.style.width=CW+'px'; canvas.style.height=CH+'px';
  scheduleDraw();
}}
window.addEventListener('resize',resize);

function fitToView(){{
  let mnX=Infinity,mxX=-Infinity,mnY=Infinity,mxY=-Infinity;
  for(let i=0;i<N;i++){{
    const d=dist[i]; if(d<dMin||d>dMax) continue;
    const x=posX[i],y=posY[i];
    if(x<mnX)mnX=x;if(x>mxX)mxX=x;if(y<mnY)mnY=y;if(y>mxY)mxY=y;
  }}
  const w=mxX-mnX||1,h=mxY-mnY||1,pad=40;
  view.scale=Math.min((CW-2*pad)/w,(CH-2*pad)/h);
  view.x=CW/2-(mnX+w/2)*view.scale;
  view.y=CH/2-(mnY+h/2)*view.scale;
  scheduleDraw();
}}

function scheduleDraw(){{needsDraw=true;}}

function draw(){{
  if(!needsDraw)return;
  needsDraw=false;

  ctx.setTransform(DPR,0,0,DPR,0,0);
  ctx.fillStyle=COL.bg; ctx.fillRect(0,0,CW,CH);
  ctx.setTransform(DPR*view.scale,0,0,DPR*view.scale,DPR*view.x,DPR*view.y);

  const vx0=-view.x/view.scale, vy0=-view.y/view.scale;
  const vx1=vx0+CW/view.scale, vy1=vy0+CH/view.scale;

  // ── Aristas ──
  if(showEdges){{
    ctx.strokeStyle=COL.edge;
    ctx.lineWidth=Math.max(0.35,0.55/view.scale);
    ctx.beginPath(); let segs=0;
    for(let k=0;k<E;k++){{
      const a=edgesA[k],b=edgesB[k];
      const da=dist[a],db=dist[b];
      if(da<dMin||da>dMax||db<dMin||db>dMax) continue;
      const ax=posX[a],ay=posY[a],bx=posX[b],by=posY[b];
      if((ax<vx0&&bx<vx0)||(ax>vx1&&bx>vx1)||(ay<vy0&&by<vy0)||(ay>vy1&&by>vy1)) continue;
      ctx.moveTo(ax,ay); ctx.lineTo(bx,by); segs++;
      if(segs>=60000){{ctx.stroke();ctx.beginPath();segs=0;}}
    }}
    if(segs>0) ctx.stroke();
  }}

  // ── Nodos ──
  if(showNodes){{
    const r=Math.max(0.5,1.4/view.scale);
    const small=r*view.scale<2;

    if(!useColor){{
      ctx.fillStyle=dark?'#60a5fa':'#2563eb';
      if(small){{
        for(let i=0;i<N;i++){{
          const d=dist[i]; if(d<dMin||d>dMax) continue;
          const x=posX[i],y=posY[i];
          if(x<vx0||x>vx1||y<vy0||y>vy1) continue;
          ctx.fillRect(x-r,y-r,r*2,r*2);
        }}
      }}else{{
        ctx.beginPath();
        for(let i=0;i<N;i++){{
          const d=dist[i]; if(d<dMin||d>dMax) continue;
          const x=posX[i],y=posY[i];
          if(x<vx0||x>vx1||y<vy0||y>vy1) continue;
          ctx.moveTo(x+r,y); ctx.arc(x,y,r,0,Math.PI*2);
        }}
        ctx.fill();
      }}
    }}else{{
      // Color por profundidad — agrupar por depth para menos cambios de fillStyle
      for(let d=dMin;d<=dMax;d++){{
        ctx.fillStyle=DEPTH_COLORS[d];
        if(small){{
          for(let i=0;i<N;i++){{
            if(dist[i]!==d) continue;
            const x=posX[i],y=posY[i];
            if(x<vx0||x>vx1||y<vy0||y>vy1) continue;
            ctx.fillRect(x-r,y-r,r*2,r*2);
          }}
        }}else{{
          ctx.beginPath();
          for(let i=0;i<N;i++){{
            if(dist[i]!==d) continue;
            const x=posX[i],y=posY[i];
            if(x<vx0||x>vx1||y<vy0||y>vy1) continue;
            ctx.moveTo(x+r,y); ctx.arc(x,y,r,0,Math.PI*2);
          }}
          ctx.fill();
        }}
      }}
    }}

    // Nodo seleccionado
    if(selectedNode>=0){{
      const x=posX[selectedNode],y=posY[selectedNode];
      const rh=Math.max(2.5,4/view.scale);
      ctx.beginPath(); ctx.arc(x,y,rh,0,Math.PI*2);
      ctx.fillStyle='#fff'; ctx.fill();
      ctx.strokeStyle=DEPTH_COLORS[dist[selectedNode]]||'#fff';
      ctx.lineWidth=Math.max(0.8,1.5/view.scale);
      ctx.stroke();
    }}

    // Nodo highlight (búsqueda)
    if(highlightNode>=0&&highlightNode!==selectedNode){{
      const x=posX[highlightNode],y=posY[highlightNode];
      const rh=Math.max(2,3.5/view.scale);
      ctx.beginPath(); ctx.arc(x,y,rh,0,Math.PI*2);
      ctx.fillStyle='#fbbf24'; ctx.fill();
    }}
  }}

  document.getElementById('hint').textContent=`zoom ${{view.scale.toFixed(2)}}× · nodos ${{N.toLocaleString('es-CL')}}`;
}}

requestAnimationFrame(function loop(){{ draw(); requestAnimationFrame(loop); }});

/* ── PAN / ZOOM ── */
let dragging=false,dragLast=null;
canvas.addEventListener('mousedown',e=>{{ dragging=true; dragLast={{x:e.clientX,y:e.clientY}}; }});
window.addEventListener('mouseup',()=>{{ dragging=false; }});
window.addEventListener('mousemove',e=>{{
  if(!dragging)return;
  view.x+=e.clientX-dragLast.x; view.y+=e.clientY-dragLast.y;
  dragLast={{x:e.clientX,y:e.clientY}}; scheduleDraw();
}});
canvas.addEventListener('wheel',e=>{{
  e.preventDefault();
  const rect=canvas.getBoundingClientRect();
  const mx=e.clientX-rect.left,my=e.clientY-rect.top;
  const wx=(mx-view.x)/view.scale,wy=(my-view.y)/view.scale;
  const f=e.deltaY<0?1.18:1/1.18;
  view.scale=Math.max(0.02,Math.min(80,view.scale*f));
  view.x=mx-wx*view.scale; view.y=my-wy*view.scale; scheduleDraw();
}},{{passive:false}});

/* Touch */
let ts=null;
canvas.addEventListener('touchstart',e=>{{
  if(e.touches.length===1){{ts={{mode:'pan',x:e.touches[0].clientX,y:e.touches[0].clientY}};}}
  else if(e.touches.length===2){{
    const dx=e.touches[0].clientX-e.touches[1].clientX,dy=e.touches[0].clientY-e.touches[1].clientY;
    ts={{mode:'zoom',dist:Math.hypot(dx,dy),scale:view.scale,
         cx:(e.touches[0].clientX+e.touches[1].clientX)/2,
         cy:(e.touches[0].clientY+e.touches[1].clientY)/2}};
  }}
}},{{passive:true}});
canvas.addEventListener('touchmove',e=>{{
  if(!ts)return;
  if(ts.mode==='pan'&&e.touches.length===1){{
    view.x+=e.touches[0].clientX-ts.x; view.y+=e.touches[0].clientY-ts.y;
    ts.x=e.touches[0].clientX; ts.y=e.touches[0].clientY; scheduleDraw();
  }}else if(ts.mode==='zoom'&&e.touches.length===2){{
    const dx=e.touches[0].clientX-e.touches[1].clientX,dy=e.touches[0].clientY-e.touches[1].clientY;
    const d=Math.hypot(dx,dy);
    const rect=canvas.getBoundingClientRect();
    const mx=ts.cx-rect.left,my=ts.cy-rect.top;
    const wx=(mx-view.x)/view.scale,wy=(my-view.y)/view.scale;
    view.scale=Math.max(0.02,Math.min(80,ts.scale*(d/ts.dist)));
    view.x=mx-wx*view.scale; view.y=my-wy*view.scale; scheduleDraw(); e.preventDefault();
  }}
}},{{passive:false}});
canvas.addEventListener('touchend',()=>{{ts=null;}},{{passive:true}});

/* ── CLIC: INSPECCIONAR NODO ── */
function getState(i){{
  const off=i*9;
  return Array.from(states.subarray(off,off+9));
}}
function manhattanDist(s){{
  const goal=[1,2,3,4,5,6,7,8,0];
  let d=0;
  for(let t=1;t<=8;t++){{
    const ci=s.indexOf(t),gi=goal.indexOf(t);
    d+=Math.abs((ci%3)-(gi%3))+Math.abs(Math.floor(ci/3)-Math.floor(gi/3));
  }}
  return d;
}}
function showStatePanel(i){{
  const s=getState(i);
  const d=dist[i];
  const md=manhattanDist(s);
  const goal=[1,2,3,4,5,6,7,8,0];
  let tilesHtml='';
  for(let k=0;k<9;k++){{
    const v=s[k];
    const isGoalPos=v===goal[k];
    const cls=v===0?'ptile empty':(isGoalPos?'ptile goal-pos':'ptile');
    tilesHtml+=`<div class="${{cls}}">${{v===0?'·':v}}</div>`;
  }}
  const isGoal=d===0;
  document.getElementById('state-info').innerHTML=`
    <div class="pgrid">${{tilesHtml}}</div>
    <div style="margin-top:8px;display:flex;flex-direction:column;gap:4px">
      <div class="leg-row">
        <div class="leg-dot" style="background:${{DEPTH_COLORS[d]}}"></div>
        <span style="color:var(--t1);font-weight:600">Profundidad BFS: ${{d}}</span>
        ${{isGoal?'<span style="color:var(--success);font-size:10px;font-weight:700">OBJETIVO ✓</span>':''}}
      </div>
      <div style="font-size:11.5px;color:var(--t2)">Distancia Manhattan: ${{md}}</div>
      <div style="font-size:11px;color:var(--t3);font-family:\'JetBrains Mono\',monospace">
        Nodo #${{i.toLocaleString('es-CL')}}
      </div>
      <div style="font-size:11px;color:var(--t3);font-family:\'JetBrains Mono\',monospace">
        [${{s.join(' ')}}]
      </div>
    </div>`;
}}

let lastClick=0;
canvas.addEventListener('click',e=>{{
  const now=Date.now();
  if(now-lastClick<200)return;  // ignore double-click
  lastClick=now;
  if(dragging)return;
  const rect=canvas.getBoundingClientRect();
  const mx=e.clientX-rect.left, my=e.clientY-rect.top;
  const wx=(mx-view.x)/view.scale, wy=(my-view.y)/view.scale;

  // Buscar nodo más cercano dentro de un radio razonable en coords mundo
  const pickR=Math.max(3,8/view.scale);
  const pickR2=pickR*pickR;
  let best=-1,bestD=Infinity;
  for(let i=0;i<N;i++){{
    const d=dist[i]; if(d<dMin||d>dMax) continue;
    const dx=posX[i]-wx,dy=posY[i]-wy;
    const d2=dx*dx+dy*dy;
    if(d2<pickR2&&d2<bestD){{bestD=d2;best=i;}}
  }}
  if(best>=0){{
    selectedNode=best;
    showStatePanel(best);
    document.getElementById('sbar').textContent=`Nodo ${{best.toLocaleString('es-CL')}} seleccionado · profundidad ${{dist[best]}}`;
  }}else{{
    selectedNode=-1;
    document.getElementById('state-info').innerHTML='<div class="pnone">Haz clic en un nodo del grafo</div>';
    document.getElementById('sbar').textContent=`Listo · ${{N.toLocaleString('es-CL')}} estados · ${{E.toLocaleString('es-CL')}} aristas`;
  }}
  scheduleDraw();
}});

/* ── BÚSQUEDA DE ESTADO ── */
function encodeState(s){{
  const FACT=[40320,5040,720,120,24,6,2,1,1];
  let idx=0; const used=new Uint8Array(9);
  for(let i=0;i<9;i++){{
    const t=s[i]; let rank=t;
    for(let j=0;j<t;j++) if(used[j]) rank--;
    used[t]=1; idx+=rank*FACT[i];
  }}
  return idx;
}}
document.getElementById('btn-search').addEventListener('click',doSearch);
document.getElementById('search-inp').addEventListener('keydown',e=>{{ if(e.key==='Enter') doSearch(); }});
function doSearch(){{
  const raw=document.getElementById('search-inp').value.trim();
  const nums=raw.split(/[\\s,]+/).map(Number);
  const inp=document.getElementById('search-inp');
  inp.classList.remove('found','notfound');
  if(nums.length!==9||nums.some(isNaN)||new Set(nums).size!==9||Math.max(...nums)>8||Math.min(...nums)<0){{
    inp.classList.add('notfound'); return;
  }}
  // Buscar linealmente en states array
  outer:for(let i=0;i<N;i++){{
    const off=i*9;
    for(let k=0;k<9;k++) if(states[off+k]!==nums[k]) continue outer;
    // Encontrado
    inp.classList.add('found');
    highlightNode=i;
    selectedNode=i;
    showStatePanel(i);
    // Centrar vista
    view.x=CW/2-posX[i]*view.scale;
    view.y=CH/2-posY[i]*view.scale;
    document.getElementById('sbar').textContent=`Estado encontrado: nodo ${{i.toLocaleString('es-CL')}} · profundidad ${{dist[i]}}`;
    scheduleDraw();
    return;
  }}
  inp.classList.add('notfound');
  document.getElementById('sbar').textContent='Estado no encontrado (puede ser un estado irresoluble)';
}}

/* ── CONTROLES ── */
document.getElementById('btn-fit').addEventListener('click',fitToView);
document.getElementById('t-edges').addEventListener('click',()=>{{
  showEdges=!showEdges;
  document.getElementById('t-edges').classList.toggle('on',showEdges);
  scheduleDraw();
}});
document.getElementById('t-nodes').addEventListener('click',()=>{{
  showNodes=!showNodes;
  document.getElementById('t-nodes').classList.toggle('on',showNodes);
  scheduleDraw();
}});
document.getElementById('t-color').addEventListener('click',()=>{{
  useColor=!useColor;
  document.getElementById('t-color').classList.toggle('on',useColor);
  scheduleDraw();
}});

/* ── ARRANQUE ── */
resize();
fitToView();
updateVisInfo();
</script>
</body>
</html>"""


if __name__ == "__main__":
    main()
