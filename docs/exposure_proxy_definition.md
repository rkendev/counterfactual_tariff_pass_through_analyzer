## Firm Exposure Proxy Definition

For real tariff events, firm level exposure is proxied using public company disclosures.

A firm is considered exposed if its filings during the event year include explicit disclosure of sourcing, manufacturing, or component dependence on China for affected product categories.

Exposure is encoded as:

- exposed = 1
- not_exposed = 0

Optional refinement (if available without added complexity):

- exposed_low
- exposed_medium
- exposed_high

No attempt is made to estimate exact import values.

This proxy is chosen to minimize data friction and to align with sign based falsification logic.
