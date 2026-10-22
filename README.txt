WORKORA DATA ANALYTICS DASHBOARD PACK

All records are synthetic and intended only for learning. Build an interactive dashboard that combines acquisition, engagement, registration, regional demand, and customer-retention views. Document any cleaning, joins, assumptions, calculated fields, and excluded records. Do not present the data as real Workora business results.

Suggested relationships and keys:
- web_traffic.csv: SessionID is unique; Date supports time-series analysis.
- customer_churn.csv: CustomerID is unique; this raw file deliberately includes missing values, duplicates, and outliers.
- regional_market.csv: RegionID is unique; Latitude and Longitude support a map.
- checkout_ab_test.csv: VisitorID is unique; Variant and Converted support experiment analysis.
