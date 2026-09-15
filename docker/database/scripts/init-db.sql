-- Ensures the two app databases exist. Run automatically by the postgres
-- entrypoint for any *.sql file in /docker-entrypoint-initdb.d/ on first init
-- (empty data dir). Idempotent: some services set POSTGRES_DB=openftv, so that
-- database is already created at bootstrap -- guard against "already exists".
SELECT 'CREATE DATABASE openftv'
  WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'openftv')\gexec

SELECT 'CREATE DATABASE openftv_adl'
  WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'openftv_adl')\gexec
