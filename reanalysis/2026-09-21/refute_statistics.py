"""Post-hoc implementation refutation; no additional significance search."""
from pathlib import Path
import json,itertools
import numpy as np
import pandas as pd
from scipy.special import expit,xlogy
from scipy.optimize import minimize
from scipy.stats import chi2
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import maximum_bipartite_matching
W=Path(__file__).resolve().parent
D=pd.read_csv(W/'analysis/items.csv');R=json.loads((W/'analysis/results.json').read_text());out={}
H=D[D.valid & (D.layer=='habitus')];P=D[D.valid & (D.layer!='habitus')]
def nll(b,X,y):return np.logaddexp(0,X@b).sum()-y@(X@b)
# Check profile interval endpoints themselves, not just coefficient agreement.
for name,data,metric,added,ref in [('H2',P,'D','norm',R['H2_linear']),('H2_quad',P,'D','norm',R['H2_quadratic']),('D_A',H,'D','A',R['habitus']['D_plus_A']),('C_A',H,'C','A',R['habitus']['C_plus_A'])]:
 x=(data[metric].to_numpy()-.5)/.1;a=data[added].to_numpy();a=(a-.25)/.1 if added=='A' else a
 X=np.c_[np.ones(len(data)),x,x*x,a] if name=='H2_quad' else np.c_[np.ones(len(data)),x,a];y=data.consensus.to_numpy();b=np.array(ref['beta'])
 assert np.max(abs(X.T@(expit(X@b)-y)))<1e-5
 dev=[]
 for val in ref['profile_beta95']:
  assert val is not None
  def f(z):return nll(np.r_[z,val],X,y)
  rr=minimize(f,b[:-1],method='Nelder-Mead',options={'maxiter':10000,'xatol':1e-10,'fatol':1e-10})
  dev.append(2*(rr.fun-ref['nll']))
  assert abs(dev[-1]-chi2.ppf(.95,1))<1e-5
 out[name+'_profile_endpoint_deviances']=dev
# Independently reconstruct ridge CV with explicit training-only scaling and penalized Newton updates.
obs=pd.read_csv(W/'analysis/leave_one_out_predictions.csv').set_index('id').loc[H.id];y=H.consensus.to_numpy();errs={}
for key,cols in [('D',['D']),('D_A',['D','A']),('C',['C']),('C_A',['C','A'])]:
 x=H[cols].to_numpy();pred=[]
 for k in range(len(H)):
  use=np.arange(len(H))!=k;mu=x[use].mean(0);sd=x[use].std(0);X=np.c_[np.ones(use.sum()),(x[use]-mu)/sd];t=np.r_[1,(x[k]-mu)/sd];b=np.zeros(X.shape[1]);pen=np.diag([0]+[1]*len(cols))
  for _ in range(80):
   p=expit(X@b);g=X.T@(p-y[use])+pen@b;hes=X.T@((p*(1-p))[:,None]*X)+pen;step=np.linalg.solve(hes,g);b-=step
   if max(abs(step))<1e-10:break
  pred.append(expit(t@b))
 err=float(max(abs(np.array(pred)-obs[key].to_numpy())));assert err<.001;errs[key]=err
out['independent_CV_max_absolute_error']=errs
# Max cardinality independently of linear assignment costs.
a=P[P.norm==1];b=P[P.norm==0];dist=abs(a.D.to_numpy()[:,None]-b.D.to_numpy()[None,:])
for row in R['H2_matching']:
 maximum=maximum_bipartite_matching(csr_matrix(dist<=row['caliper']),perm_type='column')
 assert (maximum>=0).sum()==row['n_pairs']
out['maximum_matching_cardinality']=True
# Identity permutations keep concentration and entropy but alter cross-model dot products.
q=np.load(W/'analysis/canonical_probabilities.npz')['q'];rng=np.random.default_rng(21921);per=np.take_along_axis(q,np.argsort(rng.random(q.shape),axis=2),axis=2)
assert np.allclose(q.max(2),per.max(2)) and np.allclose(-xlogy(q,q).sum(2),-xlogy(per,per).sum(2))
out['control_preserves_concentration_entropy']=True
assert R['holm_two_primary']['H2_continuous']>.05 and R['holm_two_primary']['habitus_direction']>.05
out['no_primary_exploratory_rejection_at_005']=True
(W/'analysis/refutation_statistics.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
