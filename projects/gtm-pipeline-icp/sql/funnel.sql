-- CRM pipeline funnel
SELECT
  COUNT(*) AS leads,
  SUM(mql) AS mqls,
  SUM(sql) AS sqls,
  SUM(demo) AS demos,
  SUM(trial) AS trials,
  SUM(closed_won) AS wins
FROM leads;
