#!/usr/bin/env python3
"""Complete frozen exploratory battery. No edits to original data."""
from pathlib import Path
import json,hashlib,itertools,warnings
from collections import Counter,defaultdict
import numpy as np
import pandas as pd
from scipy.special import expit
from scipy.optimize import minimize,brentq,linear_sum_assignment
from scipy.stats import chi2,binomtest
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import log_loss,brier_score_loss
W=Path(__file__).resolve().parent; I=W/'inputs'; O=W/'analysis'; O.mkdir(exist_ok=True)
TAGS=['gemma4_12b_base','gemma4_26b_base','granite4_small_base','ling_mini_base','llama31_8b_base']; L='ABCD'

def dump(name,x): (O/name).write_text(json.dumps(x,indent=2,allow_nan=False))
def fit(X,y):
 X=np.asarray(X,float);y=np.asarray(y,float)
 def f(b):
  z=X@b;return np.logaddexp(0,z).sum()-y@z
 def g(b): return X.T@(expit(X@b)-y)
 r=minimize(f,np.zeros(X.shape[1]),jac=g,method='BFGS',options={'gtol':1e-8,'maxiter':300})
 return r.x,float(r.fun),bool(np.max(np.abs(g(r.x)))<1e-5)

def profile(X,y,j):
 b,nll,ok=fit(X,y);keep=np.arange(X.shape[1])!=j
 def target(v):
  def f(z):
   eta=X[:,keep]@z+X[:,j]*v;return np.logaddexp(0,eta).sum()-y@eta
  def g(z): return X[:,keep].T@(expit(X[:,keep]@z+X[:,j]*v)-y)
  r=minimize(f,b[keep],jac=g,method='BFGS',options={'maxiter':500,'gtol':1e-7})
  return 2*(r.fun-nll)-chi2.ppf(.95,1)
 ci=[]
 for sign in [-1,1]:
  step=.2
  while step<256 and target(b[j]+sign*step)<0:step*=2
  ci.append(float(brentq(target,*sorted([b[j],b[j]+sign*step]))) if step<256 else None)
 return {'beta':b.tolist(),'profile_beta95':ci,'OR':float(np.exp(b[j])) if abs(b[j])<700 else None,'OR95':[float(np.exp(v)) if v is not None and abs(v)<700 else None for v in ci],'converged':ok,'nll':nll}

def nested(X0,X1,y,j,profiles=True):
 b0,l0,o0=fit(X0,y);b1,l1,o1=fit(X1,y);lr=max(0,2*(l0-l1))
 res={'LR':lr,'p':float(chi2.sf(lr,X1.shape[1]-X0.shape[1])),'converged':o0 and o1}
 if profiles:res.update(profile(X1,y,j))
 return res

def cv(X,y):
 pred=[]
 for k in range(len(y)):
  train=np.arange(len(y))!=k
  m=make_pipeline(StandardScaler(),LogisticRegression(C=1,solver='lbfgs',max_iter=1000))
  m.fit(X[train],y[train]);pred.append(m.predict_proba(X[k:k+1])[0,1])
 return np.array(pred)

def feature(q):
 # n items x n models x 4 canonical options
 c=q.max(axis=2).mean(axis=1)
 a=np.mean([np.sum(q[:,j]*q[:,k],axis=1) for j,k in itertools.combinations(range(q.shape[1]),2)],axis=0)
 return c,a

def decode(r):
 assert len(r['rotations'])==4 and {x['rotation'] for x in r['rotations']}==set(range(4))
 qs=[];ds=[];masses=[];missing=0
 for rot in sorted(r['rotations'],key=lambda x:x['rotation']):
  p=np.array([rot['probs'].get(l,0) for l in L],float)
  assert np.isfinite(p).all() and (p>=0).all() and p.sum()>0
  masses.append(float(p.sum()));missing+=sum(l not in rot['probs'] for l in L);p/=p.sum()
  shown=int(p.argmax()); canonical=L[(shown+rot['rotation'])%4]
  # rounding can tie probs; stored argmax may differ in ties only
  if rot.get('shown_letter'): assert p[L.index(rot['shown_letter'])]>=p.max()-1e-12
  if rot.get('shown_letter'): assert rot['canonical']==L[(L.index(rot['shown_letter'])+rot['rotation'])%4]
  qs.append(np.roll(p,rot['rotation']));ds.append(float(p.max()))
 return np.mean(qs,axis=0),np.mean(ds),min(masses),missing

def tests():
 sharp=np.array([.97,.01,.01,.01]); same=np.tile(sharp,(1,4,1));diff=np.stack([np.roll(sharp,k) for k in range(4)])[None]
 cs,aa=feature(same);cd,ab=feature(diff);assert np.allclose(cs,cd) and aa[0]>ab[0]+.8
 # correct rotation maps shown D with r=1 to canonical A; reverse is C
 assert np.roll([0,0,0,1],1).argmax()==0;assert np.roll([0,0,0,1],-1).argmax()!=0
 assert np.allclose(np.mean([np.roll(sharp,r) for r in range(4)],axis=0),.25)
 try:decode({'rotations':[{'rotation':r,'probs':{}} for r in range(4)]})
 except AssertionError:pass
 else:raise AssertionError('zero mass accepted')
 # calibration of logistic against an exactly symmetric null
 x=np.tile([-1,1],20);y=np.tile([0,0,1,1],10);X=np.c_[np.ones(40),x]
 assert abs(fit(X,y)[0][1])<1e-6
 dump('unit_checks.json',{'same_peak':float(cs[0]),'same_direction_A':float(aa[0]),'different_direction_A':float(ab[0]),'tests':5,'known_broken_mapping_rejected':True,'zero_mass_rejected':True})

def design_sim():
 rng=np.random.default_rng(21701);out=[]
 for n,base in [(81,.37),(48,.69)]:
  for effect in [.5,1.,1.5]:
   hits=0
   for _ in range(500):
    x=rng.normal(size=n);y=rng.binomial(1,expit(np.log(base/(1-base))+effect*x));X=np.c_[np.ones(n),x]
    b,l,ok=fit(X,y);_,l0,_=fit(X[:,:1],y);hits+=2*(l0-l)>chi2.ppf(.95,1)
   out.append({'n':n,'baseline':base,'standardized_log_OR':effect,'simulated_rejection_fraction':hits/500,'replicates':500})
 dump('design_sensitivity.json',out)

def bootstrap_diff(x,y,rng):
 a=x[y==1];b=x[y==0];ds=np.mean(rng.choice(a,(10000,len(a))),axis=1)-np.mean(rng.choice(b,(10000,len(b))),axis=1)
 return {'difference':float(a.mean()-b.mean()),'ci95':np.quantile(ds,[.025,.975]).tolist(),'mean_consensus':float(a.mean()),'mean_nonconsensus':float(b.mean())}

def main():
 tests();design_sim() # before accessing measured outcomes
 print('calibration and design simulation complete',flush=True)
 for r in json.loads((W/'input_manifest.json').read_text()):assert hashlib.sha256((W/r['copy']).read_bytes()).hexdigest()==r['sha256']
 items=json.loads((I/'battery_doxa.json').read_text())['items']; ids=[x['id'] for x in items];assert len(ids)==len(set(ids))==180
 sessions=defaultdict(list)
 for p in (I/'responses').glob('*.json'):
  s=json.loads(p.read_text());sessions[s['model']].append(s)
 assert len(sessions)==7 and all(len(v)==3 for v in sessions.values())
 def modal(ss,i):
  a=[s['answers'].get(str(i),'NR') for s in ss]; assert all(v in list(L)+['NR'] for v in a)
  c=Counter(v for v in a if v!='NR').most_common()
  return c[0][0] if c and (len(c)==1 or c[0][1]>c[1][1]) else 'NR'
 rows=[]
 for it in items:
  vs=[modal(s,it['id']) for s in sessions.values()];valid='NR' not in vs
  rows.append({'id':it['id'],'layer':it['layer'],'domain':it.get('domain',''),'valid':valid,'consensus':int(valid and len(set(vs))==1),'subject_modals':''.join(vs),'norm':int(it['layer']=='norm'),'preference':int(it['layer']=='preference')})
 df=pd.DataFrame(rows); q=np.zeros((180,5,4)); ds=np.zeros((180,5));quality=[]
 for j,tag in enumerate(TAGS):
  records=[]
  for suffix in ['', '_habitus']:records+=json.loads((I/'base_compare'/f'{tag}{suffix}.json').read_text())['items']
  rec={r['id']:r for r in records};assert len(rec)==len(records)==180 and set(rec)==set(ids)
  for k,i in enumerate(ids):
   q[k,j],ds[k,j],mass,missing=decode(rec[i]);quality.append({'tag':tag,'id':i,'min_letter_mass':mass,'missing_letter_entries':missing})
 assert np.allclose(q.sum(2),1)
 df['D']=ds.mean(1);df['C'],df['A']=feature(q);df.to_csv(O/'items.csv',index=False);pd.DataFrame(quality).to_csv(O/'probability_quality.csv',index=False)
 np.savez_compressed(O/'canonical_probabilities.npz',q=q,D_by_model=ds,ids=np.array(ids),tags=np.array(TAGS))
 valid=df[df.valid];hab=valid[valid.layer=='habitus'];npdf=valid[valid.layer!='habitus'];summary={}
 summary['counts']=valid.groupby('layer').consensus.agg(['count','sum']).to_dict('index');assert summary['counts']=={'habitus':{'count':81,'sum':30},'norm':{'count':28,'sum':24},'preference':{'count':20,'sum':9}}
 summary['probability_quality']={'min_letter_mass':min(r['min_letter_mass'] for r in quality),'missing_letter_entries':sum(r['missing_letter_entries'] for r in quality),'records':len(quality)}
 old={x['id'] for x in json.loads((I/'partA_doxa.json').read_text())['doxa_items']};a=hab.id.isin(old).to_numpy();b=hab.consensus.to_numpy();pe=a.mean()*b.mean()+(1-a.mean())*(1-b.mean());summary['H3_kappa']=(np.mean(a==b)-pe)/(1-pe)
 # continuous H2, predictors on interpretable scales
 y=npdf.consensus.to_numpy();d=(npdf.D.to_numpy()-.5)/.1;n=npdf.norm.to_numpy();X0=np.c_[np.ones(len(y)),d];X1=np.c_[X0,n]
 summary['H2_linear']=nested(X0,X1,y,2);summary['H2_quadratic']=nested(np.c_[X0,d*d],np.c_[X0,d*d,n],y,3)
 rng=np.random.default_rng(21702);summary['H2_matching']=[]
 ns=npdf[npdf.norm==1];ps=npdf[npdf.norm==0];dist=np.abs(ns.D.to_numpy()[:,None]-ps.D.to_numpy()[None,:])
 lo=max(ns.D.min(),ps.D.min());hi=min(ns.D.max(),ps.D.max());summary['common_support']={'range':[lo,hi],'norm_in_range':int(ns.D.between(lo,hi).sum()),'preference_in_range':int(ps.D.between(lo,hi).sum())}
 for cal in [.025,.05,.1]:
  # dummy unmatched cost=100, disallowed=10000, hence maximize valid matches first
  cost=np.c_[np.where(dist<=cal,dist,10000),np.full((len(ns),len(ns)),100.)];ii,jj=linear_sum_assignment(cost);pairs=[(i,j) for i,j in zip(ii,jj) if j<len(ps) and dist[i,j]<=cal]
  effects=np.array([int(ns.iloc[i].consensus)-int(ps.iloc[j].consensus) for i,j in pairs]);wins=int((effects==1).sum());loss=int((effects==-1).sum());boot=rng.choice(effects,(10000,len(effects))).mean(1)
  summary['H2_matching'].append({'caliper':cal,'n_pairs':len(pairs),'norm_only_consensus':wins,'pref_only_consensus':loss,'risk_difference':float(effects.mean()),'ci95':np.quantile(boot,[.025,.975]).tolist(),'exact_discordant_p':float(binomtest(wins,wins+loss,.5).pvalue) if wins+loss else 1.,'pairs':[[int(ns.iloc[i].id),int(ps.iloc[j].id),float(dist[i,j])] for i,j in pairs]})
 print('H2 complete',flush=True)
 summary['habitus']={}; hidx=hab.index.to_numpy();y=hab.consensus.to_numpy();A=hab.A.to_numpy();D=hab.D.to_numpy();C=hab.C.to_numpy()
 for name,x in [('D',D),('C',C),('A',A)]:summary['habitus'][name+'_difference']=bootstrap_diff(x,y,rng)
 cvrows=pd.DataFrame({'id':hab.id,'y':y})
 for base,x in [('D',D),('C',C)]:
  X0=np.c_[np.ones(len(y)),(x-.5)/.1];X1=np.c_[X0,(A-.25)/.1];summary['habitus'][base+'_plus_A']=nested(X0,X1,y,2)
  for extra in [False,True]:
   key=base+('_A' if extra else '');pred=cv(np.c_[x,A] if extra else x[:,None],y);cvrows[key]=pred
   summary['habitus'][key+'_cv']={'Brier':float(brier_score_loss(y,pred)),'log_loss':float(log_loss(y,pred))}
 summary['family_sensitivity']={}
 for name,idx in [('no_Gemma',[2,3,4]),('no_IBM',[0,1,3,4]),('no_Ling',[0,1,2,4]),('no_Meta',[0,1,2,3])]:
  c,a=feature(q[:,idx,:]);d=ds[:,idx].mean(1);xx=d[hidx];aa=a[hidx];X0=np.c_[np.ones(len(y)),(xx-.5)/.1];X1=np.c_[X0,(aa-.25)/.1]
  res=nested(X0,X1,y,2);res['A_difference']=bootstrap_diff(aa,y,rng)
  for base,x in [('D',xx),('C',c[hidx])]:
   p0=cv(x[:,None],y);p1=cv(np.c_[x,aa],y)
   res[base+'_cv']={'Brier_base':float(brier_score_loss(y,p0)),'Brier_augmented':float(brier_score_loss(y,p1)),'log_loss_base':float(log_loss(y,p0)),'log_loss_augmented':float(log_loss(y,p1))}
  summary['family_sensitivity'][name]=res
 cvrows.to_csv(O/'leave_one_out_predictions.csv',index=False)
 av=valid.A.to_numpy();dv=valid.D.to_numpy();yv=valid.consensus.to_numpy();X0=np.c_[np.ones(len(yv)),(dv-.5)/.1,valid.norm,valid.preference];summary['all_items_A']=nested(X0,np.c_[X0,(av-.25)/.1],yv,4)
 print('models and leave-one-out complete',flush=True)
 # independent per-item/model option permutations, preserving q peaks and entropy
 null=[];hq=q[hidx];X0=np.c_[np.ones(len(y)),(D-.5)/.1];_,ll0,_=fit(X0,y)
 observed_diff=summary['habitus']['A_difference']['difference'];observed_lr=summary['habitus']['D_plus_A']['LR']
 for k in range(1000):
  order=np.argsort(rng.random(hq.shape),axis=2);sh=np.take_along_axis(hq,order,axis=2);assert np.allclose(hq.max(2),sh.max(2))
  _,aa=feature(sh);_,ll,ok=fit(np.c_[X0,(aa-.25)/.1],y);null.append([float(aa[y==1].mean()-aa[y==0].mean()),max(0,2*(ll0-ll))])
 null=np.array(null);pd.DataFrame(null,columns=['A_difference','increment_LR']).to_csv(O/'permutation_null.csv',index=False)
 summary['negative_control']={'n':1000,'direction_difference_p_two_sided':float((1+(np.abs(null[:,0])>=abs(observed_diff)).sum())/1001),'increment_LR_p':float((1+(null[:,1]>=observed_lr).sum())/1001),'null_difference95':np.quantile(null[:,0],[.025,.975]).tolist()}
 pvals=[summary['H2_linear']['p'],summary['habitus']['D_plus_A']['p']];order=np.argsort(pvals);adj=np.zeros(2);running=0
 for rank,k in enumerate(order):running=max(running,(2-rank)*pvals[k]);adj[k]=min(1,running)
 summary['holm_two_primary']={'H2_continuous':float(adj[0]),'habitus_direction':float(adj[1])}
 dump('results.json',summary);print(json.dumps(summary,indent=2),flush=True)
if __name__=='__main__':main()
