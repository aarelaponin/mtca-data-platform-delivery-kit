-- Parameterized read queries for the debt API. Bind params; never string-build.
-- Generated 2026-06-17.

-- /api/debt/aged-balances
SELECT taxpayer_id, taxpayer_name, balance
FROM gold.mart_debt__aged_balances
WHERE ({{taxpayer_id}} IS NULL OR taxpayer_id = {{taxpayer_id}})
  AND ({{min_balance}} IS NULL OR balance >= {{min_balance}})
LIMIT {{limit}};
