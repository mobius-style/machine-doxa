from pathlib import Path
import json,hashlib,itertools
import numpy as np
import pandas as pd
from scipy.special import expit
from scipy.stats import chi2,mannwhitneyu
W=Path(__file__).resolve().parent;df=pd.read_csv(W/'analysis/items.csv');r=json.loads((W/'analysis/results.json').read_text());checks={}
for row in json.loads((W/'input_manifest.json').read_text()):assert hashlib.sha256((W/row['copy']).read_bytes()).hexdigest()==row['sha256']
checks['inputs_byte_identical']=True
# independent probability extraction using explicit canonical indices rather than np.roll
q=[]
for tag in ['gemma4_12b_base','gemma4_26b_base','granite4_small_base','ling_mini_base','llama31_8b_base']:
 rec={}
 for suf in ['', '_habitus']:
  for x in json.loads((W/'inputs/base_compare'/f'{tag}{suf}.json').read_text())['items']:
   v=np.zeros(4)
   for rot in x['rotations']:
    total=sum(rot['probs'].values())
    for l,p in rot['probs'].items():v[('ABCD'.index(l)+rot['rotation'])%4]+=p/total/4
   rec[x['id']]=v
 q.append([rec[i] for i in df.id])
q=np.array(q).transpose(1,0,2);a=[]
for qi in q:
 a.append(sum(float(v@u) for v,u in itertools.combinations(qi,2))/10)
assert np.allclose(df.A,a,rtol=0,atol=1e-14);checks['independent_mapping_and_A']=True
# independent Newton-Raphson MLE

def newton(X,y):
 b=np.zeros(X.shape[1])
 for _ in range(100):
  p=expit(X@b);delta=np.linalg.solve(X.T@((p*(1-p))[:,None]*X),X.T@(y-p));b+=delta
  if np.max(abs(delta))<1e-10:break
 eta=X@b;return b,float(np.logaddexp(0,eta).sum()-y@eta)
for key,sub,xcols in [('H2_linear',df[df.valid & (df.layer!='habitus')],['D','norm']),('habitus',df[df.valid & (df.layer=='habitus')],['D','A'])]:
 y=sub.consensus.to_numpy();D=(sub.D.to_numpy()-.5)/.1;x=sub.norm.to_numpy() if key=='H2_linear' else (sub.A.to_numpy()-.25)/.1
 X=np.c_[np.ones(len(y)),D,x];b,ll=newton(X,y);_,l0=newton(X[:,:2],y);ref=r[key] if key=='H2_linear' else r['habitus']['D_plus_A']
 assert np.allclose(b,ref['beta'],atol=1e-6);assert abs(chi2.sf(2*(l0-ll),1)-ref['p'])<1e-7
checks['independent_logistic_estimates']=True
# registered H3 full 120 scope is .649, 81-item secondary is .711
old={x['id'] for x in json.loads((W/'inputs/partA_doxa.json').read_text())['doxa_items']};h=df[df.layer=='habitus'];u=h.id.isin(old).to_numpy();v=h.consensus.to_numpy();pe=u.mean()*v.mean()+(1-u.mean())*(1-v.mean());k=(np.mean(u==v)-pe)/(1-pe);assert abs(k-.649484536082474)<1e-12;checks['H3_full_scope']=k
legacy=json.loads((W/'analysis/replayed_original.json').read_text());reference=json.loads((W/'inputs/results_doxa.json').read_text());assert legacy==reference;checks['legacy_H1_H2_H3_exact_replay']=True
h=df[df.valid & (df.layer=='habitus')];p=mannwhitneyu(h[h.consensus==1].D,h[h.consensus==0].D,alternative='two-sided',method='asymptotic',use_continuity=False).pvalue;assert abs(p-.066)<.0001;checks['old_rank_p']=float(p)
for match in r['H2_matching']:
 pairs=match['pairs'];assert len({p[0] for p in pairs})==len(pairs)==len({p[1] for p in pairs});assert all(p[2]<=match['caliper'] for p in pairs)
checks['matching_unique_and_within_caliper']=True
pred=pd.read_csv(W/'analysis/leave_one_out_predictions.csv');assert len(pred)==81 and pred.id.nunique()==81;assert ((pred[['D','D_A','C','C_A']]>=0)&(pred[['D','D_A','C','C_A']]<=1)).all().all();checks['heldout_predictions_complete']=True
(W/'analysis/verification.json').write_text(json.dumps(checks,indent=2));print(json.dumps(checks,indent=2))
