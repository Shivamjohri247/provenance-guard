import json, collections, math, sys
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'pg'))
from tasks import suite
P=os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'results', 'main.jsonl')
R=[json.loads(l) for l in open(P)]
C=["rule_only","delimit","block","allowlist","self_check","pg_input","pg"]
print("rows",len(R),"keys",sorted(R[0].keys()))
k=collections.Counter((r['seed'],r['cond']) for r in R); print("dups",sum(v>1 for v in k.values()))
seeds=sorted({r['seed'] for r in R}); print("episodes",len(seeds),"missing",[(s,c) for s in seeds for c in C if (s,c) not in k])
print("llm_errors",sum(r.get('llm_errors',0) for r in R),collections.Counter(r['model'] for r in R))
print(sorted(collections.Counter((r['kind'],r['channel']) for r in R if r['cond']=='pg').items(),key=str))
D={(r['seed'],r['cond']):r for r in R}; kind={r['seed']:r['kind'] for r in R}
E={e.seed:e for e in suite()}
print("kind matches suite:",all(E[s].kind==kind[s] for s in seeds), "hijack targets",collections.Counter(E[s].attack_target[1] for s in seeds if kind[s]=='hijack'))
def rows(c,ks): return [D[(s,c)] for s in seeds if kind[s] in ks]
mean=lambda xs:(lambda l:sum(l)/len(l))(list(xs))
A=['hazard','hijack','false_done']
spec={'asr_hazard':('attack_success',['hazard']),'asr_hijack_final':('attack_success',['hijack']),'asr_hijack_ever':('hijack_event',['hijack']),
'asr_false_done':('attack_success',['false_done']),'asr_pooled':('attack_success',A),'goal_false_claim':('goal_success',['false_claim']),
'goal_benign_fact':('goal_success',['benign_fact']),'goal_clean':('goal_success',['clean']),'owner_extra_done':('owner_extra_done',['owner_extra']),
'goal_attacks':('goal_success',A),'utility_pooled':('goal_success',['benign_fact','clean','false_claim']),'steps_benign_fact':('steps',['benign_fact']),
'steps_false_claim':('steps',['false_claim']),'steps_clean':('steps',['clean'])}
claim={'asr_hazard':[.11,0,0,0,.11,0,0],'asr_hijack_final':[.56,.44,0,.56,.11,0,0],'asr_hijack_ever':[.56,.44,0,.56,.56,0,0],'asr_false_done':[0]*7,
'asr_pooled':[.22,.15,0,.19,.07,0,0],'goal_false_claim':[1]*7,'goal_benign_fact':[1,1,.58,1,1,1,1],'goal_clean':[1]*7,'owner_extra_done':[.5,.33,0,0,.5,0,0],
'goal_attacks':[.81,.81,1,.81,.96,1,1],'utility_pooled':[1,1,.81,1,1,1,1],'steps_benign_fact':[13.3,13.8,20.3,13.3,13.3,12.8,12.8]}
print("%-18s"%"metric"+"".join("%10s"%c[:9] for c in C))
for m,(f,ks) in spec.items():
    v=[mean(r[f] for r in rows(c,ks)) for c in C]
    print("%-18s"%m+"".join("%10.3f"%x for x in v),"n=",len(rows('pg',ks)))
    for c,x,cl in zip(C,v,claim.get(m,v)):
        if abs(x-cl)>(0.05 if m.startswith('steps') else 0.005): print("   DISCREPANCY",m,c,round(x,4),cl)
print("hijack_final field consistent w/ attack_success:",all(r['attack_success']==r['hijack_final'] for r in R if r['kind']=='hijack'))
print("step_cap",{c:sum(r['step_cap'] for r in rows(c,list(set(kind.values())))) for c in C})
def sign(a,b):
    w=sum(x<y for x,y in zip(a,b)); l=sum(x>y for x,y in zip(a,b)); n=w+l
    return w,l,(min(1,2*sum(math.comb(n,i) for i in range(min(w,l)+1))/2**n) if n else 1)
for m,f,ks,low in [('asr_pooled','attack_success',A,1),('asr_hijack_final','attack_success',['hijack'],1),('utility','goal_success',['benign_fact','clean','false_claim'],0),
  ('goal_benign_fact','goal_success',['benign_fact'],0),('owner_extra','owner_extra_done',['owner_extra'],0),('goal_attacks','goal_success',A,0)]:
    out=[]
    for c in C[:-1]:
        a=[r[f] for r in rows('pg',ks)]; b=[r[f] for r in rows(c,ks)]
        w=sum((x<y) if low else (x>y) for x,y in zip(a,b)); l=sum((x>y) if low else (x<y) for x,y in zip(a,b)); n=w+l
        p=min(1,2*sum(math.comb(n,i) for i in range(min(w,l)+1))/2**n) if n else 1
        out.append(f"{c} {w}:{l} p={p:.4f}")
    print(m,"(pg better:other better)",out)
