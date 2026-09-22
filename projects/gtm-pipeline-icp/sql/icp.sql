-- ICP segments: conversion, value and speed
SELECT
  company_size,
  industry,
  COUNT(*) AS leads,
  AVG(closed_won * 1.0) AS win_rate,
  AVG(CASE WHEN closed_won = 1 THEN acv END) AS avg_acv,
  AVG(CASE WHEN closed_won = 1 THEN sales_cycle_days END) AS avg_sales_cycle_days
FROM leads
GROUP BY 1,2
HAVING COUNT(*) >= 80
ORDER BY win_rate DESC, avg_acv DESC;
