#!/usr/bin/env python3
# Genere les fichiers /data du seed (7 pays) a partir des parametres du prototype.
# Sortie conforme a schema.json. Source unique de verite : ce script.
import json, os

OUT = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(OUT, exist_ok=True)

AGES = ["a00_04","a05_14","a15_19","a20_34","a35_49","a50_64","a65_79","a80p"]
FEMALE_BASE = [0.487,0.487,0.487,0.495,0.502,0.515,0.555,0.63]
clamp = lambda x,a,b: max(a,min(b,x))

# --- parametres bruts par pays (diriges par les vraies donnees, a remplacer par le pipeline) ---
C = {
 "FRA":{"name_fr":"France","name_en":"France","region":"Europe de l'Ouest","income_group":"high","prep":"en","pop":66000000,
   "age":[0.05,0.115,0.06,0.18,0.185,0.19,0.14,0.08],"femOff":0,"settle":{"grande":0.30,"ville":0.51,"rural":0.19},
   "gpct":[58,72,83,90,96],"edu":{"aucune":0.03,"primaire":0.11,"secondaire":0.44,"superieur":0.42},"eduGender":False,
   "schoolIn":0.99,"health":"rich","elec":1.0,"net":0.93,"eau":1.0},
 "AUT":{"name_fr":"Autriche","name_en":"Austria","region":"Europe centrale","income_group":"high","prep":"en","pop":9100000,
   "age":[0.045,0.10,0.055,0.185,0.20,0.20,0.145,0.07],"femOff":0,"settle":{"grande":0.28,"ville":0.31,"rural":0.41},
   "gpct":[60,74,84,91,97],"edu":{"aucune":0.02,"primaire":0.10,"secondaire":0.55,"superieur":0.33},"eduGender":False,
   "schoolIn":0.99,"health":"rich","elec":1.0,"net":0.90,"eau":1.0},
 "USA":{"name_fr":"Etats-Unis","name_en":"United States","region":"Amerique du Nord","income_group":"high","prep":"aux","pop":345000000,
   "age":[0.055,0.12,0.065,0.20,0.19,0.19,0.13,0.05],"femOff":0,"settle":{"grande":0.45,"ville":0.38,"rural":0.17},
   "gpct":[55,72,84,92,98],"edu":{"aucune":0.02,"primaire":0.06,"secondaire":0.45,"superieur":0.47},"eduGender":False,
   "schoolIn":0.99,"health":"rich","elec":1.0,"net":0.92,"eau":0.99},
 "BRA":{"name_fr":"Bresil","name_en":"Brazil","region":"Amerique du Sud","income_group":"upper_middle","prep":"au","pop":212000000,
   "age":[0.06,0.14,0.08,0.24,0.21,0.16,0.08,0.03],"femOff":0,"settle":{"grande":0.45,"ville":0.42,"rural":0.13},
   "gpct":[25,40,55,70,88],"edu":{"aucune":0.08,"primaire":0.28,"secondaire":0.44,"superieur":0.20},"eduGender":False,
   "schoolIn":0.96,"health":"mid","elec":1.0,"net":0.84,"eau":0.98},
 "IND":{"name_fr":"Inde","name_en":"India","region":"Asie du Sud","income_group":"lower_middle","prep":"en","pop":1450000000,
   "age":[0.08,0.17,0.09,0.26,0.20,0.12,0.06,0.02],"femOff":-0.025,"settle":{"grande":0.15,"ville":0.21,"rural":0.64},
   "gpct":[18,30,42,55,72],"edu":{"aucune":0.22,"primaire":0.24,"secondaire":0.36,"superieur":0.18},"eduGender":True,
   "schoolIn":0.90,"health":"mid","elec":0.99,"net":0.55,"eau":0.93},
 "CHN":{"name_fr":"Chine","name_en":"China","region":"Asie de l'Est","income_group":"upper_middle","prep":"en","pop":1410000000,
   "age":[0.05,0.11,0.06,0.21,0.22,0.20,0.11,0.04],"femOff":-0.03,"settle":{"grande":0.35,"ville":0.29,"rural":0.36},
   "gpct":[30,45,58,72,88],"edu":{"aucune":0.08,"primaire":0.22,"secondaire":0.48,"superieur":0.22},"eduGender":False,
   "schoolIn":0.98,"health":"mid","elec":1.0,"net":0.78,"eau":0.97},
 "NER":{"name_fr":"Niger","name_en":"Niger","region":"Afrique de l'Ouest","income_group":"low","prep":"au","pop":27000000,
   "age":[0.18,0.30,0.11,0.22,0.11,0.055,0.02,0.005],"femOff":0,"settle":{"grande":0.05,"ville":0.12,"rural":0.83},
   "gpct":[4,8,13,20,34],"edu":{"aucune":0.63,"primaire":0.22,"secondaire":0.11,"superieur":0.04},"eduGender":True,
   "schoolIn":0.55,"health":"low","elec":0.20,"net":0.20,"eau":0.56},
}

def w(name, obj):
    json.dump(obj, open(os.path.join(OUT,name),"w",encoding="utf-8"), ensure_ascii=False, indent=2)
    print("ecrit", name)

# 1. countries.json
w("countries.json", {"table":"countries","source_id":"wpp","year":2024,"rows":[
    {"iso3":k,"name_fr":c["name_fr"],"name_en":c["name_en"],"region":c["region"],
     "income_group":c["income_group"],"population":c["pop"],"prep":c["prep"],"coverage":"national"}
    for k,c in C.items()]})

# 2. age_sex.json (jointe resolue)
age_sex={}
for k,c in C.items():
    sh={}
    for i,a in enumerate(AGES):
        pf=clamp(FEMALE_BASE[i]+c["femOff"],0.02,0.98)
        sh[a+"|F"]=round(c["age"][i]*pf,6); sh[a+"|M"]=round(c["age"][i]*(1-pf),6)
    age_sex[k]={"shares":sh,"coverage":"national"}
w("age_sex.json", {"table":"age_sex","source_id":"wpp","year":2024,"data":age_sex})

# 3. settlement.json
w("settlement.json", {"table":"settlement","source_id":"wup","year":2024,
   "data":{k:{"shares":c["settle"],"coverage":"national"} for k,c in C.items()}})

# 4. income.json (position mondiale ; quintiles fixes a 0.2)
w("income.json", {"table":"income","source_id":"pip","year":2024,
   "data":{k:{"global_percentile":c["gpct"],"coverage":"national"} for k,c in C.items()}})

# 5. education.json (base + facteurs)
w("education.json", {"table":"education","source_id":"barrolee","year":2020,
   "attainment_base":{k:{"shares":c["edu"],"coverage":"national"} for k,c in C.items()},
   "child_enrollment":{k:{"in_school":c["schoolIn"]} for k,c in C.items()},
   "factors":{
     "rural_penalty":{"aucune":1.6,"primaire":1.15,"secondaire":0.7,"superieur":0.45},
     "income_prime":{"superieur":[0.4,0.7,1.0,1.4,1.9],"aucune":[1.9,1.35,1.0,0.7,0.45],
                     "secondaire":[0.70,0.85,1.00,1.15,1.30]},
     "gender_gap":{k:{"aucune":1.5,"superieur":0.65,"secondaire":0.85} for k,c in C.items() if c["eduGender"]}
   }})

# 6. health.json (base groupe + facteurs)
w("health.json", {"table":"health","source_id":"gbd","year":2023,
   "country_group":{k:c["health"] for k,c in C.items()},
   "severity_base_group":{
     "rich":{"bonne":0.62,"gene_legere":0.24,"incap_moderee":0.10,"incap_severe":0.04},
     "mid":{"bonne":0.55,"gene_legere":0.27,"incap_moderee":0.13,"incap_severe":0.05},
     "low":{"bonne":0.48,"gene_legere":0.29,"incap_moderee":0.16,"incap_severe":0.07}},
   "age_factors":{"boost":[0.6,0.5,0.6,0.8,1.0,1.5,2.4,3.5],"good":[1.2,1.25,1.25,1.15,1.0,0.8,0.55,0.4]},
   "income_penalty":[1.4,1.2,1.0,0.85,0.7],
   "mental":{"base":0.11,"rural_add":0.01,"lowinc_add":0.03,"min":0.06,"max":0.2}})

# 7. family.json (parametres de branches)
w("family.json", {"table":"family","source_id":"undesa_marriage","year":2023,
   "early_parenthood":[k for k,c in C.items() if ("Afrique" in c["region"] or k=="IND")],
   "params":{
     "young_early":{"celibataire":0.6,"couple":0.4},
     "young_late":{"celibataire":0.85,"couple":0.15},
     "elder_widow":{"F":0.55,"M":0.28},
     "mid_celibataire":{"a20_34":0.35,"a35_49":0.18,"a50_64":0.14},
     "mid_parent":{"a20_34":0.4,"a35_49":0.55,"a50_64":0.5},
     "early_cel_mult":0.55,"early_par_mult":1.3}})

# 8. living.json (probas d'acces, penalite rurale)
w("living.json", {"table":"living","source_id":"wdi","year":2023,"rural_penalty":0.75,
   "data":{k:{"electricite":c["elec"],"internet":c["net"],"eau":c["eau"],"coverage":"national"} for k,c in C.items()}})

# blob combine pour le fallback inline de l'app
seed={}
for n in ["countries","age_sex","settlement","income","education","health","family","living"]:
    seed[n]=json.load(open(os.path.join(OUT,n+".json"),encoding="utf-8"))
json.dump(seed, open(os.path.join(os.path.dirname(__file__),"seed_blob.json"),"w",encoding="utf-8"), ensure_ascii=False)
print("seed_blob.json ecrit")
