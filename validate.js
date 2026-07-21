#!/usr/bin/env node
/* Valide les fichiers /data contre schema.json.
   Usage : node validate.js   (depuis le dossier projet)
   Sort en code 1 si au moins une erreur. */
const fs = require("fs"), path = require("path");
const dir = __dirname, dataDir = path.join(dir, "data");
const schema = JSON.parse(fs.readFileSync(path.join(dir, "schema.json"), "utf8"));
const load = n => JSON.parse(fs.readFileSync(path.join(dataDir, n + ".json"), "utf8"));

const ids = name => new Set(schema.dimensions[name].map(d => d.id));
const AGE = ids("ages"), SEX = ids("sexes"), SET = ids("settlement"),
      EDU = ids("education_adult"), HEALTH = ids("health_states"), FAM = ids("family");

const errors = [], warns = [];
const EPS = 1e-6;
const err = m => errors.push(m);
const near1 = o => Math.abs(Object.values(o).reduce((a, b) => a + b, 0) - 1) <= 1e-3;
const inRange = (x, a, b) => typeof x === "number" && x >= a && x <= b;
const validShares = (o, set, ctx) => {
  for (const k in o) { if (!set.has(k)) err(`${ctx}: bucket inconnu "${k}"`); if (o[k] < -EPS) err(`${ctx}: part negative ${k}`); }
  if (!near1(o)) err(`${ctx}: somme != 1 (${Object.values(o).reduce((a,b)=>a+b,0).toFixed(4)})`);
};

// domaine pays
const countries = load("countries");
if (!Array.isArray(countries.rows) || !countries.rows.length) err("countries.rows vide");
const DOMAIN = countries.rows.map(r => r.iso3);
countries.rows.forEach(r => {
  ["iso3","name_fr","region","income_group","population","prep"].forEach(f => { if (r[f] === undefined) err(`countries ${r.iso3||"?"}: champ manquant ${f}`); });
  if (!(r.population > 0)) err(`countries ${r.iso3}: population invalide`);
});

const need = (obj, iso, ctx) => { if (!obj || obj[iso] === undefined) { err(`${ctx}: ${iso} absent`); return false; } return true; };

// age_sex
const as = load("age_sex");
DOMAIN.forEach(iso => { if (need(as.data, iso, "age_sex")) {
  const sh = as.data[iso].shares || {};
  for (const k in sh) { const [a,s] = k.split("|"); if (!AGE.has(a)||!SEX.has(s)) err(`age_sex ${iso}: cle invalide ${k}`); }
  validShares(sh, new Set(Object.keys(sh)), `age_sex ${iso}`);
}});

// settlement
const se = load("settlement");
DOMAIN.forEach(iso => { if (need(se.data, iso, "settlement")) validShares(se.data[iso].shares, SET, `settlement ${iso}`); });

// income
const inc = load("income");
DOMAIN.forEach(iso => { if (need(inc.data, iso, "income")) {
  const gp = inc.data[iso].global_percentile;
  if (!Array.isArray(gp) || gp.length !== 5) err(`income ${iso}: global_percentile doit avoir 5 valeurs`);
  else gp.forEach(v => { if (!inRange(v,0,100)) err(`income ${iso}: percentile hors [0,100]`); });
}});

// education
const ed = load("education");
DOMAIN.forEach(iso => { if (need(ed.attainment_base, iso, "education.attainment_base")) validShares(ed.attainment_base[iso].shares, EDU, `education base ${iso}`);
  if (need(ed.child_enrollment, iso, "education.child_enrollment")) { if (!inRange(ed.child_enrollment[iso].in_school,0,1)) err(`education ${iso}: in_school hors [0,1]`); }});
["rural_penalty","income_prime","gender_gap"].forEach(f => { if (!ed.factors || !ed.factors[f]) err(`education.factors.${f} manquant`); });

// health
const he = load("health");
DOMAIN.forEach(iso => { if (need(he.country_group, iso, "health.country_group")) { if (!["rich","mid","low"].includes(he.country_group[iso])) err(`health ${iso}: groupe inconnu`); }});
["rich","mid","low"].forEach(g => { if (!he.severity_base_group[g]) err(`health.severity_base_group.${g} manquant`); else validShares(he.severity_base_group[g], HEALTH, `health base ${g}`); });
if (!he.age_factors || he.age_factors.boost.length !== 8 || he.age_factors.good.length !== 8) err("health.age_factors: boost/good doivent avoir 8 valeurs");
if (!Array.isArray(he.income_penalty) || he.income_penalty.length !== 5) err("health.income_penalty: 5 valeurs");
if (!he.mental || he.mental.base === undefined) err("health.mental.base manquant");

// family
const fa = load("family");
["young_early","young_late","elder_widow","mid_celibataire","mid_parent"].forEach(p => { if (!fa.params || !fa.params[p]) err(`family.params.${p} manquant`); });
(fa.early_parenthood || []).forEach(iso => { if (!DOMAIN.includes(iso)) warns.push(`family.early_parenthood: ${iso} hors domaine`); });

// living
const li = load("living");
if (li.rural_penalty === undefined) err("living.rural_penalty manquant");
DOMAIN.forEach(iso => { if (need(li.data, iso, "living")) ["electricite","internet","eau"].forEach(k => { if (!inRange(li.data[iso][k],0,1)) err(`living ${iso}: ${k} hors [0,1]`); }); });

// rapport
console.log(`Pays dans le domaine : ${DOMAIN.length} (${DOMAIN.join(", ")})`);
console.log(`Tables verifiees : countries, age_sex, settlement, income, education, health, family, living`);
if (warns.length) { console.log("\nAvertissements :"); warns.forEach(w => console.log("  ! " + w)); }
if (errors.length) { console.log(`\n${errors.length} ERREUR(S) :`); errors.forEach(e => console.log("  x " + e)); process.exit(1); }
console.log("\nOK. Toutes les distributions somment a 1, tous les pays presents, aucun bucket inconnu.");
