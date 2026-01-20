CREATE TABLE IF NOT EXISTS observed_margin_sign (
  event_id TEXT NOT NULL,
  firm_id TEXT NOT NULL,
  margin_change_sign INT NOT NULL CHECK (margin_change_sign IN (-1, 0, 1)),
  PRIMARY KEY (event_id, firm_id)
);
