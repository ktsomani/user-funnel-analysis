-- Churn rate and monetization by ICP segment
SELECT
  company_size,
  industry,
  COUNT(*) AS paid_accounts,
  AVG(churned * 1.0) AS churn_rate,
  AVG(mrr) AS avg_mrr
FROM accounts
WHERE paid = 1
GROUP BY 1,2
HAVING COUNT(*) >= 20
ORDER BY churn_rate ASC, avg_mrr DESC;
