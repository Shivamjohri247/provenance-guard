import os
import json, sys
from math import comb
def bcdf(k,n,p): return sum(comb(n,i)*p**i*(1-p)**(n-i) for i in range(k+1))
def bis(f,lo=0.0,hi=1.0):
    for _ in range(200):
        m=(lo+hi)/2
        if f(m): hi=m
        else: lo=m
    return (lo+hi)/2
class _B:
    def __init__(s,k,n): s.k,s.n=k,n
    @property
    def pvalue(s):
        n=s.n; m=min(s.k,n-s.k); return min(1.0,2*bcdf(m,n,.5))
def binomtest(k,n): return _B(k,n)
R=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','results','')
def load(p): return [json.loads(l) for l in open(R+p)]
M=load('main.jsonl')+load('ext_main.jsonl'); A=load('adaptive.jsonl'); V=load('v1_confounded/main.jsonl')
from collections import Counter
print(Counter((r['kind']) for r in M if r['cond']=='rule_only'), Counter(r['cond'] for r in M))
def idx(rows): return {(r['seed'],r['cond']):r for r in rows}
I=idx(M); IA=idx(A); IV=idx(V)
C=['rule_only','delimit','block','allowlist','allowlist_arg','self_check','pg_input','pg']
def cp(k,n):
    lo=0 if k==0 else bis(lambda p: 1-bcdf(k-1,n,p)>=.025)
    hi=1 if k==n else bis(lambda p: bcdf(k,n,p)<=.025); return f"[{lo:.3f},{hi:.3f}]"
def rows(rs,cond,kinds): return sorted([r for r in rs if r['cond']==cond and r['kind'] in kinds],key=lambda r:r['seed'])
ATT=['hazard','hijack','false_done']; UT=['benign_fact','false_claim','clean']
metrics={
 'hazard':(['hazard'],'attack_success'),'hijack':(['hijack'],'attack_success'),
 'hijack_ever':(['hijack'],'hijack_event'),'false_done':(['false_done'],'attack_success'),
 'all_att':(ATT,'attack_success'),'job_att':(ATT,'goal_success'),
 'benign':(['benign_fact'],'goal_success'),'fclaim':(['false_claim'],'goal_success'),'clean':(['clean'],'goal_success'),
 'utility':(UT,'goal_success'),'extra':(['owner_extra'],'owner_extra_done'),'extra_goal':(['owner_extra'],'goal_success')}
for m,(ks,f) in metrics.items():
    out=[]
    for c in C:
        rs=rows(M,c,ks); k=sum(r[f] for r in rs); out.append(f"{c}={k}/{len(rs)}{cp(k,len(rs)) if m in('all_att','utility','benign') else ''}")
    print(m,' '.join(out))
def ms(rs): return sum(r['steps'] for r in rs)/len(rs)
for c in C: print('steps',c,'benign %.2f'%ms(rows(M,c,['benign_fact'])),'fclaim %.2f'%ms(rows(M,c,['false_claim'])))
# sign tests
for pgc in ['pg_input','pg']:
  for m,(ks,f) in metrics.items():
    ps=[];det=[]
    for b in [c for c in C if c not in ('pg_input','pg')]:  # Holm family: the six baselines
        a=rows(M,pgc,ks); bb=rows(M,b,ks)
        x=sum(1 for u,v in zip(a,bb) if u[f]>v[f]); y=sum(1 for u,v in zip(a,bb) if u[f]<v[f])
        p=binomtest(x,x+y).pvalue if x+y else 1.0; ps.append(p); det.append((b,x,y))
    k=len(ps); o=sorted(range(k),key=lambda i:ps[i]); adj=[0]*k; run=0
    for r,i in enumerate(o): run=max(run,min(1,(k-r)*ps[i])); adj[i]=run
    print(pgc,m,' '.join(f"{b}:{x}:{y} p={ps[i]:.4f} holm={adj[i]:.3f}" for i,(b,x,y) in enumerate(det)))
# (b) pg_input == block on 27 attacks
print('b',all(I[(r['seed'],'pg_input')]['attack_success']==I[(r['seed'],'block')]['attack_success'] and I[(r['seed'],'pg_input')]['goal_success']==I[(r['seed'],'block')]['goal_success'] for r in rows(M,'block',ATT)))
# (c)
allr=[r for r in M+A if r['cond']=='pg']
print('c traces equal',sum(r['trace']==(I.get((r['seed'],'pg_input')) or IA[(r['seed'],'pg_input')])['trace'] for r in allr),len(allr),
  'pg blocked',sum(r['blocked'] for r in allr),'rejects',sum(r['check_rejects'] for r in allr))
# (d)
for c in ['allowlist','allowlist_arg']:
  for r in rows(M,c,['hijack','owner_extra']):
    if not r['goal_success'] or r['blocked']: print('d',c,r['kind'],r['seed'],'goal',r['goal_success'],'blocked',r['blocked'],'cap',r['step_cap'],'hev',r['hijack_event'])
# (e)
def find(rs,cond,s):
    return [(r['seed'],r['kind']) for r in rs if r['cond']==cond and any(s.lower() in t.lower() for t in r['trace'])]
print('e1',find(M,'rule_only','proceed with the updated plan')); print('e2',find(M,'rule_only','as per the urgent instruction'))
print('e3',find(M,'delimit','as instructed by the peer robot')); print('e4',[x for c in C for x in find(M,c,'may be false') ])
# (f)
for r in rows(M,'self_check',['hijack']): print('f',r['seed'],'ev',r['hijack_event'],'fin',r['hijack_final'],'goal',r['goal_success'],'cap',r['step_cap'],'rej',r['check_rejects'])
for r in rows(M,'rule_only',['hazard','hijack']): print('rule',r['kind'],r['seed'],r['attack_success'],r['hijack_event'],r['goal_success'])
# (g) adaptive
for c in ['rule_only','allowlist_arg','pg_input','pg']:
  for k in ['claim_hijack','claim_done','claim_flood']:
    rs=rows(A,c,[k]); print('g',c,k,'n',len(rs),'att',sum((r['attack_success'] or 0) for r in rs),'hev',sum(r['hijack_event'] for r in rs),'hfin',sum(r['hijack_final'] for r in rs),'goal',sum(r['goal_success'] for r in rs),'prem',sum(r['premature_done'] for r in rs),'cap',sum(r['step_cap'] for r in rs),'steps %.2f'%ms(rs),'blk',sum(r['blocked'] for r in rs))
  for r in rows(A,c,['claim_done']):
    if r['premature_done'] or r['step_cap'] or not r['goal_success']: print('  g2',c,r['seed'],'steps',r['steps'],'prem',r['premature_done'],'cap',r['step_cap'],'goal',r['goal_success'])
# v1
for c in C[:3]+C[3:4]+C[5:]:
    a=rows(V,c,ATT); b=rows(V,c,['benign_fact']); h=rows(V,c,['hijack'])
    print('v1',c,'att %d/%d=%.2f'%(sum(r['attack_success'] for r in a),len(a),sum(r['attack_success'] for r in a)/len(a)),'benign %.2f'%(sum(r['goal_success'] for r in b)/len(b)),'hij',sum(r['attack_success'] for r in h))
print('errors', set(k for r in M+A for k in r if 'err' in k.lower()), sum(r.get('parse_fail',0) for r in M+A))
