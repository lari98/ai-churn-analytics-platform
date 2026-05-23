# 📊 Power BI DAX Measures
## AI Churn Analytics Platform — PL-300 Certified Implementations

---

## Page 1: Executive Overview

```dax
-- KPI: Monthly Churn Rate
Churn Rate % = 
VAR TotalCustomers = COUNTROWS('dim_customers')
VAR ChurnedCustomers = CALCULATE(
    COUNTROWS('fact_churn_scores'),
    'fact_churn_scores'[churn_label] = 1,
    DATESINPERIOD('dim_date'[date], LASTDATE('dim_date'[date]), -30, DAY)
)
RETURN DIVIDE(ChurnedCustomers, TotalCustomers, 0) * 100

-- KPI: Revenue at Risk (€)
Revenue at Risk EUR = 
SUMX(
    FILTER('fact_churn_scores', 'fact_churn_scores'[churn_probability] >= 0.55),
    'fact_churn_scores'[estimated_clv_eur] * 'fact_churn_scores'[churn_probability]
)

-- KPI: High Risk Customers Count
High Risk Customers = 
CALCULATE(
    COUNTROWS('fact_churn_scores'),
    'fact_churn_scores'[risk_level] IN {"HIGH", "CRITICAL"}
)

-- KPI: Churn Rate YoY Change
Churn Rate YoY Delta = 
VAR CurrentRate = [Churn Rate %]
VAR PriorRate = CALCULATE([Churn Rate %], SAMEPERIODLASTYEAR('dim_date'[date]))
RETURN CurrentRate - PriorRate

-- Trend Line: Churn Rate by Month
Monthly Churn Rate =
CALCULATE(
    DIVIDE(
        COUNTROWS(FILTER('fact_churn_scores', 'fact_churn_scores'[churn_label] = 1)),
        COUNTROWS('dim_customers'),
        0
    ) * 100,
    ALLEXCEPT('dim_date', 'dim_date'[year_month])
)

-- Model Confidence (avg)
Avg Model Confidence =
AVERAGE('fact_churn_scores'[confidence_score])

-- Churn Forecast (3-month linear projection)
Churn Forecast 3M =
VAR Slope = LINESTX('dim_date'[date_serial], [Monthly Churn Rate], 1)
RETURN [Churn Rate %] + Slope * 90
```

---

## Page 2: High-Risk Customers

```dax
-- Critical Risk Count
Critical Risk Count = 
CALCULATE(
    COUNTROWS('fact_churn_scores'),
    'fact_churn_scores'[risk_level] = "CRITICAL"
)

-- CLV-Weighted Risk Score
CLV Weighted Risk =
SUMX(
    'fact_churn_scores',
    'fact_churn_scores'[churn_probability] * 'fact_churn_scores'[estimated_clv_eur]
)

-- Top N Customers by Revenue at Risk (for table visual)
Top Risk Customers Revenue =
TOPN(
    100,
    'fact_churn_scores',
    'fact_churn_scores'[churn_probability] * 'fact_churn_scores'[estimated_clv_eur],
    DESC
)

-- Risk Distribution (for pie chart)
Risk Level % =
DIVIDE(
    COUNTROWS('fact_churn_scores'),
    CALCULATE(COUNTROWS('fact_churn_scores'), ALL('fact_churn_scores'[risk_level])),
    0
) * 100

-- Requires Human Review Count (GDPR Art. 22)
Requires Human Review =
CALCULATE(
    COUNTROWS('fact_churn_scores'),
    'fact_churn_scores'[requires_human_review] = TRUE()
)

-- Heatmap: Risk by Segment and Region
Risk by Segment Region =
CALCULATE(
    AVERAGE('fact_churn_scores'[churn_probability]),
    ALLEXCEPT(
        'fact_churn_scores',
        'dim_customers'[region],
        'dim_segments'[segment_name]
    )
)
```

---

## Page 3: Customer Segments

```dax
-- Segment Size
Segment Customer Count =
COUNTROWS('fact_segments')

-- Segment Revenue
Segment Monthly Revenue EUR =
SUMX(
    RELATEDTABLE('dim_customers'),
    'dim_customers'[monthly_charge_eur]
)

-- Segment Churn Risk
Segment Avg Churn Probability =
CALCULATE(
    AVERAGE('fact_churn_scores'[churn_probability]),
    USERELATIONSHIP('fact_segments'[customer_token], 'fact_churn_scores'[customer_token])
)

-- RFM Score Distribution
Avg RFM Score =
AVERAGE('fact_segments'[rfm_score])

-- CLV by Segment
Avg CLV by Segment EUR =
CALCULATE(
    AVERAGE('fact_churn_scores'[estimated_clv_eur]),
    ALLEXCEPT('dim_segments', 'dim_segments'[segment_name])
)

-- Segment Migration (customers who changed segment vs. last month)
Segment Migration Count =
CALCULATE(
    COUNTROWS('fact_segments'),
    'fact_segments'[segment_name] <> 'fact_segments'[previous_segment_name]
)
```

---

## Page 4: Anomaly Monitor

```dax
-- Total Anomalies (30 days)
Anomalies 30D =
CALCULATE(
    COUNTROWS('fact_anomalies'),
    DATESINPERIOD('dim_date'[date], LASTDATE('dim_date'[date]), -30, DAY),
    'fact_anomalies'[is_anomaly] = TRUE()
)

-- Critical Anomalies
Critical Anomalies =
CALCULATE(
    COUNTROWS('fact_anomalies'),
    'fact_anomalies'[severity] = "critical"
)

-- Anomaly Rate (% of all transactions)
Anomaly Rate % =
DIVIDE(
    CALCULATE(COUNTROWS('fact_anomalies'), 'fact_anomalies'[is_anomaly] = TRUE()),
    COUNTROWS('fact_anomalies'),
    0
) * 100

-- False Positive Rate
False Positive Rate % =
DIVIDE(
    CALCULATE(
        COUNTROWS('fact_anomalies'),
        'fact_anomalies'[is_anomaly] = TRUE(),
        'fact_anomalies'[confirmed_fraud] = FALSE()
    ),
    CALCULATE(COUNTROWS('fact_anomalies'), 'fact_anomalies'[is_anomaly] = TRUE()),
    0
) * 100

-- Anomaly Trend (daily)
Daily Anomaly Count =
CALCULATE(
    COUNTROWS('fact_anomalies'),
    'fact_anomalies'[is_anomaly] = TRUE(),
    ALLEXCEPT('dim_date', 'dim_date'[date])
)
```

---

## Page 5: Retention Tracker

```dax
-- Retention Campaign Success Rate
Retention Success Rate % =
DIVIDE(
    CALCULATE(
        COUNTROWS('fact_retention'),
        'fact_retention'[outcome] = "retained"
    ),
    COUNTROWS('fact_retention'),
    0
) * 100

-- Retention Campaign ROI
Retention ROI =
DIVIDE(
    SUMX('fact_retention', 'fact_retention'[clv_saved_eur]) -
    SUMX('fact_retention', 'fact_retention'[campaign_cost_eur]),
    SUMX('fact_retention', 'fact_retention'[campaign_cost_eur]),
    0
) * 100

-- CLV Saved by Retention
Total CLV Saved EUR =
CALCULATE(
    SUM('fact_retention'[clv_saved_eur]),
    'fact_retention'[outcome] = "retained"
)

-- Retention Funnel
Funnel Contacted =
COUNTROWS('fact_retention')

Funnel Engaged =
CALCULATE(COUNTROWS('fact_retention'), 'fact_retention'[engaged] = TRUE())

Funnel Retained =
CALCULATE(COUNTROWS('fact_retention'), 'fact_retention'[outcome] = "retained")

-- Best Performing Campaign Type
Best Campaign ROI =
MAXX(
    GROUPBY(
        'fact_retention',
        'fact_retention'[campaign_type],
        "ROI", [Retention ROI]
    ),
    [ROI]
)
```

---

## Page 6: AI Model Health

```dax
-- AUC-ROC Score
Model AUC ROC =
MAX('fact_model_metrics'[auc_roc])

-- F1 Score (latest)
Model F1 Score =
CALCULATE(
    LASTNONBLANK('fact_model_metrics'[f1_score], 1),
    ALLEXCEPT('fact_model_metrics', 'fact_model_metrics'[model_name])
)

-- Model Drift PSI
Model PSI Score =
CALCULATE(
    LASTNONBLANK('fact_model_metrics'[psi_score], 1),
    ALLEXCEPT('fact_model_metrics', 'fact_model_metrics'[model_name])
)

-- Drift Alert Flag
Drift Alert =
IF([Model PSI Score] >= 0.20, "⚠️ DRIFT DETECTED — Retrain Required", "✅ Stable")

-- AUC Trend (for line chart)
AUC Trend Over Time =
CALCULATE(
    AVERAGE('fact_model_metrics'[auc_roc]),
    ALLEXCEPT('dim_date', 'dim_date'[month_year])
)

-- Prediction Volume Today
Predictions Today =
CALCULATE(
    COUNTROWS('fact_churn_scores'),
    'dim_date'[date] = TODAY()
)

-- Confidence Distribution (histogram buckets)
Confidence Bucket =
SWITCH(
    TRUE(),
    'fact_churn_scores'[confidence_score] < 0.6, "Low (<60%)",
    'fact_churn_scores'[confidence_score] < 0.8, "Medium (60-80%)",
    "High (>80%)"
)
```

---

## Shared Calculated Columns

```dax
-- dim_customers: tenure_bucket
tenure_bucket_label = 
SWITCH(
    TRUE(),
    dim_customers[tenure_months] <= 6, "0-6 months",
    dim_customers[tenure_months] <= 12, "7-12 months",
    dim_customers[tenure_months] <= 24, "1-2 years",
    dim_customers[tenure_months] <= 48, "2-4 years",
    "4+ years"
)

-- fact_churn_scores: risk_color (for conditional formatting)
risk_color =
SWITCH(
    fact_churn_scores[risk_level],
    "LOW", "#22C55E",       -- green
    "MEDIUM", "#F59E0B",    -- amber
    "HIGH", "#EF4444",      -- red
    "CRITICAL", "#7C3AED"   -- purple
)
```
