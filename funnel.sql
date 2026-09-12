-- Unit: session. Each stage requires a strictly later event than the prior stage.
-- The session table supplies dimensions; timestamps are ISO-8601 UTC.
DROP TABLE IF EXISTS session_funnel;
CREATE TABLE session_funnel AS
WITH visits AS (
  SELECT s.*, MIN(e.event_time) AS visited_at
  FROM sessions s LEFT JOIN events e ON s.session_id=e.session_id AND e.event_name='visit'
  GROUP BY s.session_id
), views AS (
  SELECT v.*, (SELECT MIN(event_time) FROM events e WHERE e.session_id=v.session_id
    AND event_name='view_product' AND event_time>v.visited_at) AS viewed_at FROM visits v
), carts AS (
  SELECT v.*, (SELECT MIN(event_time) FROM events e WHERE e.session_id=v.session_id
    AND event_name='add_to_cart' AND event_time>v.viewed_at) AS carted_at FROM views v
), checkouts AS (
  SELECT c.*, (SELECT MIN(event_time) FROM events e WHERE e.session_id=c.session_id
    AND event_name='checkout' AND event_time>c.carted_at) AS checked_out_at FROM carts c
)
SELECT c.*, (SELECT MIN(event_time) FROM events e WHERE e.session_id=c.session_id
  AND event_name='purchase' AND event_time>c.checked_out_at) AS purchased_at FROM checkouts c;

-- These nested counts exclude out-of-order and incomplete paths.
SELECT COUNT(visited_at) AS visits, COUNT(viewed_at) AS product_views,
       COUNT(carted_at) AS carts, COUNT(checked_out_at) AS checkouts,
       COUNT(purchased_at) AS purchases FROM session_funnel;
