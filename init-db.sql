-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create admin user
INSERT INTO users (username, email, full_name, hashed_password, role, is_active)
VALUES (
  'admin',
  'admin@cyberlaw.gov',
  'System Administrator',
  -- Password: Admin@123 (bcrypt hash)
  '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW',
  'admin',
  true
) ON CONFLICT (username) DO NOTHING;

-- Create default editor
INSERT INTO users (username, email, full_name, hashed_password, role, is_active)
VALUES (
  'editor1',
  'editor@cyberlaw.gov',
  'Document Editor',
  -- Password: Editor@123
  '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW',
  'editor',
  true
) ON CONFLICT (username) DO NOTHING;