"""Personal Aviator dashboard and persisted-history read APIs."""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from fastapi.responses import HTMLResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.aviator_access import require_dashboard_access
from app.db import get_db
from app.models import RoundResult

router = APIRouter()


@router.get("/api/v1/aviator/rounds")
def list_rounds(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    _: None = Depends(require_dashboard_access),
):
    total = db.query(func.count(RoundResult.id)).filter(
        RoundResult.provider == "aviator_capture"
    ).scalar() or 0
    rows = (
        db.query(RoundResult)
        .filter(RoundResult.provider == "aviator_capture")
        .order_by(RoundResult.id.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "items": [
            {
                "id": row.id,
                "round_reference": row.round_id,
                "multiplier": row.multiplier,
                "occurred_at": row.occurred_at.isoformat() if row.occurred_at else None,
                "time_of_day": row.time_of_day,
                "players": row.players,
                "bets": row.bets,
                "prize": row.prize,
                "source": row.source,
                "source_file": row.source_file,
                "verification_status": row.verification_status,
            }
            for row in rows
        ],
    }


@router.get("/api/v1/aviator/summary")
def history_summary(
    db: Session = Depends(get_db),
    _: None = Depends(require_dashboard_access),
):
    query = db.query(RoundResult).filter(RoundResult.provider == "aviator_capture")
    count = query.count()
    if not count:
        return {
            "round_count": 0,
            "mean": None,
            "minimum": None,
            "maximum": None,
            "at_least_2x": 0,
            "at_least_5x": 0,
            "at_least_10x": 0,
            "unverified_count": 0,
            "last_imported_at": None,
        }

    stats = db.query(
        func.avg(RoundResult.multiplier),
        func.min(RoundResult.multiplier),
        func.max(RoundResult.multiplier),
        func.sum((RoundResult.multiplier >= 2).cast if False else 0),
    ).filter(RoundResult.provider == "aviator_capture").first()

    values = [row.multiplier for row in query.order_by(RoundResult.id.asc()).all()]
    return {
        "round_count": count,
        "mean": round(float(stats[0]), 4) if stats[0] is not None else None,
        "minimum": float(stats[1]) if stats[1] is not None else None,
        "maximum": float(stats[2]) if stats[2] is not None else None,
        "median": round(float(__import__("statistics").median(values)), 4),
        "at_least_2x": sum(value >= 2 for value in values),
        "at_least_5x": sum(value >= 5 for value in values),
        "at_least_10x": sum(value >= 10 for value in values),
        "unverified_count": query.filter(RoundResult.verification_status == "unverified").count(),
        "last_imported_at": datetime.now(timezone.utc).isoformat(),
        "disclaimer": "Historical description only; not a forecast or betting signal.",
    }


@router.get("/dashboard", response_class=HTMLResponse)
def dashboard_page():
    return HTMLResponse(DASHBOARD_HTML)


DASHBOARD_HTML = r"""
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>HAMSA AVIATOR AI — Research Dashboard</title>
<style>
:root{color-scheme:dark;--bg:#0b1020;--panel:#141d32;--line:#263653;--text:#e8eefb;--muted:#9aabc7;--accent:#62d5e8}
*{box-sizing:border-box}body{margin:0;background:radial-gradient(circle at 15% 0,#142b49 0,var(--bg) 48%);color:var(--text);font:15px system-ui, sans-serif}
main{max-width:1100px;margin:auto;padding:26px 18px 60px}.top{display:flex;align-items:center;justify-content:space-between;gap:16px;flex-wrap:wrap}
h1{font-size:clamp(24px,4vw,36px);margin:0}.sub,.muted{color:var(--muted)}.panel{background:#141d32eF;border:1px solid var(--line);border-radius:16px;padding:18px;margin-top:18px;box-shadow:0 12px 34px #0003}
.grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px}.stat{background:#0d1729;border:1px solid var(--line);padding:14px;border-radius:12px}.stat b{display:block;font-size:24px;margin-top:5px}
label{display:block;color:var(--muted);font-size:13px;margin-bottom:6px}input,button{font:inherit;border-radius:9px;border:1px solid var(--line);padding:11px;background:#0b1426;color:var(--text);width:100%}
button{background:#176078;border:0;font-weight:650;cursor:pointer}button.secondary{background:#263653}button:disabled{opacity:.55;cursor:wait}
.formgrid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}.actions{display:flex;gap:10px;margin-top:12px;flex-wrap:wrap}.actions button{width:auto;min-width:150px}
.tablewrap{overflow:auto}table{width:100%;border-collapse:collapse;white-space:nowrap}th,td{text-align:left;padding:10px;border-bottom:1px solid var(--line);font-size:13px}th{color:var(--muted);font-weight:600}
canvas{width:100%;height:210px;display:block}.notice{font-size:12px;color:var(--muted);line-height:1.5}.status{min-height:22px;color:var(--accent);margin-top:10px}
@media(max-width:700px){.grid{grid-template-columns:repeat(2,minmax(0,1fr))}.formgrid{grid-template-columns:1fr}.panel{padding:14px}}
</style>
</head>
<body><main>
<header class="top"><div><h1>HAMSA <span style="color:var(--accent)">AVIATOR AI</span></h1><div class="sub">Historical research · Imported rounds · Local analytics</div></div><button id="refresh" class="secondary" style="width:auto">Refresh data</button></header>
<section class="panel">
<h2 style="margin-top:0">Access & data import</h2>
<div class="formgrid">
<div><label for="token">Dashboard access token</label><input id="token" type="password" autocomplete="off" placeholder="Required when configured on server"></div>
<div><label for="source">Data source label</label><input id="source" value="User-provided local capture export"></div>
<div><label for="basis">Authorization basis</label><input id="basis" value="Local export supplied by the account owner"></div>
<div><label for="file">CSV or JSON export (max 1 MB)</label><input id="file" type="file" accept=".csv,.json,text/csv,application/json"></div>
</div>
<div class="actions"><button id="import">Import & save rounds</button><button id="refresh2" class="secondary">Load saved history</button></div>
<div id="status" class="status" role="status" aria-live="polite"></div>
<p class="notice">Imports are stored in the configured HAMSA database. Re-imported rounds are deduplicated. The source and authorization statements are user-provided and are not independently verified. Historical statistics do not predict future rounds.</p>
</section>
<section class="panel"><h2 style="margin-top:0">Historical overview</h2><div class="grid">
<div class="stat"><span class="muted">Saved rounds</span><b id="count">—</b></div>
<div class="stat"><span class="muted">Average multiplier</span><b id="mean">—</b></div>
<div class="stat"><span class="muted">Lowest / highest</span><b id="range">—</b></div>
<div class="stat"><span class="muted">Unverified records</span><b id="unverified">—</b></div>
<div class="stat"><span class="muted">At least 2x</span><b id="two">—</b></div>
<div class="stat"><span class="muted">At least 5x</span><b id="five">—</b></div>
<div class="stat"><span class="muted">At least 10x</span><b id="ten">—</b></div>
<div class="stat"><span class="muted">Median</span><b id="median">—</b></div>
</div></section>
<section class="panel"><h2 style="margin-top:0">Latest multiplier history</h2><canvas id="chart" width="1000" height="240" aria-label="Bar chart of recent multipliers"></canvas><div class="notice">The chart displays the latest saved records only; it is not a prediction curve.</div></section>
<section class="panel"><h2 style="margin-top:0">Saved rounds</h2><div class="tablewrap"><table><thead><tr><th>Round</th><th>Multiplier</th><th>Time</th><th>Players</th><th>Bets</th><th>Prize</th><th>Verification</th></tr></thead><tbody id="rows"><tr><td colspan="7" class="muted">Load history to view records.</td></tr></tbody></table></div><div class="actions"><button id="more" class="secondary">Load next 50</button></div></section>
</main>
<script>
let offset=0;const limit=50;let total=0;let chartValues=[];
const $=id=>document.getElementById(id);
function tokenHeaders(){const t=$('token').value.trim();return t?{'X-Dashboard-Token':t}:{}}
async function api(url,options={}){const response=await fetch(url,{...options,headers:{...tokenHeaders(),...(options.headers||{})}});let data={};try{data=await response.json()}catch{}if(!response.ok)throw new Error(data.detail||('HTTP '+response.status));return data}
function status(message,isError=false){$('status').textContent=message;$('status').style.color=isError?'#ff9c9c':'var(--accent)'}
function put(id,value){$(id).textContent=value}
function drawChart(values){const canvas=$('chart'),ctx=canvas.getContext('2d'),w=canvas.width,h=canvas.height;ctx.clearRect(0,0,w,h);ctx.strokeStyle='#34445f';ctx.fillStyle='#9aabc7';ctx.font='12px system-ui';ctx.beginPath();ctx.moveTo(38,12);ctx.lineTo(38,h-28);ctx.lineTo(w-10,h-28);ctx.stroke();if(!values.length){ctx.fillText('No saved rounds yet',50,45);return}const max=Math.max(2,...values),barW=Math.max(4,(w-65)/values.length-4);values.forEach((v,i)=>{const x=44+i*((w-65)/values.length),bh=(h-55)*(v/max);ctx.fillStyle=v>=10?'#62d5e8':v>=2?'#3988a7':'#62718c';ctx.fillRect(x,h-29-bh,barW,bh)});ctx.fillStyle='#9aabc7';ctx.fillText(max.toFixed(1)+'x',4,18);ctx.fillText('Oldest',44,h-8);ctx.fillText('Latest',w-62,h-8)}
function cell(row,value){const td=document.createElement('td');td.textContent=value==null?'—':String(value);row.appendChild(td)}
async function loadSummary(){const s=await api('/api/v1/aviator/summary');put('count',s.round_count);put('mean',s.mean==null?'—':s.mean+'x');put('range',s.minimum==null?'—':s.minimum+'x / '+s.maximum+'x');put('unverified',s.unverified_count);put('two',s.at_least_2x);put('five',s.at_least_5x);put('ten',s.at_least_10x);put('median',s.median==null?'—':s.median+'x')}
async function loadRounds(reset=false){if(reset){offset=0;$('rows').replaceChildren()}const data=await api('/api/v1/aviator/rounds?limit='+limit+'&offset='+offset);total=data.total;const body=$('rows');if(reset&&!data.items.length){const tr=document.createElement('tr');cell(tr,'No imported rounds yet');body.appendChild(tr)}data.items.forEach(item=>{const tr=document.createElement('tr');cell(tr,item.round_reference);cell(tr,Number(item.multiplier).toFixed(2)+'x');cell(tr,item.time_of_day||item.occurred_at||'—');cell(tr,item.players);cell(tr,item.bets);cell(tr,item.prize);cell(tr,item.verification_status);body.appendChild(tr)});if(reset){chartValues=data.items.slice().reverse().map(x=>Number(x.multiplier));drawChart(chartValues)}offset+=data.items.length;$('more').disabled=offset>=total}
async function refreshAll(){try{status('Loading saved history…');await loadSummary();await loadRounds(true);status('Saved history loaded.')}catch(e){status(e.message,true)}}
$('refresh').onclick=refreshAll;$('refresh2').onclick=refreshAll;$('more').onclick=async()=>{try{await loadRounds(false)}catch(e){status(e.message,true)}};
$('import').onclick=async()=>{const file=$('file').files[0];if(!file){status('Choose a CSV or JSON file first.',true);return}if(file.size>1000000){status('File exceeds the 1 MB limit.',true);return}const button=$('import');button.disabled=true;try{const content=await file.text(),format=file.name.toLowerCase().endsWith('.json')?'json':'csv';const result=await api('/api/v1/data/aviator/import',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({file_name:file.name,format,content,source:$('source').value,authorization_basis:$('basis').value})});status('Import complete: '+result.inserted_count+' saved, '+result.duplicate_count+' duplicates skipped.');await refreshAll()}catch(e){status(e.message,true)}finally{button.disabled=false}};
drawChart([]);refreshAll();
</script></body></html>
"""
