-- seed.sql
-- Baseline test data for the Restaurant API.
-- Applied by harness/reset_db.py after schema.sql.
-- Item id=5 (Mushroom Risotto) has available=0 — used by unavailable-item tests.

PRAGMA foreign_keys = ON;

-- ── Menu categories (ids 1-4) ─────────────────────────────────────────────────
INSERT INTO menu_categories (name) VALUES
    ('Starters'),
    ('Mains'),
    ('Desserts'),
    ('Drinks');

-- ── Menu items (ids 1-8; id=5 is unavailable) ────────────────────────────────
INSERT INTO menu_items (category_id, name, description, price_cents, available) VALUES
    (1, 'Garlic Bread',       'Toasted sourdough with roasted garlic butter',   499,  1),
    (1, 'Soup of the Day',    'Chef''s seasonal soup with crusty roll',          650,  1),
    (2, 'Grilled Salmon',     'Atlantic salmon with lemon butter sauce',        1850,  1),
    (2, 'Margherita Pizza',   'Classic tomato and mozzarella',                 1200,  1),
    (2, 'Mushroom Risotto',   'Creamy arborio rice with wild mushrooms',        1350,  0),
    (3, 'Chocolate Lava Cake','Warm chocolate cake with vanilla ice cream',      750,  1),
    (4, 'Still Water',        '500 ml mineral water',                           250,  1),
    (4, 'House Wine',         'Glass of red or white house wine',               850,  1);

-- ── Dining tables (ids 1-5) ───────────────────────────────────────────────────
INSERT INTO dining_tables (table_number, seats, status) VALUES
    ('T1', 2, 'available'),
    ('T2', 4, 'available'),
    ('T3', 4, 'available'),
    ('T4', 6, 'available'),
    ('T5', 8, 'available');

-- ── Seed customers (ids 1-2) ──────────────────────────────────────────────────
INSERT INTO customers (name, email, phone) VALUES
    ('Alice Johnson', 'alice@example.com', '+1-555-0101'),
    ('Bob Williams',  'bob@example.com',   '+1-555-0102');
