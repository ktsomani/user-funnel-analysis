"""Reproduce the full portfolio project with Python 3.10+ (standard library only)."""
import csv
import json
import math
import random
import sqlite3
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STAGES = ['visit', 'view_product', 'add_to_cart', 'checkout', 'purchase']
COLS = ['visited_at', 'viewed_at', 'carted_at', 'checked_out_at', 'purchased_at']


def write_csv(path, rows, fields=None):
    with path.open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=fields or list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def generate():
    rng = random.Random(42)
    sessions, events = [], []
    def event(sid, name, t, value=0):
        events.append(dict(event_id=f'E{len(events)+1:07}', session_id=sid,
                           event_name=name, event_time=t.isoformat()+'Z', revenue=value))
    for i in range(12000):
        sid = f'S{i+1:05}'
        day = rng.randrange(90)
        t = datetime(2026, 1, 1) + timedelta(days=day, seconds=rng.randrange(84000))
        device = rng.choices(['Mobile', 'Desktop', 'Tablet'], [60, 35, 5])[0]
        channel = rng.choices(['Organic', 'Paid Search', 'Social', 'Email'], [35, 30, 25, 10])[0]
        sessions.append(dict(session_id=sid, user_id=f'U{rng.randrange(1,8001):05}',
                             started_at=t.isoformat()+'Z', device=device, channel=channel))
        event(sid, 'visit', t)
        # Deliberate tracking noise: purchase before the ordered funnel must be excluded.
        if i % 211 == 0:
            event(sid, 'purchase', t-timedelta(seconds=1), 25)
        probs = [0.80 if channel=='Email' else 0.71,
                 0.43 if channel=='Email' else (0.26 if channel=='Social' else 0.34),
                 0.70, 0.48 if device=='Mobile' else 0.72]
        for name, probability in zip(STAGES[1:], probs):
            if rng.random() > probability:
                break
            t += timedelta(seconds=rng.randrange(10,180))
            event(sid, name, t, round(rng.uniform(20,180),2) if name=='purchase' else 0)
            if name=='view_product' and i % 13 == 0:
                event(sid, name, t+timedelta(seconds=1))
    duplicates = [dict(e) for e in events[::137]]
    raw = events + duplicates + [dict(event_id='INVALID001',session_id='MISSING',
        event_name='visit',event_time='2026-01-01T00:00:00Z',revenue=0)]
    rng.shuffle(raw)
    write_csv(ROOT/'data/sessions.csv', sessions)
    write_csv(ROOT/'data/events_raw.csv', raw)
    return sessions, raw


def clean(sessions, raw):
    ids = {s['session_id'] for s in sessions}
    seen, valid, rejected, reasons = set(), [], [], Counter()
    for e in raw:
        reason = None
        if e['event_id'] in seen:
            reason = 'duplicate_event_id'
        elif e['session_id'] not in ids:
            reason = 'unknown_session'
        elif e['event_name'] not in STAGES:
            reason = 'unknown_event'
        else:
            try:
                datetime.fromisoformat(e['event_time'].replace('Z','+00:00'))
            except ValueError:
                reason = 'invalid_timestamp'
        seen.add(e['event_id'])
        if reason:
            rejected.append(dict(e, reason=reason))
            reasons[reason] += 1
        else:
            valid.append(e)
    valid.sort(key=lambda e:(e['session_id'],e['event_time'],e['event_id']))
    write_csv(ROOT/'data/events_clean.csv', valid)
    write_csv(ROOT/'data/events_rejected.csv', rejected)
    return valid, dict(raw_events=len(raw), clean_events=len(valid), rejected_events=len(rejected), reasons=dict(reasons))


def wilson(k,n):
    if not n:
        return [None,None]
    p,z=k/n,1.96
    center=(p+z*z/(2*n))/(1+z*z/n)
    half=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/(1+z*z/n)
    return [round(100*(center-half),2),round(100*(center+half),2)]


def summarize(rows):
    counts = [sum(r[c] is not None for r in rows) for c in COLS]
    return dict(visits=counts[0], purchases=counts[-1], counts=counts,
                conversion_pct=round(100*counts[-1]/counts[0],2) if counts[0] else None,
                ci95_pct=wilson(counts[-1],counts[0]))


def verify(db, sessions, valid, records):
    assert len({e['event_id'] for e in valid}) == len(valid)
    assert len(records)==len(sessions)
    # Independent procedural check of every SQL path, not just count monotonicity.
    by_session = {}
    for e in valid:
        by_session.setdefault(e['session_id'],[]).append(e)
    for row in records:
        previous=None
        for name,col in zip(STAGES,COLS):
            options=[e['event_time'] for e in by_session[row['session_id']]
                     if e['event_name']==name and (name=='visit' or previous is not None and e['event_time']>previous)]
            expected=min(options) if options else None
            assert row[col]==expected, (row['session_id'],col)
            previous=expected
    assert db.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
    return 'PASS: unique cleaned IDs; one row per session; all ordered SQL paths match independent Python traversal; SQLite integrity.'


def main():
    for name in ['data','results','dist']:
        (ROOT/name).mkdir(exist_ok=True)
    sessions, raw = generate()
    valid, quality = clean(sessions,raw)
    db=sqlite3.connect(ROOT/'data/funnel.sqlite')
    db.row_factory=sqlite3.Row
    db.executescript('''DROP TABLE IF EXISTS events; DROP TABLE IF EXISTS sessions;
      CREATE TABLE sessions(session_id TEXT PRIMARY KEY,user_id TEXT,started_at TEXT,device TEXT,channel TEXT);
      CREATE TABLE events(event_id TEXT PRIMARY KEY,session_id TEXT,event_name TEXT,event_time TEXT,revenue REAL,
      FOREIGN KEY(session_id) REFERENCES sessions(session_id));
      CREATE INDEX events_path ON events(session_id,event_name,event_time);''')
    db.execute('PRAGMA foreign_keys=ON')
    db.executemany('INSERT INTO sessions VALUES(:session_id,:user_id,:started_at,:device,:channel)',sessions)
    db.executemany('INSERT INTO events VALUES(:event_id,:session_id,:event_name,:event_time,:revenue)',valid)
    db.commit()
    db.executescript((ROOT/'sql/funnel.sql').read_text())
    records=[dict(r) for r in db.execute('SELECT * FROM session_funnel')]
    overall=summarize(records)
    funnel=[]
    for i,(stage,n) in enumerate(zip(STAGES,overall['counts'])):
        prev=overall['counts'][i-1] if i else n
        funnel.append(dict(stage=stage,sessions=n,step_conversion_pct=round(100*n/prev,2) if prev else None,
                           dropoff_sessions=prev-n,dropoff_pct=round(100*(prev-n)/prev,2) if prev else None))
    segments=[]
    for dim in ['device','channel']:
        for name in sorted({r[dim] for r in records}):
            segments.append(dict(dimension=dim,segment=name,**summarize([r for r in records if r[dim]==name])))
    cubes=[]
    for device in ['Mobile','Desktop','Tablet']:
        for channel in ['Organic','Paid Search','Social','Email']:
            for month in ['2026-01','2026-02','2026-03']:
                subset=[r for r in records if r['device']==device and r['channel']==channel and r['started_at'].startswith(month)]
                cubes.append(dict(device=device,channel=channel,month=month,**summarize(subset)))
    validation=verify(db,sessions,valid,records)
    payload=dict(overall=overall,cubes=cubes,segments=segments,quality=quality,stages=STAGES)
    write_csv(ROOT/'results/funnel.csv',funnel)
    write_csv(ROOT/'results/segments.csv',segments)
    write_csv(ROOT/'results/session_funnel.csv',records)
    (ROOT/'results/summary.json').write_text(json.dumps(payload,indent=2),encoding='utf-8')
    (ROOT/'results/validation.txt').write_text(validation,encoding='utf-8')
    template=(ROOT/'dashboard.html').read_text(encoding='utf-8')
    (ROOT/'dist/index.html').write_text(template.replace('__DATA__',json.dumps(payload)),encoding='utf-8')
    mobile=next(s for s in segments if s['segment']=='Mobile')
    desktop=next(s for s in segments if s['segment']=='Desktop')
    biggest=max(funnel[1:],key=lambda r:r['dropoff_pct'])
    report=f'''# Funnel analysis: findings and recommendations

**Simulated data, not evidence about a real business.** Seed 42; 12,000 sessions; January–March 2026.

## Results
- {overall['purchases']:,} ordered purchases / {overall['visits']:,} visits = **{overall['conversion_pct']}% session conversion**.
- Largest proportional loss: **{biggest['stage']}**, with {biggest['dropoff_pct']}% of eligible sessions dropping off ({biggest['dropoff_sessions']:,} sessions).
- Mobile conversion: {mobile['conversion_pct']}%; desktop: {desktop['conversion_pct']}%. These differences are intentionally built into the generator.
- Removed {quality['reasons']['duplicate_event_id']} duplicate records and {quality['reasons']['unknown_session']} orphan record. Out-of-order purchases remain in cleaned data but do not qualify for the ordered funnel.

## Three recommendations to investigate
1. Examine product-to-cart friction using product detail interactions, availability, and price/shipping visibility. Test a clearer product page. Primary metric: carted sessions / product-view sessions; guardrails: purchase conversion and return rate.
2. Inspect mobile checkout validation, payment errors, and load times. Test checkout simplification. Primary metric: ordered purchases / checkouts; guardrails: payment errors, order value, and refunds.
3. Review traffic intent and landing-page match by channel. Test channel-specific landing pages before changing spend. Channel rates alone cannot establish acquisition efficiency without spend, margin, and attribution data.

## Experiment design
Randomize eligible users before treatment and keep assignment stable across sessions. Predefine the hypothesis, primary metric, minimum detectable effect, power, and stopping rule. Estimate sample size from real baseline data; run through complete weekly cycles. Report intention-to-treat results with user-level uncertainty. Do not claim any recommendation has already caused a lift.

## Method and limitations
Unit = session, not unique user. A qualifying path requires strictly increasing timestamps in the same session: visit → view_product → add_to_cart → checkout → purchase. Repeated stage events count once using the earliest eligible event. Cross-session conversions and alternative paths are excluded. Equal timestamps do not satisfy ordering. Cohort month is session start, using UTC. The simulation includes complete sessions, so the final date is not right-censored.

Dashboard confidence intervals use the Wilson 95% binomial interval. They assume independent sessions; repeated users can violate this assumption, so treat these intervals as educational, not decision-grade. Use user-cluster bootstrap on real repeated-user data. Device/channel mixes may confound differences; segmentation is descriptive, not causal. Revenue is synthetic currency-neutral transaction value and is not used as a business KPI.

## Validation
{validation}
'''
    (ROOT/'results/findings.md').write_text(report,encoding='utf-8')
    db.close()
    print(json.dumps(dict(overall=overall,quality=quality,validation=validation),indent=2))


if __name__=='__main__':
    main()
