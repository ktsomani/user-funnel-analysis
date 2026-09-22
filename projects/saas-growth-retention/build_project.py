"""Generate the synthetic SaaS growth/retention dataset and analytical outputs."""
from pathlib import Path
import json
import numpy as np
import pandas as pd

ROOT = Path(__file__).parent
for d in ["data","results"]:
    (ROOT/d).mkdir(exist_ok=True)

rng = np.random.default_rng(42)
n = 3500
plans = rng.choice(["Starter","Growth","Pro"], n, p=[.50,.34,.16])
sizes = rng.choice(["1-10","11-50","51-200","201+"], n, p=[.36,.34,.22,.08])
industries = rng.choice(["SaaS","E-commerce","FinTech","Services","HealthTech"], n, p=[.30,.22,.18,.18,.12])
channels = rng.choice(["Organic","Outbound","Paid Search","Referral","Partner"], n, p=[.26,.22,.24,.18,.10])
regions = rng.choice(["India","SEA","Europe","North America"], n, p=[.45,.18,.19,.18])
signup = pd.to_datetime("2025-01-01")+pd.to_timedelta(rng.integers(0,365,n),unit="D")

act_base={"Starter":.60,"Growth":.69,"Pro":.76}
size_bonus={"1-10":-.05,"11-50":.01,"51-200":.05,"201+":.07}
channel_bonus={"Organic":.04,"Outbound":.02,"Paid Search":-.04,"Referral":.06,"Partner":.05}
p_act=np.clip([act_base[p]+size_bonus[s]+channel_bonus[c] for p,s,c in zip(plans,sizes,channels)],.35,.90)
activated=rng.random(n)<p_act

paid_base={"Starter":.42,"Growth":.58,"Pro":.71}
p_paid=np.clip([paid_base[p]+(.05 if c=="Referral" else 0)+(.03 if c=="Outbound" else 0)-(.05 if c=="Paid Search" else 0) for p,c in zip(plans,channels)],.2,.9)
paid=activated & (rng.random(n)<p_paid)

churn_base={"Starter":.42,"Growth":.27,"Pro":.18}
size_churn={"1-10":.08,"11-50":.02,"51-200":-.04,"201+":-.07}
channel_churn={"Organic":-.04,"Outbound":-.02,"Paid Search":.07,"Referral":-.05,"Partner":-.04}
p_churn=np.clip([churn_base[p]+size_churn[s]+channel_churn[c] for p,s,c in zip(plans,sizes,channels)],.05,.70)
churned=paid & (rng.random(n)<p_churn)

paid_date = signup + pd.to_timedelta(rng.integers(7,31,n),unit="D")
churn_date = paid_date + pd.to_timedelta(rng.integers(30,240,n),unit="D")
feature=np.clip(rng.beta(2.2,2.0,n)+np.where(paid & ~churned,.10,0)-np.where(churned,.06,0),0,1)
mrr_base={"Starter":39,"Growth":99,"Pro":249}
mrr=np.array([mrr_base[p] for p in plans],float)*np.where(sizes=="201+",1.5,np.where(sizes=="51-200",1.2,1.0))*paid

df=pd.DataFrame({
    "account_id":np.arange(1,n+1),"signup_date":signup.date,"plan":plans,"company_size":sizes,
    "industry":industries,"acquisition_channel":channels,"region":regions,
    "activated":activated.astype(int),"paid":paid.astype(int),"churned":churned.astype(int),
    "paid_date":paid_date.date,"churn_date":pd.Series(churn_date.date).where(churned),
    "feature_adoption_score":np.round(feature,3),"mrr":np.round(mrr,2)
})
df.to_csv(ROOT/"data"/"accounts.csv",index=False)

paid_df=df[df.paid==1].copy()
segments=paid_df.groupby(["company_size","acquisition_channel"]).agg(
    paid_accounts=("account_id","count"),churn_rate=("churned","mean"),
    avg_mrr=("mrr","mean"),avg_feature_adoption=("feature_adoption_score","mean")
).reset_index()
segments.to_csv(ROOT/"results"/"segment_metrics.csv",index=False)

summary={
    "accounts":n,
    "activation_rate":round(float(df.activated.mean()),4),
    "activated_to_paid_rate":round(float(df.loc[df.activated==1,"paid"].mean()),4),
    "paid_accounts":int(len(paid_df)),
    "paid_churn_rate":round(float(paid_df.churned.mean()),4),
    "mrr":round(float(paid_df.mrr.sum()),2)
}
(ROOT/"results"/"summary.json").write_text(json.dumps(summary,indent=2))
print(json.dumps(summary,indent=2))
