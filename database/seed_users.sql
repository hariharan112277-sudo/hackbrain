-- Track A Stage 2 — Demo user seed (bcrypt password hashes)
-- Passwords (plain, for local demo only):
--   admin@iob.demo    / admin123
--   engineer@iob.demo / engineer123
--   operator@iob.demo / operator123
--
-- Hashes generated with:
--   from passlib.context import CryptContext
--   pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
--   pwd_context.hash("<password>")

INSERT INTO users (email, password_hash, full_name, role) VALUES
('admin@iob.demo', '$2b$12$uDL4LvtEXhJjyDLCAj2qluu2a7dC8ue4KF7xV00hCQvj0Maq5Xci2', 'Demo Admin', 'admin'),
('engineer@iob.demo', '$2b$12$hU97HqhZ8HuWv/DcnYv0i.u0mbkPShLCohl2OCQAM3dgzVw30C/T6', 'Demo Engineer', 'engineer'),
('operator@iob.demo', '$2b$12$rmj3uVs2IEqFQdOjL.zb6.SIkmfq0dyNZzFLd7/RZMmVytA7So/ta', 'Demo Operator', 'operator')
ON CONFLICT (email) DO UPDATE
  SET password_hash = EXCLUDED.password_hash,
      full_name     = EXCLUDED.full_name,
      role          = EXCLUDED.role;
