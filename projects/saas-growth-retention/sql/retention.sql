-- Retention proxy using churn status in the synthetic observation window
SELECT
  plan,
  acquisition_channel,
  COUNT(*) AS paid_accounts,
  1.0 - AVG(churned * 1.0) AS retained_share,
  AVG(feature_adoption_score) AS avg_feature_adoption
FROM accounts
WHERE paid = 1
GROUP BY 1,2
ORDER BY retained_share DESC;
