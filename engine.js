/* =========================================================================
   LE DÉ DE LA VIE — moteur data-driven
   Aucune donnée pays n'est écrite ici. Tout vient de DATA, chargé depuis
   /data/*.json (si l'app est servie) ou du seed embarqué window.__SEED__
   (fallback pour l'aperçu en fichier local). Ajouter un pays = ajouter des
   lignes de données, jamais toucher ce code.

   INTERNATIONALISATION (FR / EN)
   Toutes les chaînes visibles passent par la couche I18N ci-dessous. La
   logique de données (distribution / apply) reste identique dans les deux
   langues : on ne traduit que l'interface, jamais les chiffres. Les noms de
   pays viennent de name_fr / name_en (données), les libellés de dimensions
   de label_fr / label_en (schema.json). Le portrait final a un gabarit de
   phrase distinct par langue (préposition en/au/aux côté FR, « in » + nom
   anglais côté EN).
   ========================================================================= */

const WORLD_POP = 8_000_000_000;
let DATA = null, CTY = {};

/* ================= COUCHE I18N (interface uniquement) ================= */
let LANG = "fr";
const LANGS = ["fr", "en"];

function detectLang(){
  try{ const saved = localStorage.getItem("dv_lang"); if(saved && LANGS.includes(saved)) return saved; }catch(_){}
  const nav = (navigator.language || navigator.userLanguage || "fr").toLowerCase();
  return nav.startsWith("fr") ? "fr" : "en";
}

const I18N = {
  fr: {
    doc_lang: "fr", locale: "fr-FR",
    title: "Le Dé de la Vie",
    logo: "Le Dé<br>de la Vie",
    kicker: "un jeu de hasard grandeur nature",
    tagline: "8 milliards de vies. Le dé en tire une au sort. Ça aurait pu être la tienne.",
    scrawl: "clique la Terre &darr;",
    start_btn: "Lancer le dé",
    earth_aria: "Lancer",
    hud_souls: "vies tirées",
    hud_count: "des gens comme ça",
    step: "étape",
    die_hint: "clique le dé pour tirer",
    src_btn: "voir les probas",
    next_btn: "Continuer &rarr;",
    final_title: "le dé a parlé. voici ta nouvelle vie :",
    question: "Tu échanges ta vie contre la sienne ?",
    ans_no: "Non merci",
    ans_yes: "Carrément",
    ans_yes_reply: "audacieux.",
    ans_no_reply: "noté. tu gardes la tienne.",
    replay_btn: "Relancer le dé",
    modal_kicker: "les probas",
    modal_body: "ce que le dé pouvait sortir, d'après les vraies données, dans cette situation.",
    modal_close: "OK",
    modal_source_prefix: "source · ",
    data_error: "Données introuvables. Sers le dossier avec un serveur, ou ouvre le fichier autonome.",
    lang_name: "Français",
    /* libellés d'étape */
    steps: {pays:"le pays", agesexe:"l'âge & le sexe", milieu:"le décor", revenu:"le portefeuille",
      education:"les études", sante:"la santé", famille:"la tribu", detail:"le bonus"},
    /* libellés de catégorie (chips) */
    cat: {pays:"pays", agesexe:"âge", milieu:"décor", revenu:"argent",
      education:"études", sante:"santé", famille:"tribu", detail:"bonus"},
    /* pays */
    pays_cap: n => "direction " + n + " !",
    /* âge & sexe */
    who_child: s => s === "F" ? "Une fille" : "Un garçon",
    who_adult: s => s === "F" ? "Une femme" : "Un homme",
    agesexe_cap: yr => yr + " ans, on démarre",
    agesexe_chip: (s, yr) => (s === "F" ? "F" : "H") + ", " + yr + " ans",
    /* milieu */
    milieu_word: {grande:"La grande ville", ville:"Une ville", rural:"La campagne"},
    milieu_cap: {grande:"lumières et béton", ville:"peinard, taille moyenne", rural:"grand air, loin du bruit"},
    milieu_chip: {grande:"Grande ville", ville:"Ville", rural:"Campagne"},
    /* revenu */
    revenu_word: ["Serré","Modeste","Au milieu","Confortable","Peinard"],
    revenu_cap: pct => "plus riche que " + pct + " % du monde",
    /* éducation */
    edu_word: {petite:"Trop petit pour l'école", ecole:"À l'école", hors:"Pas scolarisé",
      aucune:"Pas allé à l'école", primaire:"Niveau primaire", secondaire:"Niveau lycée", superieur:"Études supérieures"},
    edu_cap: {superieur:"diplôme dans la poche", secondaire:"bac en vue", ecole:"cartable sur le dos"},
    edu_chip: {petite:"Petite enfance", ecole:"Scolarisé", hors:"Non scolarisé", aucune:"Sans école",
      primaire:"Primaire", secondaire:"Lycée", superieur:"Supérieur"},
    /* santé */
    sante_word: {bonne:"En pleine forme", gene_legere:"Une gêne légère", incap_moderee:"Une incapacité modérée", incap_severe:"Une incapacité sévère"},
    sante_cap_bonne: "la grande forme",
    /* famille */
    famille_word: {enfant:"Chez ses parents", celibataire:"Célibataire", couple:"En couple", parent:"Déjà parent"},
    famille_veuf: s => s === "F" ? "Veuve" : "Veuf",
    /* bonus / conditions de vie */
    living: {
      electricite: {y:"L'électricité à la maison", n:"Pas d'électricité fiable"},
      internet:    {y:"Connecté à internet",       n:"Pas d'internet"},
      eau:         {y:"L'eau potable au robinet",   n:"Pas d'eau potable sûre"}
    },
    /* portrait final */
    persona_who_child: s => s === "F" ? "Une enfant" : "Un enfant",
    persona_who_adult: s => s === "F" ? "Une femme" : "Un homme",
    persona_milieu: {grande:"dans une grande ville", ville:"dans une ville", rural:"à la campagne"},
    persona_line: (who, age, mil, prep, name) =>
      `<span class="hl">${who}</span>, ${age} ans, ${mil} ${prep} ${name}.`,
    persona_edu: {petite:"pas encore l'école", ecole:"à l'école", hors:"non scolarisé", aucune:"sans école",
      primaire:"niveau primaire", secondaire:"niveau lycée", superieur:"diplômé du supérieur"},
    persona_fam: {enfant:"chez ses parents", celibataire:"célibataire", couple:"en couple", parent:"parent"},
    persona_fam_veuf: s => s === "F" ? "veuve" : "veuf",
    persona_sante: {bonne:"en pleine forme", gene_legere:"une gêne légère", incap_moderee:"une incapacité modérée", incap_severe:"une incapacité sévère"},
    persona_mental: ", et un trouble de santé mentale",
    src_label: {wpp:"ONU · WPP 2024", wup:"ONU · WUP 2025", pip:"Banque mondiale · PIP",
      barrolee:"Barro-Lee · UNESCO", gbd:"IHME · GBD 2023", undesa_marriage:"ONU DESA · Marriage Data", wdi:"Banque mondiale · WDI"}
  },
  en: {
    doc_lang: "en", locale: "en-US",
    title: "The Dice of Life",
    logo: "The Dice<br>of Life",
    kicker: "a life-size game of chance",
    tagline: "8 billion lives. The die draws one at random. It could have been yours.",
    scrawl: "tap the Earth &darr;",
    start_btn: "Roll the die",
    earth_aria: "Start",
    hud_souls: "lives drawn",
    hud_count: "people like this",
    step: "step",
    die_hint: "tap the die to roll",
    src_btn: "see the odds",
    next_btn: "Continue &rarr;",
    final_title: "the die has spoken. here's your new life:",
    question: "Would you swap your life for theirs?",
    ans_no: "No thanks",
    ans_yes: "Absolutely",
    ans_yes_reply: "bold.",
    ans_no_reply: "noted. you keep yours.",
    replay_btn: "Roll again",
    modal_kicker: "the odds",
    modal_body: "what the die could have rolled, from the real data, in this situation.",
    modal_close: "OK",
    modal_source_prefix: "source · ",
    data_error: "Data not found. Serve the folder with a server, or open the standalone file.",
    lang_name: "English",
    steps: {pays:"the country", agesexe:"age & sex", milieu:"the setting", revenu:"the wallet",
      education:"schooling", sante:"health", famille:"the family", detail:"the bonus"},
    cat: {pays:"country", agesexe:"age", milieu:"setting", revenu:"money",
      education:"school", sante:"health", famille:"family", detail:"bonus"},
    pays_cap: n => "off to " + n + "!",
    who_child: s => s === "F" ? "A girl" : "A boy",
    who_adult: s => s === "F" ? "A woman" : "A man",
    agesexe_cap: yr => "aged " + yr + ", here we go",
    agesexe_chip: (s, yr) => (s === "F" ? "F" : "M") + ", " + yr + "y",
    milieu_word: {grande:"The big city", ville:"A town", rural:"The countryside"},
    milieu_cap: {grande:"lights and concrete", ville:"easy, mid-sized", rural:"fresh air, far from the noise"},
    milieu_chip: {grande:"Big city", ville:"Town", rural:"Countryside"},
    revenu_word: ["Tight","Modest","Middle","Comfortable","Cushy"],
    revenu_cap: pct => "richer than " + pct + "% of the world",
    edu_word: {petite:"Too young for school", ecole:"In school", hors:"Out of school",
      aucune:"Never went to school", primaire:"Primary level", secondaire:"Secondary level", superieur:"Higher education"},
    edu_cap: {superieur:"degree in hand", secondaire:"diploma in sight", ecole:"backpack on"},
    edu_chip: {petite:"Early years", ecole:"In school", hors:"Out of school", aucune:"No school",
      primaire:"Primary", secondaire:"Secondary", superieur:"Higher"},
    sante_word: {bonne:"In great shape", gene_legere:"A slight impairment", incap_moderee:"A moderate disability", incap_severe:"A severe disability"},
    sante_cap_bonne: "feeling great",
    famille_word: {enfant:"Living with parents", celibataire:"Single", couple:"In a relationship", parent:"Already a parent"},
    famille_veuf: () => "Widowed",
    living: {
      electricite: {y:"Electricity at home", n:"No reliable electricity"},
      internet:    {y:"Connected to the internet", n:"No internet"},
      eau:         {y:"Running drinking water", n:"No safe drinking water"}
    },
    persona_who_child: s => s === "F" ? "A girl" : "A boy",
    persona_who_adult: s => s === "F" ? "A woman" : "A man",
    persona_milieu: {grande:"in a big city", ville:"in a town", rural:"in the countryside"},
    persona_line: (who, age, mil, prep, name) =>
      `<span class="hl">${who}</span>, aged ${age}, living ${mil} in ${name}.`,
    persona_edu: {petite:"not in school yet", ecole:"in school", hors:"out of school", aucune:"no schooling",
      primaire:"primary level", secondaire:"secondary level", superieur:"a higher-education graduate"},
    persona_fam: {enfant:"living with parents", celibataire:"single", couple:"in a relationship", parent:"a parent"},
    persona_fam_veuf: () => "widowed",
    persona_sante: {bonne:"in great shape", gene_legere:"a slight impairment", incap_moderee:"a moderate disability", incap_severe:"a severe disability"},
    persona_mental: ", and a mental-health condition",
    src_label: {wpp:"UN · WPP 2024", wup:"UN · WUP 2025", pip:"World Bank · PIP",
      barrolee:"Barro-Lee · UNESCO", gbd:"IHME · GBD 2023", undesa_marriage:"UN DESA · Marriage Data", wdi:"World Bank · WDI"}
  }
};

const T = () => I18N[LANG];                         /* pack de langue courant */
const countryName = iso => LANG === "en" ? (CTY[iso].name_en || CTY[iso].name_fr) : CTY[iso].name_fr;

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
const fmt=n=>Math.round(n).toLocaleString(T().locale).replace(/ /g," ").replace(/ /g," ");
const norm=o=>{const t=Object.values(o).reduce((a,b)=>a+b,0)||1;const r={};for(const k in o)r[k]=o[k]/t;return r;};
function pick(d){const n=norm(d);let r=Math.random(),a=0;for(const k in n){a+=n[k];if(r<=a)return k;}return Object.keys(n).pop();}
const REDUCED=matchMedia("(prefers-reduced-motion:reduce)").matches;
const wait=ms=>new Promise(r=>setTimeout(r,REDUCED?Math.min(ms,100):ms));
const ageIdx=id=>AGES.indexOf(id);

/* ================= STRATES ================= */
/* La logique de tirage (distribution, apply) est universelle et identique
   quelle que soit la langue. Seul reveal() produit du texte visible : il lit
   dans T() (pack de langue courant). Un chip est [catégorie, valeur]. */
const STRATA=[
 {id:"pays",source_ref:()=>DATA.countries.source_id,
  distribution:()=>{const d={};DATA.countries.rows.forEach(r=>d[r.iso3]=r.population);return d;},
  reveal:o=>{const n=countryName(o);return{word:n,cap:T().pays_cap(n),chip:[T().cat.pays,n]};},
  apply:(o,st)=>{st.country=o;}},

 {id:"agesexe",source_ref:()=>DATA.age_sex.source_id,
  distribution:st=>({...DATA.age_sex.data[st.country].shares}),
  reveal:o=>{const[a,s]=o.split("|"),i=ageIdx(a),yr=AGE_MID[a],child=i<=1;
    const word=child?T().who_child(s):T().who_adult(s);
    return{word,cap:T().agesexe_cap(yr),chip:[T().cat.agesexe,T().agesexe_chip(s,yr)]};},
  apply:(o,st)=>{const[a,s]=o.split("|");st.ageId=a;st.ageIdx=ageIdx(a);st.age=AGE_MID[a];st.sex=s;}},

 {id:"milieu",source_ref:()=>DATA.settlement.source_id,
  distribution:st=>({...DATA.settlement.data[st.country].shares}),
  reveal:o=>({word:T().milieu_word[o],cap:T().milieu_cap[o],chip:[T().cat.milieu,T().milieu_chip[o]]}),
  apply:(o,st)=>{st.rural=o==="rural";st.milieu=o;}},

 {id:"revenu",source_ref:()=>DATA.income.source_id,
  distribution:()=>({q1:.2,q2:.2,q3:.2,q4:.2,q5:.2}),
  reveal:(o,st)=>{const qi=["q1","q2","q3","q4","q5"].indexOf(o);
    const lbl=T().revenu_word[qi];
    // percentile mondial réel du quintile : un pauvre -> petit %, un riche -> grand %.
    // borné 1..99 pour éviter "0 %" / "100 %" aux extrêmes.
    const pct=clamp(DATA.income.data[st.country].global_percentile[qi],1,99);
    return{word:lbl,cap:T().revenu_cap(pct),chip:[T().cat.revenu,lbl]};},
  apply:(o,st)=>{st.qi=["q1","q2","q3","q4","q5"].indexOf(o);}},

 {id:"education",source_ref:()=>DATA.education.source_id,
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
  reveal:o=>({word:T().edu_word[o],cap:T().edu_cap[o]||"",chip:[T().cat.education,T().edu_chip[o]]}),
  apply:(o,st)=>{st.edu=o;}},

 {id:"sante",source_ref:()=>DATA.health.source_id,
  distribution:st=>{const H=DATA.health;let w={...H.severity_base_group[H.country_group[st.country]]};
    const i=st.ageIdx,ab=H.age_factors.boost[i],ga=H.age_factors.good[i],li=H.income_penalty[st.qi];
    w.bonne*=ga;w.incap_moderee*=ab*li;w.incap_severe*=ab*li;w.gene_legere*=(0.9+0.05*i);return w;},
  reveal:(o,st)=>{const H=DATA.health,m=H.mental;
    const mp=clamp(m.base+(st.rural?m.rural_add:0)+(st.qi<=1?m.lowinc_add:0),m.min,m.max);st.mental=Math.random()<mp;
    return{word:T().sante_word[o],cap:o==="bonne"?T().sante_cap_bonne:"",chip:[T().cat.sante,T().sante_word[o]]};},
  apply:(o,st)=>{st.health=o;}},

 {id:"famille",source_ref:()=>DATA.family.source_id,
  distribution:st=>{const F=DATA.family,P=F.params,early=F.early_parenthood.includes(st.country);
    if(st.ageIdx<=1)return{enfant:1};
    if(st.ageIdx===2)return early?{...P.young_early}:{...P.young_late};
    if(st.ageIdx>=6){const vf=P.elder_widow[st.sex];return{veuf:vf,couple:1-vf-0.08,celibataire:0.08};}
    let cel=P.mid_celibataire[st.ageId]||0.2,par=P.mid_parent[st.ageId]||0.4;
    if(early){cel*=P.early_cel_mult;par*=P.early_par_mult;}
    let cou=1-cel-par;if(cou<0.05)cou=0.05;
    return{celibataire:cel,couple:cou,parent:par};},
  reveal:(o,st)=>{const w=o==="veuf"?T().famille_veuf(st.sex):T().famille_word[o];
    return{word:w,cap:"",chip:[T().cat.famille,w]};},
  apply:(o,st)=>{st.family=o;}},

 {id:"detail",source_ref:()=>DATA.living.source_id,
  distribution:()=>({a:1}),
  reveal:(o,st)=>{const L=DATA.living,d=L.data[st.country],rp=st.rural?L.rural_penalty:1,lv=T().living;
    const fs=[{h:Math.random()<clamp(d.electricite*rp,0,1),y:lv.electricite.y,n:lv.electricite.n},
             {h:Math.random()<clamp(d.internet*rp,0,1),y:lv.internet.y,n:lv.internet.n},
             {h:Math.random()<clamp(d.eau*rp,0,1),y:lv.eau.y,n:lv.eau.n}];
    const miss=fs.find(f=>!f.h),f=miss||fs[0];const txt=f.h?f.y:f.n;
    return{word:txt,cap:"",chip:[T().cat.detail,txt]};},
  apply:()=>{}}
];

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
  $("#stepTag").textContent=T().step+" "+(i+1)+" · "+T().steps[s.id];
  $("#ico").outerHTML=ICONS[s.id].replace('class="ico"','class="ico" id="ico"');
  $("#result").textContent="";$("#result").className="result";
  $("#caption").textContent="";$("#caption").className="caption";
  $("#srcBtn").style.display="none";$("#nextBtn").classList.remove("show");
  $("#dieWrap").style.display="flex";$("#dieHint").innerHTML=T().die_hint;$("#dieHint").style.visibility="visible";
  buildDie(Math.ceil(Math.random()*6));
}
function buildDie(face){const L={1:[4],2:[0,8],3:[0,4,8],4:[0,2,6,8],5:[0,2,4,6,8],6:[0,2,3,5,6,8]};
  const on=new Set(L[face]);let h="";for(let k=0;k<9;k++)h+='<div class="pip'+(on.has(k)?" on":"")+'"></div>';$("#die").innerHTML=h;}

async function rollDie(){
  if(rolled)return;rolled=true;const s=STRATA[i];
  curDist=s.distribution(state);distLog[s.id]={dist:curDist,source_id:s.source_ref(),strataId:s.id};
  curOutcome=pick(curDist);const share=norm(curDist)[curOutcome];
  const die=$("#die");$("#dieHint").style.visibility="hidden";
  const spins=REDUCED?1:6;
  for(let c=0;c<spins;c++){die.classList.remove("rolling");void die.offsetWidth;die.classList.add("rolling");buildDie(Math.ceil(Math.random()*6));await wait(90);}
  die.classList.remove("rolling");
  const r=s.reveal(curOutcome,state);s.apply(curOutcome,state);
  distLog[s.id].picked=curOutcome;
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
  c.dataset.strata=id;
  c.onclick=()=>openDist(id,null);$("#chips").appendChild(c);requestAnimationFrame(()=>requestAnimationFrame(()=>c.classList.add("in")));}

function toFinal(){
  show("s-final");soul++;$("#soulN").textContent=soul;
  document.getElementById("stage").style.background="var(--c-final)";
  $("#avatar").outerHTML=AVATAR.replace('class="ico avatar"','class="ico avatar" id="avatar"');
  renderPersona();
  const fc=$("#finalChips");fc.innerHTML="";
  Object.keys(distLog).forEach(id=>{const e=distLog[id];if(e.picked===undefined)return;
    const val=chipValue(id);if(!val)return;
    const el=document.createElement("div");el.className="chip";el.textContent=val;el.dataset.strata=id;
    el.onclick=()=>openDist(id,null);fc.appendChild(el);});
  $("#answerRow").style.display="flex";$("#after").style.opacity="0";$("#after").textContent="";$("#replayRow").classList.remove("show");
  if(!REDUCED)confetti();
}
/* portrait final : gabarit de phrase distinct par langue */
function renderPersona(){
  const C=CTY[state.country],child=state.ageIdx<=1;
  const who=child?T().persona_who_child(state.sex):T().persona_who_adult(state.sex);
  const mil=T().persona_milieu[state.milieu];
  $("#personaLine").innerHTML=T().persona_line(who,state.age,mil,C.prep,countryName(state.country));
  const edu=T().persona_edu[state.edu];
  const fam=state.family==="veuf"?T().persona_fam_veuf(state.sex):T().persona_fam[state.family];
  const sante=T().persona_sante[state.health];
  $("#personaDay").textContent=`${cap(edu)}. ${cap(fam)}. ${cap(sante)}${state.mental?T().persona_mental:""}.`;
}
function cap(s){return s?s[0].toUpperCase()+s.slice(1):s;}
function answer(swap){$("#answerRow").style.display="none";
  $("#after").dataset.swap=swap?"1":"0";
  $("#after").textContent=swap?T().ans_yes_reply:T().ans_no_reply;$("#after").style.opacity="1";
  setTimeout(()=>$("#replayRow").classList.add("show"),600);}

/* valeur de chip courante pour une strate (recalcule dans la langue active) */
function chipValue(id){const e=distLog[id];if(!e||e.picked===undefined)return null;
  const s=STRATA.find(x=>x.id===id);try{return s.reveal(e.picked,{...state}).chip[1];}catch(_){return null;}}

function openDist(id,picked){const e=distLog[id];if(!e)return;const n=norm(e.dist),s=STRATA.find(x=>x.id===id);
  const hi=picked||e.picked||null;
  const rows=Object.keys(n).map(k=>{let l;try{l=s.reveal(k,{...state}).chip[1];}catch(_){l=k;}return{k,l,p:n[k]};}).sort((a,b)=>b.p-a.p);
  $("#mK").textContent=T().modal_kicker;$("#mT").textContent=T().steps[id];
  $("#mB").textContent=T().modal_body;
  const host=$("#mDist");host.innerHTML="";
  rows.forEach(r=>{const el=document.createElement("div");el.className="drow"+(hi&&r.k===hi?" pick":"");
    el.innerHTML=`<span class="dn">${r.l}</span><span class="db"><i style="width:${(r.p*100).toFixed(1)}%"></i></span><span class="dp">${(r.p*100).toFixed(0)}%</span>`;host.appendChild(el);});
  $("#mSrc").textContent=T().modal_source_prefix+(T().src_label[e.source_id]||e.source_id);$("#modal").classList.add("open");
  $("#modal").dataset.dist=id;$("#modal").dataset.pick=picked||"";}
function closeModal(){$("#modal").classList.remove("open");$("#modal").dataset.dist="";}

function confetti(){const cols=["#3B6BFF","#FF6B5E","#FFB020","#12B5A0","#8B5CF6","#FF6FA5"];
  for(let k=0;k<26;k++){const d=document.createElement("div");d.className="confetti";
    d.style.left=(20+Math.random()*60)+"%";d.style.top="30%";d.style.background=cols[k%cols.length];
    d.style.transform=`rotate(${Math.random()*360}deg)`;d.style.borderRadius=Math.random()<.5?"50%":"2px";
    document.getElementById("stage").appendChild(d);
    d.animate([{transform:d.style.transform,opacity:1},{transform:`translate(${(Math.random()-.5)*260}px,${300+Math.random()*260}px) rotate(${Math.random()*720}deg)`,opacity:0}],
      {duration:1100+Math.random()*700,easing:"cubic-bezier(.2,.6,.4,1)"}).onfinish=()=>d.remove();}}

function show(id){document.querySelectorAll(".screen").forEach(s=>s.classList.remove("active"));$("#"+id).classList.add("active");}

/* ================= application de la langue à l'interface ================= */
function applyStaticI18n(){
  const t=T();
  document.documentElement.lang=t.doc_lang;
  document.title=t.title;
  document.querySelectorAll("[data-i18n]").forEach(el=>{el.innerHTML=t[el.dataset.i18n];});
  const eb=$("#earthBtn");if(eb)eb.setAttribute("aria-label",t.earth_aria);
  /* boutons de langue actifs */
  document.querySelectorAll(".lang-btn").forEach(b=>b.classList.toggle("on",b.dataset.lang===LANG));
}
/* rafraîchit tout l'écran courant (jeu en cours, portrait, modale) */
function refreshDynamic(){
  /* compteur */
  const cn=$("#countN");if(cn)cn.textContent=fmt(remaining!==undefined?Math.max(remaining,1):WORLD_POP);
  /* étape courante */
  if(i<STRATA.length){const s=STRATA[i];
    $("#stepTag").textContent=T().step+" "+(i+1)+" · "+T().steps[s.id];
    if(rolled&&curOutcome){const r=s.reveal(curOutcome,state);
      $("#result").textContent=r.word;const cp=$("#caption");cp.textContent=r.cap||"";}
  }
  /* chips de la barre de jeu */
  document.querySelectorAll("#chips .chip").forEach(c=>{const v=chipValue(c.dataset.strata);if(v)c.textContent=v;});
  /* portrait final si visible */
  if($("#s-final").classList.contains("active")){
    renderPersona();
    document.querySelectorAll("#finalChips .chip").forEach(c=>{const v=chipValue(c.dataset.strata);if(v)c.textContent=v;});
    const af=$("#after");if(af&&af.style.opacity==="1"&&af.dataset.swap!==undefined)
      af.textContent=af.dataset.swap==="1"?T().ans_yes_reply:T().ans_no_reply;
  }
  /* modale ouverte */
  if($("#modal").classList.contains("open")&&$("#modal").dataset.dist){
    const id=$("#modal").dataset.dist,pk=$("#modal").dataset.pick;openDist(id,pk||null);
  }
}
function setLang(lang){
  if(!LANGS.includes(lang)||lang===LANG)return;
  LANG=lang;
  try{localStorage.setItem("dv_lang",lang);}catch(_){}
  applyStaticI18n();
  refreshDynamic();
}

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
  document.querySelectorAll(".lang-btn").forEach(b=>b.addEventListener("click",()=>setLang(b.dataset.lang)));
}

(async function init(){
  try{
    LANG=detectLang();
    DATA=await loadData(); buildIndexes(); wire();
    applyStaticI18n();
  }
  catch(e){ document.body.innerHTML='<div style="font-family:sans-serif;padding:40px;color:#fff">'+T().data_error+'</div>'; console.error(e); }
})();
