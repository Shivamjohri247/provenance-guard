"""Pre-registered replication analysis (replication/PREREG.md). Independent of pg/analyze.py."""
import json, os
from math import comb
from collections import Counter
R = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'results', '')
load = lambda p: [json.loads(l) for l in open(R + p)]
M, A = load('rep_main.jsonl'), load('rep_adaptive.jsonl')
I = {(r['seed'], r['cond']): r for r in M}
C = ['rule_only', 'delimit', 'block', 'allowlist', 'allowlist_arg', 'self_check', 'pg_input', 'pg']
assert len(M) == 480 and len(A) == 108 and len(I) == 480
seeds = sorted({r['seed'] for r in M}); assert seeds == list(range(9000, 9060))
kind = {s: I[(s, 'pg')]['kind'] for s in seeds}
print('composition', Counter(kind.values()))
def p2(x, n): return 1.0 if n == 0 else min(1.0, 2 * sum(comb(n, i) for i in range(min(x, n - x) + 1)) / 2 ** n)
def holm(ps):
    o = sorted(range(len(ps)), key=lambda i: ps[i]); adj = [0] * len(ps); run = 0
    for r, i in enumerate(o): run = max(run, min(1, (len(ps) - r) * ps[i])); adj[i] = run
    return adj
def sign(a, b, ks, f, lower_better):
    ss = [s for s in seeds if kind[s] in ks]
    better = sum(1 for s in ss if (I[(s, a)][f] < I[(s, b)][f]) == lower_better and I[(s, a)][f] != I[(s, b)][f])
    worse = sum(1 for s in ss if I[(s, a)][f] != I[(s, b)][f]) - better
    return len(ss), better, worse, p2(better, better + worse)
ATT = ['hazard', 'hijack', 'false_done']
prim = [('1 pooled attack pg_input<rule_only', 'pg_input', 'rule_only', ATT, 'attack_success', True),
        ('2 benign steps pg_input<block', 'pg_input', 'block', ['benign_fact'], 'steps', True),
        ('3 benign goal pg_input>block', 'pg_input', 'block', ['benign_fact'], 'goal_success', False)]
res = [sign(*p[1:]) for p in prim]; adj = holm([r[3] for r in res])
for p, r, h in zip(prim, res, adj): print('PRIMARY', p[0], 'n=%d better=%d worse=%d p=%.4g holm=%.4g' % (*r, h))
for f, ks in [('attack_success', ATT), ('goal_success', ['benign_fact']), ('steps', ['benign_fact'])]:
    print(f, '+'.join(ks), ' '.join('%s=%s' % (c, round(sum(I[(s, c)][f] or 0 for s in seeds if kind[s] in ks) / sum(kind[s] in ks for s in seeds), 3)) for c in C))
# secondary
def cnt(c, ks, f): rs = [I[(s, c)] for s in seeds if kind[s] in ks]; return sum(r[f] or 0 for r in rs), len(rs)
for name, ks, f in [('hazard', ['hazard'], 'attack_success'), ('hijack', ['hijack'], 'attack_success'), ('hijack_ever', ['hijack'], 'hijack_event'),
                    ('false_done', ['false_done'], 'attack_success'), ('job_att', ATT, 'goal_success'), ('fclaim', ['false_claim'], 'goal_success'),
                    ('clean', ['clean'], 'goal_success'), ('extra', ['owner_extra'], 'owner_extra_done'), ('extra_goal', ['owner_extra'], 'goal_success')]:
    print('SEC', name, ' '.join('%s=%d/%d' % (c, *cnt(c, ks, f)) for c in C))
for pgc in ['pg']:
    for name, ks, f, lb in [('pooled_att', ATT, 'attack_success', True), ('benign_goal', ['benign_fact'], 'goal_success', False), ('benign_steps', ['benign_fact'], 'steps', True)]:
        rs = [sign(pgc, b, ks, f, lb) for b in C[:6]]; h = holm([r[3] for r in rs])
        print('PGvs6', name, ' '.join('%s:%d:%d holm=%.3g' % (b, r[1], r[2], hh) for b, r, hh in zip(C[:6], rs, h)))
print('self_check vs rule_only final hijack', sign('self_check', 'rule_only', ['hijack'], 'hijack_final', True))
for c in C:
    rs = [r for r in M if r['cond'] == c]; print('stall', c, 'cap', sum(r['step_cap'] for r in rs), 'cap&fail', sum(r['step_cap'] and not r['goal_success'] for r in rs), 'blocked', sum(r['blocked'] for r in rs))
P = [r for r in M + A if r['cond'] == 'pg']; IA = {(r['seed'], r['cond']): r for r in A}
print('pg==pg_input traces', sum(r['trace'] == (I.get((r['seed'], 'pg_input')) or IA[(r['seed'], 'pg_input')])['trace'] for r in P), len(P), 'blocked', sum(r['blocked'] for r in P), 'rej', sum(r['check_rejects'] for r in P))
for c in ['rule_only', 'allowlist_arg', 'pg_input', 'pg']:
    for k in ['claim_hijack', 'claim_done', 'claim_flood']:
        rs = [r for r in A if r['cond'] == c and r['kind'] == k]
        print('ADAPT', c, k, len(rs), 'att', sum(r['attack_success'] or 0 for r in rs), 'hev', sum(r['hijack_event'] for r in rs), 'goal', sum(r['goal_success'] for r in rs), 'prem', sum(r['premature_done'] for r in rs), 'cap', sum(r['step_cap'] for r in rs))
print('errors', set(k for r in M + A for k in r if 'err' in k.lower()), 'parse_fail', sum(r.get('parse_fail', 0) for r in M + A), 'models', Counter(r['model'] for r in M + A))
# exploratory paired numbers quoted in the paper's replication section
def cp(k, n):
    from math import comb as C_
    cdf = lambda k, n, p: sum(C_(n, i) * p**i * (1 - p)**(n - i) for i in range(k + 1))
    def bis(f):
        lo, hi = 0.0, 1.0
        for _ in range(100):
            m = (lo + hi) / 2; lo, hi = (lo, m) if f(m) else (m, hi)
        return (lo + hi) / 2
    return (0 if k == 0 else bis(lambda p: 1 - cdf(k - 1, n, p) >= .025), 1 if k == n else bis(lambda p: cdf(k, n, p) <= .025))
print('CI rule_only pooled 5/27', cp(5, 27), 'pg_input 0/27', cp(0, 27), 'hijack 4/9', cp(4, 9), 'block benign 7/12', cp(7, 12))
print('job_att pg_input>allowlist_arg', sign('pg_input', 'allowlist_arg', ATT, 'goal_success', False))
print('owner extra rule_only>pg_input', sign('rule_only', 'pg_input', ['owner_extra'], 'owner_extra_done', False))
print('stalls (cap & >=10 refusals)', {c: [(kind[r['seed']], r['seed'], r['blocked'], r['goal_success']) for r in M if r['cond'] == c and r['step_cap'] and r['blocked'] >= 10] for c in ['allowlist', 'allowlist_arg']})
print('hijack self_check vs rule_only attack', sign('self_check', 'rule_only', ['hijack'], 'attack_success', True))
