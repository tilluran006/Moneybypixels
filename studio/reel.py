"""Render a MoneyByPixels reel from the "reel" block of a post's spec.json.

    python3 -m studio.reel posts/<dir>

Motion rules (MOTION.md): one pool of pixels morphs from scene to scene and every
square means something; slow push-in on every hold; words land on the beat;
cuts on bar lines; orange pixel-bar wipes; Night cut for the verdict; loop ending.

Scene types (fields):
  hook     question (ends '?', max 8 words), value, format, caption with [[tension]]
           everything visible at frame 0; number pulses and highlighter swipes in the first 0.5 s
  units    kicker?, headline, value?, format?, n, k, cols?, unit, k_style?
           n squares, k highlighted; '#' in headline = the counted value inline
  fill     headline, counter ('{i}' = squares so far), n, style (main|compare),
           meter? {label, values[n+1]}, big? ('#' = count), after?, final?
  verdict  kicker?, statement ('#' = counted value), value?, cta
Common: bars (length in music bars, 1 bar = 2.86 s at 84 bpm).
Text markup: '|' line break, {{x}} accent colour, [[x]] highlighter.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FONTS = ROOT / "node_modules" / "@fontsource"
FPS = 30

RUPEE = ["########", ".....##.", "########", ".....##.", "######..", ".##.....",
         "..##....", "...##...", "....##..", ".....##.", "......##"]

JS = r"""
const R=REEL, G=RUPEE, BEAT=60/R.bpm, BAR=4*BEAT;
const OR='#BD3F0E',GR='#C2B8AA',BL='#17405F',EM='#F08A3C',INK='#1B1814',SOFT='#5C5249';
const clamp=(x,a=0,b=1)=>Math.max(a,Math.min(b,x)), eo=x=>1-Math.pow(1-clamp(x),3), eio=x=>{x=clamp(x);return x<.5?4*x*x*x:1-Math.pow(-2*x+2,3)/2};
const seg=(t,a,b)=>clamp((t-a)/(b-a));
const fmt=(v,f)=>f==='inr'?'₹'+Math.round(v).toLocaleString('en-IN'):f==='pct'?Math.round(v)+'%':Math.round(v).toLocaleString('en-IN');
const col=s=>s==='compare'?BL:OR;
// timeline
let t0=0; R.scenes.forEach(s=>{s.start=t0;s.dur=s.bars*BAR;t0+=s.dur;}); const LOOP=t0, END=t0+0.4*BAR; window.RD=END;
// ---- markup
function mk(txt,acc){return txt.split('|').map(line=>line.split(' ').map(w=>{
  let h=w.replace(/\{\{(.+?)\}\}/g,(m,a)=>`<span style="color:${acc}">${a}</span>`).replace(/\[\[(.+?)\]\]/g,(m,a)=>`<span class="mark"><i></i><span style="position:relative">${a}</span></span>`);
  return `<span class="w">${h}</span>`;}).join(' ')).join('<br>');}
// accent spans may contain spaces: pre-join {{...}} groups into one token
function prep(txt){return txt.replace(/\{\{(.+?)\}\}/g,m=>m.replace(/ /g,' ')).replace(/\[\[(.+?)\]\]/g,m=>m.replace(/ /g,' '));}
const cam=document.getElementById('cam');
function layer(html,style){const d=document.createElement('div');d.className='L';d.style.cssText=style;d.innerHTML=html;cam.appendChild(d);return d;}
// ---- pixel pool
const rup=[];G.forEach((r,ri)=>[...r].forEach((c,ci)=>{if(c==='#')rup.push([ci,ri]);}));
const N=Math.max(rup.length,...R.scenes.map(s=>s.n||0));
const pool=document.getElementById('pool'),P=[];for(let i=0;i<N;i++){const d=document.createElement('div');d.className='px';pool.appendChild(d);P.push(d);}
function Lrupee(i){const c=40;if(i<rup.length){const[cx,cy]=rup[i];const acc=(cy==0&&cx==7)||(cy==10&&cx==7);return[380+cx*c,470+cy*c,35,acc?EM:OR,1];}return[540,690,0,OR,0];}
const HID=i=>[540,960,0,OR,0];
// ---- build scenes
R.scenes.forEach((s,idx)=>{
  s.layers=[];
  const night=s.t==='verdict'; const acc=night?EM:(s.style==='compare'?BL:OR);
  let y=300;
  if(s.kicker&&s.t!=='hook'){s.layers.push(layer(`<span class="kick" style="color:${night?'#EFE8DB':OR}">${s.kicker}</span>`,`left:90px;top:${night?520:300}px`));y=360;}
  if(s.t==='hook'){
    s.layers.push(layer(s.question,'left:90px;top:290px;width:900px;font-size:62px;line-height:70px;font-family:"Source Serif 4";font-weight:600;color:'+OR));
    s.val=layer('','left:84px;top:930px;transform-origin:0 50%;font-size:210px;line-height:210px;color:'+OR+';letter-spacing:-.02em;font-family:"Source Serif 4";font-weight:600');
    s.val.dataset.always=1;
    s.layers.push(s.capEl=layer(mk(prep(s.caption),OR),'left:90px;top:1160px;width:900px;font-size:64px;line-height:74px;font-family:"Source Serif 4";font-weight:600'));
    s.layout=Lrupee; s.endLayout=Lrupee;
  }
  if(s.t==='units'){
    const lines=s.headline.split('|').length;
    const head=layer(mk(prep(s.headline.replace('#','\u2016')),acc).replace('\u2016','<b class="cnt"></b>'),`left:90px;top:${y}px;width:900px;font-size:70px;line-height:80px;font-family:"Source Serif 4";font-weight:600`);
    s.layers.push(head); y+=lines*80+30;
    if(s.value!==undefined && !s.headline.includes('#')){
      s.val=layer(s.highlight?`<span class="mark"><i class="hl"></i><span class="cnt" style="position:relative"></span></span>`:'<span class="cnt"></span>',
        `left:84px;top:${y}px;font-size:180px;line-height:190px;font-family:"Source Serif 4";font-weight:600;color:${s.highlight?INK:acc}`);
      s.layers.push(s.val); y+=220;
    }
    const cols=s.cols||10, rows=Math.ceil(s.n/cols); y+=30;
    const cell=Math.min(90,Math.floor(900/cols),Math.floor((1440-y)/rows)); const size=Math.round(cell*0.88);
    const x0=Math.round((1080-cols*cell)/2);
    s.layout=i=>i<s.n?[x0+(i%cols)*cell,y+Math.floor(i/cols)*cell,size,i<s.k?col(s.k_style):GR,1]:HID(i);
    s.endLayout=s.layout;
    if(s.unit)s.layers.push(layer(s.unit.replace(/■/g,'<b style="color:'+OR+'">■</b>'),`left:90px;top:${y+rows*cell+24}px;font-size:30px;color:${SOFT}`));
  }
  if(s.t==='fill'){
    s.layers.push(layer(mk(prep(s.headline),acc),`left:90px;top:330px;width:900px;font-size:64px;line-height:74px;font-family:"Source Serif 4";font-weight:600`));
    if(s.counter){s.ctr=layer('',`left:90px;top:420px;font-size:34px;color:${SOFT}`);s.layers.push(s.ctr);}
    const cols=12, rows=Math.ceil(s.n/cols); const top=s.counter?500:440;
    const cell=Math.min(60,Math.floor(((s.final?1400:1450)-top)/Math.max(rows,1))); const size=Math.round(cell*0.86); const x0=Math.round((1080-cols*cell)/2);
    s.grid=(i,shown)=>i<s.n?[x0+(i%cols)*cell,top+Math.floor(i/cols)*cell,size,col(s.style),i<shown?1:0]:HID(i);
    s.layout=i=>s.grid(i,0); s.endLayout=i=>s.grid(i,s.n);
    const gb=top+rows*cell;
    if(s.big){s.bigEl=layer(s.big.replace('#','<span class="cnt"></span>'),`left:84px;top:${gb+80}px;font-size:220px;line-height:220px;font-family:"Source Serif 4";font-weight:600;color:${col(s.style)}`);s.layers.push(s.bigEl);}
    if(s.after)s.layers.push(s.afterEl=layer(s.after,`left:90px;top:${gb+(s.big?330:60)}px;width:900px;font-size:48px;line-height:62px`));
    if(s.final)s.layers.push(s.finalEl=layer(mk(prep(s.final),acc),`left:90px;top:${Math.min(gb+30,1500)}px;width:900px;font-size:50px;line-height:58px;font-family:"Source Serif 4";font-weight:600;background:#F5EFE3`));
  }
  if(s.t==='verdict'){
    s.layers.push(layer(mk(prep(s.statement.replace('#','\u2016')),EM).replace('\u2016','<b class="cnt"></b>'),`left:90px;top:600px;width:900px;font-size:104px;line-height:112px;font-family:"Source Serif 4";font-weight:600;color:#EFE8DB`));
    if(s.cta)s.layers.push(s.ctaEl=layer(s.cta,`left:90px;top:1080px;width:900px;font-size:46px;line-height:60px;color:#EFE8DB`));
    s.layout=HID; s.endLayout=HID;
  }
});
function place(L){for(let i=0;i<N;i++){const[x,y,s,c,v]=L(i);const d=P[i];const z=Math.max(0,s*v);
  d.style.transform=`translate(${x+(s-z)/2}px,${y+(s-z)/2}px)`;d.style.width=z+'px';d.style.height=z+'px';d.style.background=c;}}
function morph(A,B,p,st=0.35){return i=>{const q=eio(clamp(p*(1+st)-st*(i/N)));const a=A(i),b=B(i);
  return[a[0]+(b[0]-a[0])*q,a[1]+(b[1]-a[1])*q,a[2]+(b[2]-a[2])*q,q<.5?a[3]:b[3],a[4]+(b[4]-a[4])*q];}}
function words(el,t,a){el.querySelectorAll('.w').forEach((w,k)=>{const p=eo(seg(t,a+0.05+k*BEAT/4,a+0.35+k*BEAT/4));w.style.opacity=p;w.style.transform=`translateY(${(1-p)*18}px)`;});}
function render(t){
  let si=R.scenes.findIndex(s=>t>=s.start&&t<s.start+s.dur); const inLoop=t>=LOOP; if(inLoop)si=-1;
  const s=si>=0?R.scenes[si]:null;
  const ss=s?s.start:LOOP, sd=s?s.dur:END-LOOP;
  cam.style.transform=`scale(${1+0.035*seg(t,ss,ss+sd)})`;
  const night=!!(s&&s.t==='verdict');
  document.getElementById('night').style.opacity=night?1:0;
  document.getElementById('hdr').style.opacity=night?0:1;
  document.getElementById('foot').style.opacity=(s&&s.t!=='hook'&&!night)?1:0;
  // wipe at each cut
  let w='';for(const c of [...R.scenes.slice(1).map(x=>x.start),LOOP]){const p=seg(t,c-0.18,c+0.22);if(p>0&&p<1){const x=-160+1400*eo(p);
    w=`<div style="position:absolute;left:${x}px;top:0;width:48px;height:1920px;background:${OR}"></div><div style="position:absolute;left:${x-36}px;top:0;width:20px;height:1920px;background:${EM}"></div>`;}}
  document.getElementById('wipe').innerHTML=w;
  // layers visibility
  R.scenes.forEach((x,k)=>{x.layers.forEach(el=>{el.style.opacity=(x.t==='hook'&&(k===si||inLoop))?(inLoop?seg(t,LOOP+0.1,LOOP+0.35):1-seg(t,x.start+x.dur-0.15,x.start+x.dur)):k===si?Math.min(seg(t,x.start+0.1,x.start+0.35),1-seg(t,x.start+x.dur-0.15,x.start+x.dur)):0;});
    if(x.val&&x.t==='hook')x.val.style.opacity=(k===si||inLoop)?1:0;});
  if(inLoop){const h=R.scenes[0];h.val.textContent=fmt(h.value,h.format);h.layers.forEach(el=>el.querySelectorAll('.w').forEach(w=>{w.style.opacity=1;w.style.transform='none';}));h.val.style.transform='none';
    place(i=>{const r=Lrupee(i);return[r[0],r[1],r[2],r[3],r[4]*eo(seg(t,LOOP+0.25+i*0.012,LOOP+0.5+i*0.012))];});return;}
  // pixels
  const prev=si>0?R.scenes[si-1]:null; const mp=seg(t,s.start-0.05,s.start+0.7);
  let L;
  if(s.t==='hook')L=Lrupee;
  else if(s.t==='units')L=prev?morph(prev.endLayout,s.layout,mp):s.layout;
  else if(s.t==='fill'){const fe=s.n>40?Math.min(3.6,s.dur-1.6):0.9; const shown=Math.floor(s.n*seg(t,s.start+0.8,s.start+0.8+fe));
    s.shownNow=shown; L=t<s.start+0.7&&prev?morph(prev.endLayout,s.layout,mp):(i=>s.grid(i,shown));
    if(s.ctr)s.ctr.innerHTML=s.counter.replace('{i}',`<b style="color:${INK}">${shown}</b>`);
    const meter=document.getElementById('meter'); if(s.meter){meter.style.opacity=1;const v=s.meter.values[Math.min(shown,s.meter.values.length-1)];
      document.getElementById('meterl').textContent=s.meter.label;document.getElementById('meterv').textContent=fmt(v,'inr');
      document.getElementById('meterbar').style.width=(100*v/s.meter.values[0])+'%';document.getElementById('meterbar').style.background=col(s.style);}
    const cnt=s.bigEl&&s.bigEl.querySelector('.cnt'); if(cnt)cnt.textContent=shown;
    if(s.finalEl)s.finalEl.style.opacity=Math.min(seg(t,s.start+0.8+fe+0.2,s.start+0.8+fe+0.5),1-seg(t,s.start+s.dur-0.15,s.start+s.dur));
    if(s.afterEl)s.afterEl.style.opacity=Math.min(seg(t,s.start+0.8+fe+0.3,s.start+0.8+fe+0.6),1-seg(t,s.start+s.dur-0.15,s.start+s.dur));
  }
  else L=prev?i=>{const a=prev.endLayout(i);return[a[0],a[1],a[2],a[3],a[4]*(1-eo(seg(t,s.start-0.05,s.start+0.25)))];}:HID;
  if(!(s.t==='fill'&&s.meter))document.getElementById('meter').style.opacity=0;
  place(L);
  // text animation + counters
  if(s.t==='hook')s.layers.forEach(el=>el.querySelectorAll('.w').forEach(w=>{w.style.opacity=1;w.style.transform='none';}));
  else s.layers.forEach(el=>words(el,t,s.start+0.15));
  const cv=seg(t,s.start+0.9,s.start+1.9);
  if(s.t==='hook'){s.val.textContent=fmt(s.value,s.format);
    s.val.style.transform=`scale(${1.08-0.08*eo(seg(t,0,0.4))})`;
    s.capEl.querySelectorAll('.mark i').forEach(i=>{const p=eo(seg(t,0.1,0.5));i.style.width=`calc(${p*100}% + ${p*20}px)`;});}
  if(s.value!==undefined&&s.t!=='hook')cam.querySelectorAll('.cnt').forEach(c=>{if(s.layers.some(l=>l.contains(c)))c.textContent=fmt(s.value*eo(cv),s.format||'int');});
  if(s.highlight&&s.val){const hl=s.val.querySelector('.hl');if(hl)hl.style.width=(s.val.querySelector('.cnt').offsetWidth+20)*eo(seg(t,s.start+2.0,s.start+2.4))+'px';}
}
render(0);
"""

HTML = r"""<!doctype html><meta charset="utf-8">
<link rel="stylesheet" href="FONTS/source-serif-4/600.css">
<link rel="stylesheet" href="FONTS/source-sans-3/400.css">
<link rel="stylesheet" href="FONTS/source-sans-3/600.css">
<style>
html,body{margin:0}*{box-sizing:border-box}
#s{position:relative;width:1080px;height:1920px;overflow:hidden;background:#F5EFE3;color:#1B1814;font-family:'Source Sans 3',sans-serif}
#night{position:absolute;inset:0;background:#14110E;opacity:0}
#cam{position:absolute;inset:0;transform-origin:50% 45%}
.kick{font-size:34px;font-weight:600;letter-spacing:.05em;text-transform:uppercase}
.L{position:absolute;opacity:0}.w{display:inline-block;opacity:0}.px{position:absolute;left:0;top:0}
.mark{position:relative;display:inline-block;isolation:isolate}
.mark i{position:absolute;left:-10px;top:14%;height:78%;background:#F6DCC2;z-index:-1;width:0}
.mark i:not(.hl){width:calc(100% + 20px)}
</style>
<div id="s"><div id="night"></div>
 <div id="cam">
  <div style="position:absolute;left:90px;top:170px;display:flex;align-items:center;gap:14px" id="hdr">
   <div style="width:22px;height:22px;background:#BD3F0E"></div><span style="font-size:34px;font-weight:600">MoneyByPixels</span></div>
  <div id="meter" style="position:absolute;left:90px;top:250px;width:900px;opacity:0">
   <div style="display:flex;justify-content:space-between;font-size:30px;color:#5C5249"><span id="meterl"></span><span id="meterv" style="color:#1B1814;font-weight:600"></span></div>
   <div style="margin-top:10px;height:14px;background:#D9D0C1"><div id="meterbar" style="height:14px;width:100%"></div></div></div>
  <div id="pool"></div>
 </div>
 <div id="wipe" style="position:absolute;left:0;top:0;width:1080px;height:1920px"></div>
 <div id="foot" style="position:absolute;left:90px;top:1590px;width:900px;font-size:26px;line-height:34px;color:#5C5249">FOOTER</div>
</div>
<script>JS</script>"""


def music(path: Path, dur: float, bpm: float, cues: dict) -> None:
    """Original lo-fi bed (Am7-Fmaj7-C-G) with motion-synced cues. No licensing issues."""
    import numpy as np
    import wave
    SR = 44100
    N = int(SR * dur)
    BEAT = 60 / bpm
    BAR = 4 * BEAT
    mix = np.zeros(N)
    rng = np.random.default_rng(7)

    def note(f, start, length, amp, decay):
        s = int(start * SR); n = min(int(length * SR), N - s)
        if n <= 0: return
        tt = np.arange(n) / SR
        env = (1 - np.exp(-tt * 40)) * np.exp(-tt * decay)
        mix[s:s + n] += amp * env * (np.sin(2 * np.pi * f * tt) + .35 * np.sin(4 * np.pi * f * tt) + .12 * np.sin(6 * np.pi * f * tt))

    hz = lambda m: 440 * 2 ** ((m - 69) / 12)
    chords = [[57, 60, 64, 67], [53, 57, 60, 64], [48, 55, 60, 64], [55, 59, 62, 67]]
    st, k = 0.0, 0
    while st < dur:
        ch = chords[k % 4]
        for i, m in enumerate(ch): note(hz(m), st + .02 * i, BAR, .05, .9)
        note(hz(ch[0] - 12), st, BAR, .07, .8)
        for b in range(4): note(hz(ch[(b + 1) % 4] + 12), st + b * BEAT + BEAT / 2, BEAT, .035, 4)
        st += BAR; k += 1

    def kick(s):
        i = int(s * SR); n = min(int(.25 * SR), N - i); tt = np.arange(n) / SR
        f = 60 + 60 * np.exp(-tt * 30); mix[i:i + n] += .22 * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 14)

    def hat(s):
        i = int(s * SR); n = min(int(.06 * SR), N - i); tt = np.arange(n) / SR
        nz = np.diff(np.concatenate([[0], rng.standard_normal(n)])); mix[i:i + n] += .02 * nz * np.exp(-tt * 60)

    x = 0.0
    while x < dur - .3:
        if x >= BAR: kick(x)
        hat(x + BEAT / 2); x += BEAT
    fade = np.ones(N); fi, fo = int(.4 * SR), int(.8 * SR)
    fade[:fi] = np.linspace(.4, 1, fi); fade[-fo:] = np.linspace(1, .4, fo)
    sfx = np.zeros(N)

    def tick(s, a=.07):
        i = int(s * SR); n = min(int(.02 * SR), N - i); tt = np.arange(n) / SR
        sfx[i:i + n] += a * np.sin(2 * np.pi * 2400 * tt) * np.exp(-tt * 300)

    def pop(s, a=.025, f=900):
        i = int(s * SR); n = min(int(.04 * SR), N - i); tt = np.arange(n) / SR
        sfx[i:i + n] += a * np.sin(2 * np.pi * f * tt) * np.exp(-tt * 120)

    def whoosh(s, a=.09, L=.42):
        i = max(0, int(s * SR)); n = min(int(L * SR), N - i); tt = np.arange(n) / SR
        nz = np.convolve(rng.standard_normal(n), np.ones(25) / 25, 'same') * 5
        sfx[i:i + n] += a * nz * np.sin(np.pi * tt / L) ** 2

    def thud(s, a=.35):
        i = int(s * SR); n = min(int(.3 * SR), N - i); tt = np.arange(n) / SR
        sfx[i:i + n] += a * np.sin(2 * np.pi * (90 * tt - 40 * tt ** 2)) * np.exp(-tt * 18)

    for c in cues["wipes"]: whoosh(c - .2)
    for a, b, n in cues["ticks"]:
        for j in range(n): tick(a + (b - a) * (1 - (1 - j / n) ** 2))
    for a, b, n in cues["pops"]:
        for j in range(n): pop(a + (b - a) * j / max(n, 1), .025, 700 + 30 * (j % 8))
    for c in cues["thuds"]: thud(c)
    out = mix * fade + sfx
    out = out / np.max(np.abs(out)) * .8
    wv = wave.open(str(path), 'wb'); wv.setnchannels(1); wv.setsampwidth(2); wv.setframerate(SR)
    wv.writeframes((out * 32767).astype(np.int16).tobytes()); wv.close()


def cues_for(reel: dict) -> tuple[float, dict]:
    bpm = reel.get("bpm", 84); BAR = 4 * 60 / bpm
    t, wipes, ticks, pops, thuds = 0.0, [], [], [], []
    for k, s in enumerate(reel["scenes"]):
        if k: wipes.append(t)
        if s["t"] == "hook": ticks.append((0.25, 1.5, 14))
        elif s.get("value") is not None: ticks.append((t + .9, t + 1.9, 10))
        if s["t"] == "fill":
            fe = min(3.6, s["bars"] * BAR - 1.6) if s["n"] > 40 else 0.9
            pops.append((t + .8, t + .8 + fe, min(s["n"], 60)))
        if s["t"] == "verdict": thuds.append(t)
        t += s["bars"] * BAR
    wipes.append(t)
    return t + 0.4 * BAR, {"wipes": wipes, "ticks": ticks, "pops": pops, "thuds": thuds}


def check(reel: dict) -> list[str]:
    errs = []
    sc = reel.get("scenes", [])
    if not sc or sc[0]["t"] != "hook": errs.append("first scene must be a hook")
    if sc and sc[0]["t"] == "hook":
        h = sc[0]
        if not h.get("question", "").strip().endswith("?"): errs.append("hook needs a 'question' that speaks to the viewer and ends with '?'")
        if "[[" not in h.get("caption", ""): errs.append("hook caption must highlight the tension with [[...]]")
        if len(h.get("question", "").split()) > 8: errs.append("hook question max 8 words")
    if len(sc) > 5: errs.append(f"{len(sc)} scenes (max 5: hook, 2-3 middle, verdict)")
    if sc and sc[-1]["t"] != "verdict": errs.append("last scene must be a verdict")
    total = (sum(s["bars"] for s in sc) + 0.4) * 4 * 60 / reel.get("bpm", 84)
    if not 14 <= total <= 22: errs.append(f"reel length {total:.1f}s (want 15-20s, max 22s)")
    for i, s in enumerate(sc, 1):
        if s.get("n", 0) > 240: errs.append(f"scene {i}: max 240 squares")
        if s["t"] == "units" and s.get("k", 0) > s.get("n", 0): errs.append(f"scene {i}: k > n")
        if s["t"] == "fill" and len(s.get("headline", "")) > 28: errs.append(f"scene {i}: fill headline max 28 characters (one line)")
        if s["t"] == "fill" and s.get("meter") and len(s["meter"]["values"]) < s["n"] + 1: errs.append(f"scene {i}: meter needs n+1 values")
    return errs


def render(post_dir: str) -> Path:
    d = Path(post_dir).resolve()
    spec = json.loads((d / "spec.json").read_text())
    reel = spec["reel"]
    errs = check(reel)
    if errs: raise SystemExit("Reel check failed:\n- " + "\n- ".join(errs))
    out = d / "reel"; out.mkdir(exist_ok=True)
    frames = out / "frames"
    if frames.exists(): shutil.rmtree(frames)
    frames.mkdir()
    footer = reel.get("footer") or " ".join(spec["footer"])
    html = (HTML.replace("FONTS", FONTS.as_uri()).replace("FOOTER", footer)
            .replace("JS", JS.replace("REEL", json.dumps(reel, ensure_ascii=False)).replace("RUPEE", json.dumps(RUPEE))))
    page = out / "scene.html"; page.write_text(html)
    dur, cues = cues_for(reel)
    from playwright.sync_api import sync_playwright
    chrome = shutil.which("google-chrome") or shutil.which("chromium")
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=chrome) if chrome else p.chromium.launch()
        pg = b.new_page(viewport={"width": 1080, "height": 1920})
        pg.goto(page.as_uri()); pg.wait_for_timeout(800)
        for i in range(int(FPS * dur)):
            pg.evaluate(f"render({i / FPS})")
            pg.screenshot(path=str(frames / f"{i:04d}.png"))
        b.close()
    wav = out / "audio.wav"
    music(wav, dur, reel.get("bpm", 84), cues)
    mp4 = out / f"{spec['slug']}_reel.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", str(frames / "%04d.png"), "-i", str(wav),
                    "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k",
                    "-shortest", "-movflags", "+faststart", str(mp4)], check=True)
    # contact sheet of key frames
    from PIL import Image
    pick = sorted(frames.glob("*.png"))
    step = max(1, len(pick) // 10)
    thumbs = [Image.open(f).resize((216, 384)) for f in pick[::step][:10]]
    sheet = Image.new("RGB", (5 * 226 + 10, 2 * 394 + 10), "white")
    for k, im in enumerate(thumbs): sheet.paste(im, (10 + (k % 5) * 226, 10 + (k // 5) * 394))
    sheet.save(out / "reel_contact_sheet.png")
    shutil.rmtree(frames); wav.unlink(); page.unlink()
    cap = reel.get("caption", spec["caption"])
    tags = " ".join("#" + t for t in spec.get("hashtags", []))
    (out / "caption_reel.md").write_text(f"# Reel: {spec['title']}\n\nPost on Monday **as a Trial Reel** first (shown to non-followers only). After 24-48 hours check the skip rate: if it beats the page's last reel, share it to your profile; if not, leave it as a trial and note what the hook was. The file already has its own music.\n\n```\n{cap.strip()}\n\n{tags}\n```\n")
    return mp4


if __name__ == "__main__":
    for p in sys.argv[1:]:
        print(render(p))
