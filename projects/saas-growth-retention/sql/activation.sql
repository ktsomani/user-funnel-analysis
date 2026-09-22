-- Activation and paid conversion by segment
SELECT
  acquisition_channel,
  company_size,
  COUNT(*) AS signups,
  AVG(activated * 1.0) AS activation_rate,
  AVG(CASE WHEN activated = 1 THEN paid * 1.0 END) AS activated_to_paid_rate
FROM accounts
GROUP BY 1,2
ORDER BY signups DESC;
