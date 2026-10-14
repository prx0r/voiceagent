/* Answered pricing builder + "Book a call with Tom". Shared by / (home.html) and the console Plans panel.
   Data: GET /api/pricing (knowledge/pricing.json). No dependencies; uses the page's CSS variables. */
(function(){
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const gbp=n=>n<10&&n%1?'£'+n.toFixed(2):'£'+Math.round(n);
let P=null,PICK=new Set(['website']),CALLS=40;
const css=`
.pz{display:flex;flex-direction:column;gap:14px}
.pz .promise{display:flex;flex-wrap:wrap;gap:8px}
.pz .promise span{display:inline-flex;align-items:center;gap:6px;font-size:13px;font-weight:600;border:1px solid rgba(52,211,153,.35);color:#a7f3d0;background:rgba(52,211,153,.08);border-radius:999px;padding:5px 12px}
.pz .box{background:var(--bg2);border:1px solid var(--line2);border-radius:16px;padding:16px 18px}
.pz .box.main{border-color:rgba(245,165,36,.45);background:linear-gradient(180deg,rgba(245,165,36,.07),transparent 70%),var(--bg2)}
.pz .hd{display:flex;align-items:baseline;justify-content:space-between;gap:10px;margin-bottom:6px}
.pz .hd b{font-size:16px;font-weight:600}.pz .hd .pr{font-weight:700;font-size:16px;color:var(--acc);white-space:nowrap}
.pz ul.inc{margin:6px 0 0;padding:0;list-style:none}.pz ul.inc li{padding:4px 0 4px 22px;position:relative;color:var(--dim);font-size:14px}
.pz ul.inc li:before{content:"";position:absolute;left:3px;top:10px;width:9px;height:5px;border-left:2px solid var(--ok);border-bottom:2px solid var(--ok);transform:rotate(-45deg)}
.pz .usage{display:flex;justify-content:space-between;gap:10px;align-items:baseline}
.pz .usage small{color:var(--dim2);font-size:13px;display:block}
.pz .h2{font-size:12px;color:var(--dim2);text-transform:uppercase;letter-spacing:.06em;margin:6px 0 -4px}
.pz .ad{display:flex;gap:12px;align-items:flex-start;padding:12px 14px;border:1px solid var(--line2);border-radius:14px;background:var(--bg2);cursor:pointer;text-align:left;width:100%;color:inherit;font:inherit}
.pz .ad:hover{border-color:rgba(255,255,255,.22)}.pz .ad.on{border-color:var(--acc);background:rgba(245,165,36,.06)}
.pz .ad .tick{width:22px;height:22px;border-radius:7px;border:2px solid var(--line2);flex:0 0 auto;margin-top:1px;display:flex;align-items:center;justify-content:center}
.pz .ad.on .tick{background:var(--acc);border-color:var(--acc)}.pz .ad.on .tick:after{content:"";width:9px;height:5px;border-left:2px solid #111;border-bottom:2px solid #111;transform:rotate(-45deg) translate(1px,-1px)}
.pz .ad .t{flex:1}.pz .ad b{font-weight:600;font-size:14.5px}.pz .ad p{margin:2px 0 0;color:var(--dim);font-size:13px}
.pz .ad .pr{font-weight:600;font-size:13.5px;white-space:nowrap;color:var(--text)}
.pz .ads{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:8px}
.pz.compact .ads{grid-template-columns:1fr}
.pz .est{position:sticky;bottom:0;background:#101010;border:1px solid var(--line2);border-radius:16px;padding:14px 16px;display:flex;flex-wrap:wrap;gap:12px 20px;align-items:center}
.pz .est .n{font-size:22px;font-weight:700;letter-spacing:-.01em}.pz .est small{display:block;color:var(--dim2);font-size:12px}
.pz .est .sp{flex:1}
.pz input[type=range]{width:100%;accent-color:#f5a524}
.pz .draft{color:var(--dim2);font-size:12px}
.tomb{display:inline-flex;align-items:center;gap:8px;border-radius:999px;padding:11px 20px;font-weight:600;font-size:15px;background:#fff;color:#0d0d0d;border:0;cursor:pointer;white-space:nowrap}
.tomb:hover{opacity:.9}
#tomm{position:fixed;inset:0;background:rgba(0,0,0,.6);display:none;align-items:center;justify-content:center;z-index:100;padding:16px}
#tomm.on{display:flex}
#tomm .card{background:#1e1e1e;border:1px solid var(--line2);border-radius:20px;padding:22px;width:min(440px,100%);max-height:90vh;overflow:auto;color:var(--text)}
#tomm h3{margin:0 0 4px;font-size:20px}#tomm p{margin:0 0 14px;color:var(--dim);font-size:14px}
#tomm input{width:100%;background:#2a2a2a;border:1px solid var(--line2);border-radius:12px;padding:12px 14px;margin:0 0 10px;font-size:16px;color:var(--text);outline:none;font-family:inherit}
#tomm .slots{display:grid;grid-template-columns:repeat(2,1fr);gap:6px;margin:4px 0 14px}
#tomm .slots button{border:1px solid var(--line2);border-radius:10px;padding:9px 6px;background:none;color:var(--text);font:inherit;font-size:13.5px;cursor:pointer}
#tomm .slots button.on{border-color:var(--acc);background:rgba(245,165,36,.1)}
#tomm .row{display:flex;gap:8px;justify-content:flex-end;margin-top:4px}
#tomm .x{background:none;border:1px solid var(--line2);color:var(--text);border-radius:999px;padding:10px 16px;cursor:pointer;font:inherit}
#tomm .msg{font-size:14px;margin-top:10px}#tomm .ok{color:#6ee7b7}#tomm .bad{color:#fca5a5}
`;
function inject(){if(document.getElementById('pz-css'))return;const s=document.createElement('style');s.id='pz-css';s.textContent=css;document.head.appendChild(s)}
async function load(){if(P)return P;for(let k=0;k<3&&!P;k++){try{P=await (await fetch('/api/pricing')).json()}catch(e){await new Promise(r=>setTimeout(r,500))}}return P}

function estimate(){
  const mins=CALLS*2,use=mins*P.usage.unit_price;let one=0,yr=0,per=0;
  for(const a of P.addons)if(PICK.has(a.id)){one+=a.one_off||0;yr+=a.yearly||0;
    if(a.per_use)per+=a.per_use*(a.id==='aftercall'?CALLS:15)}
  return {use,one,yr,per};
}
function paintEst(root){
  const e=estimate(),el=root.querySelector('.est');if(!el)return;
  el.innerHTML=`<div><div class="n">${e.one?gbp(e.one):'£0'}</div><small>to get started</small></div>
  <div><div class="n">${e.yr?gbp(e.yr):'£0'}</div><small>a year</small></div>
  <div><div class="n">about ${gbp(e.use+e.per)}</div><small>a month at ${CALLS} missed calls, only if used</small></div>
  <span class="sp"></span><button class="tomb" onclick="Tom.open()">Book a call with Tom</button>`;
}
async function render(root,opt={}){
  inject();root.innerHTML='<div class="draft">Loading prices…</div>';await load();
  if(!P){root.innerHTML='<div class="draft">Prices are loading slowly. Refresh in a moment.</div>';return}
  root.innerHTML=`<div class="pz${opt.compact?' compact':''}">
    <div class="promise">${P.promise.map(x=>`<span>${esc(x)}</span>`).join('')}</div>
    <div class="box main"><div class="hd"><b>1. ${esc(P.pack.name)}</b><span class="pr">${esc(P.pack.price)}</span></div>
      <ul class="inc">${P.pack.includes.map(x=>`<li>${esc(x)}</li>`).join('')}</ul></div>
    <div class="box"><div class="usage"><div><b style="font-size:16px">2. ${esc(P.usage.name)}</b><small>50p ${esc(P.usage.unit)}. Quiet month, small bill. No calls, no bill.</small></div><span class="pr" style="font-weight:700;color:var(--acc);font-size:16px">50p a minute</span></div>
      <div style="margin-top:12px;font-size:13px;color:var(--dim)">Missed calls a month: <b id="pz-c">${CALLS}</b></div><input type="range" min="0" max="150" step="5" value="${CALLS}" id="pz-r"></div>
    <div class="h2">3. Add only what you want</div>
    <div class="ads">${P.addons.map(a=>`<button class="ad${PICK.has(a.id)?' on':''}" data-a="${a.id}"><span class="tick"></span><span class="t"><b>${esc(a.name)}</b><p>${esc(a.what)}</p></span><span class="pr">${esc(a.price)}</span></button>`).join('')}</div>
    <div class="est"></div>
    ${P.addons.some(a=>a.draft)?'<div class="draft">Per-use add-on prices are early prices and may change before launch. You\'ll always see them before you switch anything on.</div>':''}
  </div>`;
  root.querySelectorAll('[data-a]').forEach(b=>b.onclick=()=>{const id=b.dataset.a;PICK.has(id)?PICK.delete(id):PICK.add(id);b.classList.toggle('on');paintEst(root)});
  const r=root.querySelector('#pz-r');r.oninput=()=>{CALLS=+r.value;root.querySelector('#pz-c').textContent=CALLS;paintEst(root)};
  paintEst(root);
}

/* ---- Book a call with Tom ---- */
function slots(){
  const out=[],d=new Date();let n=0;
  while(out.length<6&&n<14){d.setDate(d.getDate()+1);n++;const wd=d.getDay();if(wd===0||wd===6)continue;
    const day=d.toLocaleDateString('en-GB',{weekday:'short',day:'numeric',month:'short'});
    for(const t of ['10:00','14:00','17:30'])if(out.length<6&&(out.length<2||t!=='17:30'))out.push(`${day}, ${t}`);
    if(out.length>=6)break}
  return out;
}
let SLOT='';
async function open(ctx){
  inject();await load();
  const url=P&&P.booking_url;if(url){window.open(url,'_blank','noopener');return}
  let m=document.getElementById('tomm');
  if(!m){m=document.createElement('div');m.id='tomm';m.setAttribute('role','dialog');m.setAttribute('aria-label','Book a call with Tom');document.body.appendChild(m);
    m.addEventListener('click',e=>{if(e.target===m)close()})}
  const s=slots();SLOT=s[0];
  m.innerHTML=`<div class="card"><h3>Book a call with Tom</h3><p>${esc((P&&P.owner&&P.owner.call_minutes)||20)} minutes on the phone. Tom sets everything up with you, tests it and answers any questions. No obligation. Times are UK time.</p>
    <input id="tm-n" placeholder="Your name" autocomplete="name"><input id="tm-p" placeholder="Your mobile" inputmode="tel" autocomplete="tel"><input id="tm-b" placeholder="Your business or trade (optional)">
    <div style="font-size:13px;color:var(--dim2);margin:2px 0 6px">When suits you?</div>
    <div class="slots">${s.map((x,i)=>`<button data-s="${esc(x)}" class="${i?'':'on'}">${esc(x)}</button>`).join('')}<button data-s="Any time, just ring me">Any time</button></div>
    <div class="row"><button class="x" onclick="Tom.close()">Not now</button><button class="tomb" id="tm-go">Book my call</button></div><div class="msg" id="tm-o"></div></div>`;
  m.querySelectorAll('[data-s]').forEach(b=>b.onclick=()=>{SLOT=b.dataset.s;m.querySelectorAll('[data-s]').forEach(x=>x.classList.toggle('on',x===b))});
  m.querySelector('#tm-go').onclick=()=>submit(ctx);
  m.classList.add('on');setTimeout(()=>m.querySelector('#tm-n').focus(),30);
}
function close(){const m=document.getElementById('tomm');if(m)m.classList.remove('on')}
async function submit(ctx){
  const n=document.getElementById('tm-n').value.trim(),p=document.getElementById('tm-p').value.trim(),b=document.getElementById('tm-b').value.trim(),o=document.getElementById('tm-o');
  if(n.length<2||p.replace(/\D/g,'').length<10){o.className='msg bad';o.textContent='Add your name and a mobile number Tom can ring.';return}
  try{const j=await (await fetch('/api/callback',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({business:'answered-trial',name:n,phone:p,
      reason:`Call with Tom: ${SLOT} · ${b||ctx||''} · wants: ${[...PICK].join(',')||'answering only'}`})})).json();
    if(j.ok){o.className='msg ok';o.textContent=`Booked. Tom will ring ${p} ${SLOT.startsWith('Any')?'soon':'on '+SLOT}.`;document.getElementById('tm-go').disabled=true}
    else{o.className='msg bad';o.textContent=j.reason||'Something went wrong. Please try again.'}}
  catch(e){o.className='msg bad';o.textContent="Couldn't reach us. Please try again in a moment."}
}
window.Pricing={render};window.Tom={open,close};
})();
