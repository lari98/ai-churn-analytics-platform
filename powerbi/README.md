# 📊 Power BI Dashboard Setup Guide
## AI Churn Analytics Platform

### Prerequisites
- Power BI Desktop (latest)
- Power BI Premium P1 licence (for scheduled refresh + RLS)
- Azure SQL connection (Private Link endpoint)

### Setup Steps
1. Open Power BI Desktop
2. **Get Data → Azure → Azure SQL Database**
   - Server: `sql-churnanalytics-prod.database.windows.net`
   - Mode: **DirectQuery** for real-time tables (`fact_churn_scores`, `fact_anomalies`)
   - Mode: **Import** for dimension tables and historical (`dim_customers`, `dim_date`)
3. Import the DAX measures from `dax_measures.md`
4. Apply the layout from `dashboard_design.md`
5. Configure Row-Level Security (see below)
6. Publish to Power BI Service workspace: `ws-churn-analytics-prod`

### Row-Level Security (RLS)
```dax
-- bi-analyst role: no individual tokens
[customer_token] = "AGGREGATED"  -- always false → hides all rows

-- retention-manager role: own region only
[region] = USERPRINCIPALNAME()   -- requires UPN = region mapping table
```

### Scheduled Refresh
- DirectQuery tables: live (no refresh needed)
- Import tables: hourly via On-Premises Data Gateway → Azure SQL Private Link

### DAX measures: see `dax_measures.md`
### Layout spec: see `dashboard_design.md`
