-- Run funnel.sql first. A conversion rate is purchases / eligible visits.
SELECT device, COUNT(visited_at) AS visits, COUNT(purchased_at) AS purchases,
       ROUND(100.0*COUNT(purchased_at)/NULLIF(COUNT(visited_at),0),2) AS conversion_pct,
       COUNT(checked_out_at) AS checkouts,
       ROUND(100.0*COUNT(purchased_at)/NULLIF(COUNT(checked_out_at),0),2) AS checkout_completion_pct
FROM session_funnel GROUP BY device;

SELECT channel, COUNT(visited_at) AS visits, COUNT(purchased_at) AS purchases,
       ROUND(100.0*COUNT(purchased_at)/NULLIF(COUNT(visited_at),0),2) AS conversion_pct
FROM session_funnel GROUP BY channel ORDER BY conversion_pct DESC;

SELECT SUBSTR(started_at,1,7) AS month, COUNT(visited_at) AS visits,
       COUNT(purchased_at) AS purchases,
       ROUND(100.0*COUNT(purchased_at)/NULLIF(COUNT(visited_at),0),2) AS conversion_pct
FROM session_funnel GROUP BY month ORDER BY month;
