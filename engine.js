/* =========================================================================
   LE DÉ DE LA VIE — moteur data-driven
   Aucune donnée pays n'est écrite ici. Tout vient de DATA, chargé depuis
   /data/*.json (si l'app est servie) ou du seed embarqué window.__SEED__
   (fallback pour l'aperçu en fichier local). Ajouter un pays = ajouter des
   lignes de données, jamais toucher ce code.
   ========================================================================= */

const WORLD_POP = 8_000_000_000;
let DATA = null, CTY = {};

/* ---- métadonnées de dimensions (UI, pas de la donnée pays) ---- */
const AGES = ["a00_04","a05_14","a15_19","a20_34","a35_49","a50_64","a65_79","a80p"];
const AGE_MID = {a00_04:2,a05_14:10,a15_19:17,a20_34:27,a35_49:42,a50_64:57,a65_79:72,a80p:86};
const SCENE = {pays:"--c-pays",agesexe:"--c-agesexe",milieu:"--c-milieu",revenu:"--c-revenu",education:"--c-education",sante:"--c-sante",famille:"--c-famille",detail:"--c-detail"};

const ICONS={
  pays:`<svg class="ico" viewBox="0 0 120 120"><circle cx="60" cy="60" r="42"/><ellipse cx="60" cy="60" rx="18" ry="42"/><path d="M20 50 H100"/><path d="M18 72 H102"/><path d="M40 30 q20 10 40 0"/></svg>`,
  agesexe:`<svg class="ico" viewBox="0 0 120 120"><circle cx="60" cy="38" r="17"/><path d="M32 96 q0-30 28-30 q28 0 28 30"/><path d="M60 12 v8"/></svg>`,
  milieu:`<svg class="ico" viewBox="0 0 120 120"><path d="M22 60 L48 38 L74 60"/><path d="M28 58 V94 H68 V58"/><rect x="42" y="74" width="14" height="20"/><path d="M78 94 V52 H98 V94"/><path d="M84 60 h8 M84 72 h8"/></svg>`,
  revenu:`<svg class="ico" viewBox="0 0 120 120"><ellipse cx="60" cy="40" rx="30" ry="12"/><path d="M30 40 V74 q0 12 30 12 q30 0 30-12 V40"/><path d="M30 57 q0 12 30 12 q30 0 30-12"/></svg>`,
  education:`<svg class="ico" viewBox="0 0 120 120"><path d="M60 40 q-22-12-40-6 V90 q20-6 40 6 q20-12 40-6 V34 q-18-6-40 6 Z"/><path d="M60 40 V92"/></svg>`,
  sante:`<svg class="ico" viewBox="0 0 120 120"><path d="M60 92 C22 66 26 34 46 34 q14 0 14 16 q0-16 14-16 c20 0 24 32 -14 58 Z"/><path d="M30 60 H46 L52 48 L60 74 L66 60 H92" stroke-width="4"/></svg>`,
  famille:`<svg class="ico" viewBox="0 0 120 120"><circle cx="40" cy="42" r="13"/><path d="M20 92 q0-24 20-24 q20 0 20 24"/><circle cx="80" cy="42" r="13"/><path d="M60 92 q0-24 20-24 q20 0 20 24"/><circle cx="60" cy="66" r="8"/><path d="M48 96 q0-14 12-14 q12 0 12 14"/></svg>`,
  detail:`<svg class="ico" viewBox="0 0 120 120"><circle cx="60" cy="50" r="22"/><path d="M50 74 H70 M53 82 H67"/><path d="M60 20 V12 M86 50 H94 M26 50 H34 M80 30 l6-6 M40 30 l-6-6"/></svg>`
};
const AVATAR=`<svg class="ico avatar" viewBox="0 0 120 120"><circle cx="60" cy="42" r="26"/><circle cx="51" cy="42" r="3.5" class="fill"/><circle cx="69" cy="42" r="3.5" class="fill"/><path d="M50 52 q10 8 20 0"/><path d="M30 110 q0-40 30-40 q30 0 30 40"/></svg>`;

/* ---- helpers ---- */
const $=s=>document.querySelector(s);
const clamp=(x,a,b)=>Math.max(a,Math.min(b,x));
const fmt=n=>Math.round(n).toLocaleString("fr-FR").replace(/\u202f/g," ");
const norm=o=>{const t=Object.values(o).reduce((a,b)=>a+b,0)||1;const r={};for(const k in o)r[k]=o[k]/t;return r;};
function pick(d){const n=norm(d);let r=Math.random(),a=0;for(const k in n){a+=n[k];if(r<=a)return k;}return Object.keys(n).pop();}
const REDUCED=matchMedia("(prefers-reduced-motion:reduce)").matches;
const wait=ms=>new Promise(r=>setTimeout(r,REDUCED?Math.min(ms,100):ms));
const ageIdx=id=>AGES.indexOf(id);

/* ================= STRATES (logique universelle, chiffres depuis DATA) ================= */
const STRATA=[
 {id:"pays",label:"le pays",source_ref:()=>DATA.countries.source_id,
  distribution:()=>{const d={};DATA.countries.rows.forEach(r=>d[r.iso3]=r.population);return d;},
  reveal:o=>({word:CTY[o].name_fr,cap:"direction "+CTY[o].name_fr+" !",chip:["pays",CTY[o].name_fr]}),
  apply:(o,st)=>{st.country=o;}},

 {id:"agesexe",label:"l'âge & le sexe",source_ref:()=>DATA.age_sex.source_id,
  distribution:st=>({...DATA.age_sex.data[st.country].shares}),
  reveal:o=>{const[a,s]=o.split("|"),i=ageIdx(a),yr=AGE_MID[a],child=i<=1;
    const word=child?(s==="F"?"Une fille":"Un garçon"):(s==="F"?"Une femme":"Un homme");
    return{word,cap:yr+" ans, on démarre",chip:["âge",(s==="F"?"F":"H")+", "+yr+" ans"]};},
  apply:(o,st)=>{const[a,s]=o.split("|");st.ageId=a;st.ageIdx=ageIdx(a);st.age=AGE_MID[a];st.sex=s;}},

 {id:"milieu",label:"le décor",source_ref:()=>DATA.settlement.source_id,
  distribution:st=>({...DATA.settlement.data[st.country].shares}),
  reveal:o=>{const w={grande:"La grande ville",ville:"Une ville",rural:"La campagne"}[o];
    const c={grande:"lumières et béton",ville:"peinard, taille moyenne",rural:"grand air, loin du bruit"}[o];
    return{word:w,cap:c,chip:["décor",{grande:"Grande ville",ville:"Ville",rural:"Campagne"}[o]]};},
  apply:(o,st)=>{st.rural=o==="rural";st.milieu=o;}},

 {id:"revenu",label:"le portefeuille",source_ref:()=>DATA.income.source_id,
  distribution:()=>({q1:.2,q2:.2,q3:.2,q4:.2,q5:.2}),
  reveal:(o,st)=>{const qi=["q1","q2","q3","q4","q5"].indexOf(o);
    const lbl=["Serré","Modeste","Au milieu","Confortable","Peinard"][qi];
    const top=100-DATA.income.data[st.country].global_percentile[qi];
    return{word:lbl,cap:"soit le top "+top+" % mondial, à peu près",chip:["argent",lbl]};},
  apply:(o,st)=>{st.qi=["q1","q2","q3","q4","q5"].indexOf(o);}},

 {id:"education",label:"les études",source_ref:()=>DATA.education.source_id,
  distribution:st=>{const E=DATA.education;
    if(st.ageIdx<=0)return{petite:1};
    if(st.ageIdx===1){const p=E.child_enrollment[st.country].in_school;return{ecole:p,hors:1-p};}
    let w={...E.attainment_base[st.country].shares};const f=E.factors;
    if(st.rural){for(const k in w)w[k]*=f.rural_penalty[k];}
    w.superieur*=f.income_prime.superieur[st.qi];
    w.aucune*=f.income_prime.aucune[st.qi];
    w.secondaire*=f.income_prime.secondaire[st.qi];
    const gg=f.gender_gap[st.country];
    if(gg&&st.sex==="F"){w.aucune*=gg.aucune;w.superieur*=gg.superieur;w.secondaire*=gg.secondaire;}
    return w;},
  reveal:o=>{const m={petite:"Trop petit pour l'école",ecole:"À l'école",hors:"Pas scolarisé",
    aucune:"Pas allé à l'école",primaire:"Niveau primaire",secondaire:"Niveau lycée",superieur:"Études supérieures"};
    const c={superieur:"diplôme dans la poche",secondaire:"bac en vue",ecole:"cartable sur le dos"}[o]||"";
    const p={petite:"Petite enfance",ecole:"Scolarisé",hors:"Non scolarisé",aucune:"Sans école",primaire:"Primaire",secondaire:"Lycée",superieur:"Supérieur"};
    return{word:m[o],cap:c,chip:["études",p[o]]};},
  apply:(o,st)=>{st.edu=o;}},

 {id:"sante",label:"la santé",source_ref:()=>DATA.health.source_id,
  distribution:st=>{const H=DATA.health;let w={...H.severity_base_group[H.country_group[st.country]]};
    const i=st.ageIdx,ab=H.age_factors.boost[i],ga=H.age_factors.good[i],li=H.income_penalty[st.qi];
    w.bonne*=ga;w.incap_moderee*=ab*li;w.incap_severe*=ab*li;w.gene_legere*=(0.9+0.05*i);return w;},
  reveal:(o,st)=>{const H=DATA.health,m=H.mental;
    const mp=clamp(m.base+(st.rural?m.rural_add:0)+(st.qi<=1?m.lowinc_add:0),m.min,m.max);st.mental=Math.random()<mp;
    const map={bonne:"En pleine forme",gene_legere:"Une gêne légère",incap_moderee:"Une incapacité modérée",incap_severe:"Une incapacité sévère"};
    return{word:map[o],cap:o==="bonne"?"la grande forme":"",chip:["santé",map[o]]};},
  apply:(o,st)=>{st.health=o;}},

 {id:"famille",label:"la tribu",source_ref:()=>DATA.family.source_id,
  distribution:st=>{const F=DATA.family,P=F.params,early=F.early_parenthood.includes(st.country);
    if(st.ageIdx<=1)return{enfant:1};
    if(st.ageIdx===2)return early?{...P.young_early}:{...P.young_late};
    if(st.ageIdx>=6){const vf=P.elder_widow[st.sex];return{veuf:vf,couple:1-vf-0.08,celibataire:0.08};}
    let cel=P.mid_celibataire[st.ageId]||0.2,par=P.mid_parent[st.ageId]||0.4;
    if(early){cel*=P.early_cel_mult;par*=P.early_par_mult;}
    let cou=1-cel-par;if(cou<0.05)cou=0.05;
    return{celibataire:cel,couple:cou,parent:par};},
  reveal:(o,st)=>{const m={enfant:"Chez ses parents",celibataire:"Célibataire",couple:"En couple",parent:"Déjà parent",veuf:st.sex==="F"?"Veuve":"Veuf"};
    return{word:m[o],cap:"",chip:["tribu",m[o]]};},
  apply:(o,st)=>{st.family=o;}},

 {id:"detail",label:"le bonus",source_ref:()=>DATA.living.source_id,
  distribution:()=>({a:1}),
  reveal:(o,st)=>{const L=DATA.living,d=L.data[st.country],rp=st.rural?L.rural_penalty:1;
    const fs=[{h:Math.random()<clamp(d.electricite*rp,0,1),y:"L'électricité à la maison",n:"Pas d'électricité fiable"},
             {h:Math.random()<clamp(d.internet*rp,0,1),y:"Connecté à internet",n:"Pas d'internet"},
             {h:Math.random()<clamp(d.eau*rp,0,1),y:"L'eau potable au robinet",n:"Pas d'eau potable sûre"}];
    const miss=fs.find(f=>!f.h),f=miss||fs[0];const txt=f.h?f.y:f.n;
    return{word:txt,cap:"",chip:["bonus",txt]};},
  apply:()=>{}}
];

/* labels de source lisibles (depuis le manifeste embarqué) */
const SRC_LABEL={wpp:"ONU · WPP 2024",wup:"ONU · WUP 2025",pip:"Banque mondiale · PIP",
  barrolee:"Barro-Lee · UNESCO",gbd:"IHME · GBD 2023",undesa_marriage:"ONU DESA · Marriage Data",wdi:"Banque mondiale · WDI"};

/* ================= état & flux (clic par étape) ================= */
let state,remaining,soul=0,i=0,curDist=null,curOutcome=null,rolled=false,distLog={};
function resetState(){state={};remaining=WORLD_POP;i=0;distLog={};$("#chips").innerHTML="";$("#countN").textContent=fmt(WORLD_POP);}

function startPlay(){
  const eb=$("#earthBtn");eb.style.transition="transform .6s cubic-bezier(.5,0,.3,1),opacity .6s";
  eb.style.transform="scale(2.6) rotate(20deg)";eb.style.opacity="0";
  setTimeout(()=>{resetState();show("s-play");renderStep();},REDUCED?100:520);
}
function renderStep(){
  const s=STRATA[i];rolled=false;curOutcome=null;
  document.getElementById("stage").style.background="var("+SCENE[s.id]+")";
  $("#stepTag").textContent="étape "+(i+1)+" · "+s.label;
  $("#ico").outerHTML=ICONS[s.id].replace('class="ico"','class="ico" id="ico"');
  $("#result").textContent="";$("#result").className="result";
  $("#caption").textContent="";$("#caption").className="caption";
  $("#srcBtn").style.display="none";$("#nextBtn").classList.remove("show");
  $("#dieWrap").style.display="flex";$("#dieHint").textContent="clique le dé pour tirer";$("#dieHint").style.visibility="visible";
  buildDie(Math.ceil(Math.random()*6));
}
function buildDie(face){const L={1:[4],2:[0,8],3:[0,4,8],4:[0,2,6,8],5:[0,2,4,6,8],6:[0,2,3,5,6,8]};
  const on=new Set(L[face]);let h="";for(let k=0;k<9;k++)h+='<div class="pip'+(on.has(k)?" on":"")+'"></div>';$("#die").innerHTML=h;}

async function rollDie(){
  if(rolled)return;rolled=true;const s=STRATA[i];
  curDist=s.distribution(state);distLog[s.id]={dist:curDist,source:SRC_LABEL[s.source_ref()]||s.source_ref(),label:s.label};
  curOutcome=pick(curDist);const share=norm(curDist)[curOutcome];
  const die=$("#die");$("#dieHint").style.visibility="hidden";
  const spins=REDUCED?1:6;
  for(let c=0;c<spins;c++){die.classList.remove("rolling");void die.offsetWidth;die.classList.add("rolling");buildDie(Math.ceil(Math.random()*6));await wait(90);}
  die.classList.remove("rolling");
  const r=s.reveal(curOutcome,state);s.apply(curOutcome,state);
  distLog[s.id].chip=r.chip;distLog[s.id].picked=curOutcome;
  const prev=remaining;remaining=(s.id==="pays")?CTY[curOutcome].population:remaining*share;
  animateCount(prev,Math.max(remaining,1));
  $("#dieWrap").style.display="none";
  const res=$("#result");res.textContent=r.word;res.classList.add("pop");
  const cap=$("#caption");cap.textContent=r.cap||"";if(r.cap)requestAnimationFrame(()=>cap.classList.add("in"));
  const sb=$("#srcBtn");sb.style.display="inline";sb.onclick=()=>openDist(s.id,curOutcome);
  addChip(s.id,r.chip);
  await wait(REDUCED?80:280);$("#nextBtn").classList.add("show");
}
function nextStep(){i++;if(i>=STRATA.length){toFinal();return;}renderStep();}
function animateCount(from,to){const el=$("#countN"),dur=REDUCED?150:820,t0=performance.now();
  (function step(t){const p=clamp((t-t0)/dur,0,1),e=1-Math.pow(1-p,3),v=from+(to-from)*e;
    el.textContent=v<1000?Math.max(1,Math.round(v)):fmt(v);if(p<1)requestAnimationFrame(step);})(t0);}
function addChip(id,chip){const c=document.createElement("div");c.className="chip";c.textContent=chip[1];
  c.onclick=()=>openDist(id,null);$("#chips").appendChild(c);requestAnimationFrame(()=>requestAnimationFrame(()=>c.classList.add("in")));}

function toFinal(){
  show("s-final");soul++;$("#soulN").textContent=soul;
  document.getElementById("stage").style.background="var(--c-final)";
  $("#avatar").outerHTML=AVATAR.replace('class="ico avatar"','class="ico avatar" id="avatar"');
  const C=CTY[state.country],child=state.ageIdx<=1;
  const who=child?(state.sex==="F"?"Une enfant":"Un enfant"):(state.sex==="F"?"Une femme":"Un homme");
  const mil={grande:"dans une grande ville",ville:"dans une ville",rural:"à la campagne"}[state.milieu];
  $("#personaLine").innerHTML=`<span class="hl">${who}</span>, ${state.age} ans, ${mil} ${C.prep} ${C.name_fr}.`;
  const edu={petite:"pas encore l'école",ecole:"à l'école",hors:"non scolarisé",aucune:"sans école",primaire:"niveau primaire",secondaire:"niveau lycée",superieur:"diplômé du supérieur"}[state.edu];
  const fam={enfant:"chez ses parents",celibataire:"célibataire",couple:"en couple",parent:"parent",veuf:state.sex==="F"?"veuve":"veuf"}[state.family];
  const sante={bonne:"en pleine forme",gene_legere:"une gêne légère",incap_moderee:"une incapacité modérée",incap_severe:"une incapacité sévère"}[state.health];
  $("#personaDay").textContent=`${cap(edu)}. ${cap(fam)}. ${cap(sante)}${state.mental?", et un trouble de santé mentale":""}.`;
  const fc=$("#finalChips");fc.innerHTML="";
  Object.keys(distLog).forEach(id=>{const val=distLog[id].chip&&distLog[id].chip[1];if(!val)return;
    const el=document.createElement("div");el.className="chip";el.textContent=val;el.onclick=()=>openDist(id,null);fc.appendChild(el);});
  $("#answerRow").style.display="flex";$("#after").style.opacity="0";$("#replayRow").classList.remove("show");
  if(!REDUCED)confetti();
}
function cap(s){return s?s[0].toUpperCase()+s.slice(1):s;}
function answer(swap){$("#answerRow").style.display="none";
  $("#after").textContent=swap?"audacieux.":"noté. tu gardes la tienne.";$("#after").style.opacity="1";
  setTimeout(()=>$("#replayRow").classList.add("show"),600);}

function openDist(id,picked){const e=distLog[id];if(!e)return;const n=norm(e.dist),s=STRATA.find(x=>x.id===id);
  const hi=picked||e.picked||null;
  const rows=Object.keys(n).map(k=>{let l;try{l=s.reveal(k,{...state}).chip[1];}catch(_){l=k;}return{k,l,p:n[k]};}).sort((a,b)=>b.p-a.p);
  $("#mK").textContent="les probas";$("#mT").textContent=e.label;
  $("#mB").textContent="ce que le dé pouvait sortir, d'après les vraies données, dans cette situation.";
  const host=$("#mDist");host.innerHTML="";
  rows.forEach(r=>{const el=document.createElement("div");el.className="drow"+(hi&&r.k===hi?" pick":"");
    el.innerHTML=`<span class="dn">${r.l}</span><span class="db"><i style="width:${(r.p*100).toFixed(1)}%"></i></span><span class="dp">${(r.p*100).toFixed(0)}%</span>`;host.appendChild(el);});
  $("#mSrc").textContent="source · "+e.source;$("#modal").classList.add("open");}
function closeModal(){$("#modal").classList.remove("open");}

function confetti(){const cols=["#3B6BFF","#FF6B5E","#FFB020","#12B5A0","#8B5CF6","#FF6FA5"];
  for(let k=0;k<26;k++){const d=document.createElement("div");d.className="confetti";
    d.style.left=(20+Math.random()*60)+"%";d.style.top="30%";d.style.background=cols[k%cols.length];
    d.style.transform=`rotate(${Math.random()*360}deg)`;d.style.borderRadius=Math.random()<.5?"50%":"2px";
    document.getElementById("stage").appendChild(d);
    d.animate([{transform:d.style.transform,opacity:1},{transform:`translate(${(Math.random()-.5)*260}px,${300+Math.random()*260}px) rotate(${Math.random()*720}deg)`,opacity:0}],
      {duration:1100+Math.random()*700,easing:"cubic-bezier(.2,.6,.4,1)"}).onfinish=()=>d.remove();}}

function show(id){document.querySelectorAll(".screen").forEach(s=>s.classList.remove("active"));$("#"+id).classList.add("active");}

/* ================= chargement des données ================= */
async function loadData(){
  const names=["countries","age_sex","settlement","income","education","health","family","living"];
  try{
    const out={};
    for(const n of names){const r=await fetch("data/"+n+".json",{cache:"no-store"});if(!r.ok)throw new Error(n);out[n]=await r.json();}
    console.info("[Dé de la Vie] données chargées depuis /data");
    return out;
  }catch(e){
    if(window.__SEED__){console.info("[Dé de la Vie] /data indisponible, seed embarqué utilisé");return window.__SEED__;}
    throw e;
  }
}
function buildIndexes(){CTY={};DATA.countries.rows.forEach(r=>CTY[r.iso3]=r);}

function wire(){
  $("#earthBtn").addEventListener("click",startPlay);
  $("#startBtn").addEventListener("click",startPlay);
  $("#nextBtn").addEventListener("click",nextStep);
  $("#ansNo").addEventListener("click",()=>answer(false));
  $("#ansYes").addEventListener("click",()=>answer(true));
  $("#replayBtn").addEventListener("click",()=>{const eb=$("#earthBtn");eb.style.transition="none";eb.style.transform="scale(1)";eb.style.opacity="1";document.getElementById("stage").style.background="var(--c-intro)";show("s-intro");});
  $("#mClose").addEventListener("click",closeModal);
  $("#modal").addEventListener("click",e=>{if(e.target.id==="modal")closeModal();});
  addEventListener("keydown",e=>{if(e.key==="Escape")closeModal();});
  $("#s-play").addEventListener("click",e=>{if(e.target.closest("#die"))rollDie();});
}

(async function init(){
  try{ DATA=await loadData(); buildIndexes(); wire(); }
  catch(e){ document.body.innerHTML='<div style="font-family:sans-serif;padding:40px;color:#fff">Données introuvables. Sers le dossier avec un serveur, ou ouvre le fichier autonome.</div>'; console.error(e); }
})();
