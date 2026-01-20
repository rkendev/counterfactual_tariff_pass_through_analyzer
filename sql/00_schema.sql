CREATE TABLE IF NOT EXISTS firm_hs_exposure (
  firm_id TEXT NOT NULL,
  hs_code TEXT NOT NULL,
  import_value_usd NUMERIC NOT NULL,
  PRIMARY KEY (firm_id, hs_code)
);

CREATE TABLE IF NOT EXISTS supplier_edges (
  buyer_firm_id TEXT NOT NULL,
  supplier_firm_id TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_edges_buyer ON supplier_edges (buyer_firm_id);
CREATE INDEX IF NOT EXISTS idx_edges_supplier ON supplier_edges (supplier_firm_id);
