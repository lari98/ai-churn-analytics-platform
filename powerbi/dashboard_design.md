# 📊 Power BI Dashboard Design Specification
## AI Churn Analytics Platform — PL-300 Enterprise Layout

**Data Source:** Azure SQL (DirectQuery) + Azure Data Lake Storage (Import)  
**Refresh:** DirectQuery tables: real-time | Import tables: hourly  
**Theme:** Corporate dark — #0F172A background, #3B82F6 primary, #EF4444 alert

---

## Dashboard Structure (6 Pages)

### Page 1: Executive Overview
**Layout:** 4 KPI cards (top) + 2 charts (middle) + summary table (bottom)

```
┌─────────────┬─────────────┬─────────────┬─────────────┐
│ Churn Rate  │ Revenue     │ High-Risk   │ Retention   │
│   8.4% ▼   │ at Risk     │ Customers   │ Rate        │
│ -1.2% MoM  │ €11.5M ▲   │ 3,240 ▲    │  57% ─     │
└─────────────┴─────────────┴─────────────┴─────────────┘
┌────────────────────────────┬───────────────────────────┐
│ Churn Rate Trend (12M)     │ Revenue at Risk by        │
│ [Line chart + forecast]    │ Segment [Stacked bar]     │
│ Actual ── Forecast ···     │ Champions│Loyal│At-Risk   │
└────────────────────────────┴───────────────────────────┘
┌─────────────────────────────────────────────────────────┐
│ Top 10 High-Risk Customers [Table — anonymised tokens] │
│ Token | Prob | Risk | CLV | Segment | Last Contact    │
│ [Conditional formatting: red=CRITICAL, amber=HIGH]     │
└─────────────────────────────────────────────────────────┘
```
**Filters:** Date range | Region | Contract type | Segment

---

### Page 2: High-Risk Customer Map
**Layout:** Scatter plot (main) + heatmap + drill-through table

```
┌──────────────────────────────────┬────────────────────┐
│ CLV vs Churn Probability         │ Risk by Segment    │
│ [Scatter: x=prob, y=CLV_EUR]     │ [Matrix heatmap]   │
│ Color: segment | Size: revenue   │ Rows: Segment      │
│ Bubble hover: token + features   │ Cols: Risk Level   │
│                                  │ Values: Count      │
└──────────────────────────────────┴────────────────────┘
┌──────────────────────────────────┬────────────────────┐
│ Risk Distribution by Region      │ Requires Human     │
│ [Choropleth map — DACH regions] │ Review (GDPR Art22)│
│ Color intensity = avg churn prob │ [Gauge: X / total] │
└──────────────────────────────────┴────────────────────┘
```
**Drill-through:** Click segment → Page 3 (Segment detail)

---

### Page 3: Customer Segments
**Layout:** Segment wheel + RFM matrix + profiles

```
┌──────────────┬──────────────────────────────────────┐
│ Segment      │ RFM Score Matrix                     │
│ Distribution │ [3D scatter: R/F/M axes]             │
│ [Donut chart]│ Color: segment | Click: filter table │
│ 8 segments   │                                       │
└──────────────┴──────────────────────────────────────┘
┌─────────────────────────────────────────────────────┐
│ Segment Profiles [Multi-row card]                   │
│ Champions: Avg CLV €2,400 | Churn 3% | Count 4,800 │
│ At Risk:   Avg CLV €950  | Churn 45% | Count 6,100 │
│ Cannot Lose: Avg CLV €3,200 | Churn 52% | Count 3.2K│
└─────────────────────────────────────────────────────┘
┌────────────────────┬────────────────────────────────┐
│ Segment Migration  │ CLV by Segment [Bar chart]     │
│ [Sankey diagram]   │ Sorted by avg CLV descending   │
│ Last month → This  │ Color: churn risk              │
└────────────────────┴────────────────────────────────┘
```

---

### Page 4: Anomaly Monitor
**Layout:** Alert header + timeline + severity breakdown

```
┌───────────┬───────────┬───────────┬───────────────────┐
│ Anomalies │ Critical  │ Anomaly   │ False Positive    │
│ (30d): 284│ Alerts: 12│ Rate: 1.2%│ Rate: 8.0%        │
└───────────┴───────────┴───────────┴───────────────────┘
┌─────────────────────────────────────────────────────────┐
│ Anomaly Timeline [Line chart — daily count]            │
│ By severity: Critical (red) | High (orange) | Med (yellow)│
│ Annotations: ★ = model retrain | ⚠ = threshold change │
└─────────────────────────────────────────────────────────┘
┌──────────────────────┬──────────────────────────────────┐
│ Anomaly Type         │ Recent Anomalies [Table]         │
│ Distribution [Pie]   │ ID | Type | Severity | Action   │
│ Amount | Location    │ Last 50 events, live refresh     │
│ Time | Velocity      │ [Conditional: critical = flash]  │
└──────────────────────┴──────────────────────────────────┘
```

---

### Page 5: Retention Campaign Tracker
**Layout:** Funnel + ROI gauge + campaign breakdown

```
┌─────────────────────────────────────────────────────────┐
│ Retention Funnel [Funnel chart]                        │
│ Targeted: 3,240 → Contacted: 2,890 → Engaged: 2,100  │
│ → Offer Accepted: 1,200 → Retained: 1,847 (57%)       │
└─────────────────────────────────────────────────────────┘
┌──────────────┬──────────────┬──────────────────────────┐
│ Campaign ROI │ CLV Saved    │ Campaign Type Performance │
│ [Gauge: 85%] │ [KPI: €4.1M] │ [Bar: retention rate by  │
│              │              │ type: call/email/loyalty] │
└──────────────┴──────────────┴──────────────────────────┘
┌─────────────────────────────────────────────────────────┐
│ Campaign History [Line] — Monthly retention rate trend │
│ Target line: 60% | Actual: colored by above/below      │
└─────────────────────────────────────────────────────────┘
```

---

### Page 6: AI Model Health
**Layout:** Model cards + drift monitor + performance history

```
┌──────────────┬──────────────┬──────────────────────────┐
│ Churn Model  │ Segmentation │ Anomaly Model            │
│ AUC: 0.872   │ Silhouette:  │ Precision: 0.847         │
│ F1: 0.801    │ 0.683        │ Recall: 0.779            │
│ PSI: 0.08 ✅ │ PSI: 0.05 ✅ │ PSI: 0.11 ✅             │
│ v1.3 Stable  │ v1.1 Stable  │ v2.1 Stable              │
└──────────────┴──────────────┴──────────────────────────┘
┌─────────────────────────────────────────────────────────┐
│ AUC Trend Over Time [Line — 6 months]                  │
│ Model version annotations (v1.0, v1.1, v1.2, v1.3)    │
│ Drift threshold line at 0.85                           │
└─────────────────────────────────────────────────────────┘
┌──────────────────────┬──────────────────────────────────┐
│ Confidence           │ Daily Prediction Volume          │
│ Distribution         │ [Column chart + 7-day rolling]  │
│ [Histogram: Low/     │ Avg: 8,420/day                  │
│ Med/High]            │ Trend: +2.1% WoW                │
└──────────────────────┴──────────────────────────────────┘
```

---

## Data Model (Star Schema)

```
                    ┌──────────────┐
                    │  dim_date    │
                    │  date (PK)   │
                    │  year, month │
                    └──────┬───────┘
                           │
┌──────────────┐    ┌──────▼───────┐    ┌──────────────┐
│dim_customers │    │fact_churn_   │    │dim_segments  │
│customer_token│◄───│scores        │───►│segment_id    │
│tenure_months │    │prediction_id │    │segment_name  │
│contract_type │    │churn_prob    │    │rfm_min_score │
│region        │    │risk_level    │    └──────────────┘
└──────────────┘    │confidence    │
                    │model_version │    ┌──────────────┐
                    └──────┬───────┘    │fact_anomalies│
                           │            │anomaly_id    │
                    ┌──────▼───────┐    │customer_token│
                    │fact_retention│    │severity      │
                    │plan_id       │    │anomaly_type  │
                    │campaign_type │    └──────────────┘
                    │outcome       │
                    │clv_saved_eur │
                    └──────────────┘
```

## Connection Settings

- **Azure SQL:** DirectQuery, Private Link endpoint
- **ADLS (Parquet):** Import mode, hourly refresh via Azure Data Gateway
- **Row-Level Security (RLS):**
  - `bi-analyst` role: aggregated data only, no individual tokens
  - `retention-manager` role: high-risk customers in their region
  - `exec` role: all pages, no filter restrictions
