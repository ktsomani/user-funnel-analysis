"""Generate the synthetic B2B SaaS GTM pipeline dataset and analytical outputs."""
from pathlib import Path
import json
import numpy as np
import pandas as pd

ROOT=Path(__file__).parent
for d in ["data","results"]:
    (ROOT/d).mkdir(exist_ok=True)

rng=np.random.default_rng(84)
n=8000
channels=rng.choice(["Founder Outbound","Sales Outbound","Organic","Paid Search","Referral","Partner"],n,p=[.10,.22,.22,.20,.16,.10])
sizes=rng.choice(["1-10","11-50","51-200","201+"],n,p=[.28,.36,.25,.11])
industries=rng.choice(["SaaS","E-commerce","FinTech","Services","HealthTech"],n,p=[.31,.21,.18,.18,.12])
personas=rng.choice(["Founder","Head of Sales","RevOps","Product","Finance"],n,p=[.22,.28,.24,.15,.11])
regions=rng.choice(["India","SEA","Europe","North America"],n,p=[.40,.17,.22,.21])
created=pd.to_datetime("2025-01-01")+pd.to_timedelta(rng.integers(0,365,n),unit="D")

mql_base={"Founder Outbound":.56,"Sales Outbound":.43,"Organic":.50,"Paid Search":.37,"Referral":.62,"Partner":.57}
size_bonus={"1-10":-.06,"11-50":0,"51-200":.08,"201+":.05}
mql=rng.random(n)<np.clip([mql_base[c]+size_bonus[s] for c,s in zip(channels,sizes)],.15,.85)
sql=mql & (rng.random(n)<np.array([.65 if p in ["Head of Sales","RevOps","Founder"] else .50 for p in personas]))
demo=sql & (rng.random(n)<np.array([.72 if c in ["Founder Outbound","Referral","Partner"] else .61 for c in channels]))
trial=demo & (rng.random(n)<np.array([.64 if s in ["51-200","201+"] else .55 for s in sizes]))

pwin=[]
for c,s,i in zip(channels,sizes,industries):
    p=.28 + (.12 if c=="Founder Outbound" else 0)+(.10 if c=="Referral" else 0)-(.05 if c=="Paid Search" else 0)+(.08 if s=="51-200" else 0)+(.05 if s=="201+" else 0)+(.04 if i=="SaaS" else 0)
    pwin.append(p)
won=trial & (rng.random(n)<np.clip(pwin,.08,.70))

cycle_base={"Founder Outbound":39,"Sales Outbound":52,"Organic":47,"Paid Search":58,"Referral":34,"Partner":41}
cycle=np.array([max(12,int(rng.normal(cycle_base[c],8))) if w else np.nan for c,w in zip(channels,won)])
acv_base={"1-10":3200,"11-50":7200,"51-200":16000,"201+":32000}
acv=np.array([round(max(1200,rng.normal(acv_base[s],acv_base[s]*.18)),0) if w else 0 for s,w in zip(sizes,won)])

df=pd.DataFrame({
    "lead_id":np.arange(1,n+1),"created_date":created.date,"channel":channels,"company_size":sizes,
    "industry":industries,"persona":personas,"region":regions,"mql":mql.astype(int),"sql":sql.astype(int),
    "demo":demo.astype(int),"trial":trial.astype(int),"closed_won":won.astype(int),
    "sales_cycle_days":cycle,"acv":acv
})
df.to_csv(ROOT/"data"/"leads.csv",index=False)

channel=df.groupby("channel").agg(
    leads=("lead_id","count"),wins=("closed_won","sum"),win_rate=("closed_won","mean"),
    avg_acv=("acv",lambda s:s[s>0].mean() if (s>0).any() else 0),
    avg_sales_cycle=("sales_cycle_days","mean")
).reset_index()
channel.to_csv(ROOT/"results"/"channel_performance.csv",index=False)

wins=df[df.closed_won==1]
summary={
    "leads":n,"wins":int(len(wins)),"overall_win_rate":round(float(df.closed_won.mean()),4),
    "avg_acv":round(float(wins.acv.mean()),2),"avg_sales_cycle_days":round(float(wins.sales_cycle_days.mean()),1),
    "closed_won_value":round(float(wins.acv.sum()),2)
}
(ROOT/"results"/"summary.json").write_text(json.dumps(summary,indent=2))
print(json.dumps(summary,indent=2))
