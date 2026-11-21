# Retail Profitability: Growth, Discounts and Returns

**SQL · Python · Customer cohorts · Unit economics · Data quality**

## Executive summary
This end-to-end portfolio investigates a fictional Nigerian online retailer selling Fashion, Electronics, Home and Beauty products. The business question is: **does sales growth translate into contribution after discounts, returns and fulfilment costs?** The audience is the commercial director, merchandising manager and customer operations team.

All records and prices are synthetic. Patterns are plausible simulation assumptions, not estimates of real Nigerian retail performance. No real personal information is used.

## Findings calculated from the cleaned data
- Net merchandise revenue: **NGN 1,333,719,402**, after discounts and observed refunds.
- Contribution: **NGN 381,317,765**; contribution margin **28.1%** of net merchandise revenue plus shipping fees.
- Unit return rate: **11.0%**. Fashion has the highest category rate at **18.8%**.
- November contribution margin is **11.5%**, versus **30.7%** across other months. This comparison is descriptive, not the causal effect of discounts.
- On-time delivery among delivered orders: **78.1%**. Cancelled orders are excluded from this metric and must be monitored separately.

## Dataset
Sales cover January 2024–December 2025. Return observation extends to February 15, 2026, allowing all generated 30-day return windows to mature. Dimensions contain 6,000 fictional customers and 120 products. One order contains one to four unique product lines; customers may make repeat purchases. One return event per line may return some or all units. Cancelled orders retain their booked basket but contribute no sales, refunds, payment or fulfilment costs in the model.

| Table/stage | Rows |
|---|---:|
| raw_orders | 25,150 |
| orders_normalized | 25,000 |
| orders | 24,930 |
| raw_order_items | 44,196 |
| order_items | 44,061 |
| raw_returns | 5,159 |
| returns | 5,142 |
| quarantine_orders | 70 |

See [DATA_DICTIONARY.md](DATA_DICTIONARY.md) for every input column and derived economic measure.

## Relationships and grain
customers 1 → many orders; orders 1 → many order_items; products 1 → many order_items; order_items 1 → zero/one returns in this simulation. A separate order_economics table aggregates line economics before joining order fees, preventing basket joins from multiplying shipping and payment costs. Use order_item_id for line joins, never product_id alone.

## Simulation design
- Seed 271828 makes generation reproducible.
- Uneven customer purchase propensity and signup dates create repeat purchases and unequal cohort sizes.
- Rising demand, weekday effects and November/December peaks influence order timing.
- Product prices are right-skewed; categories have different cost ratios and return propensities.
- November promotions bring deeper discounts, a different category/channel mix and longer delivery times.
- Unit costs rise faster than selling prices under the scenario assumptions.
- Returns vary with category, discount depth and delivery duration. Return delays are right-skewed and limited to 30 days after delivery.
- Source faults include 150 exact duplicate orders, 300 missing channel values, 400 inconsistent status labels, 200 mixed-format order dates, 50 negative quantities and 20 unknown product IDs. These faults may overlap across orders.
- There are no arbitrary price errors: legitimate large baskets remain in the data. Outliers should be investigated, not automatically deleted.

## SQL cleaning and transformation
`pipeline.py` stages every raw CSV as text and checks numeric syntax before conversion. SQLite scripts then normalize dates/status, preserve missing channels as Unknown, deduplicate exact order copies, and quarantine entire orders containing invalid items. Their items and associated returns are also excluded from clean tables, with original records retained in raw tables. This avoids reporting a partial basket with the full order fulfilment cost. Quarantine exclusions are not assumed random.

`sql/01_clean.sql` performs cleaning; `sql/02_transform.sql` builds line and order economics; `sql/03_analysis.sql` provides seven named analytical queries; `sql/04_validation.sql` checks references, chronology, returns, cancellation rules, order join cardinality and arithmetic reconciliation. Unique indexes enforce dimension, order and line keys. Dataset-specific rules are not a general ingestion service for arbitrary company data.

## Metric definitions
Gross sales = quantity × transaction unit price. Discounts = gross sales × discount rate. Booked merchandise sales = gross sales − discounts. Refunds = returned quantity × discounted unit price. Net merchandise revenue = booked sales − refunds.

Contribution = net merchandise revenue + shipping fees − retained product cost − fulfilment cost − payment fees − return handling. Restockable returned units reverse their original unit cost; other returned goods remain a cost. Shipping fees and payment fees are assumed nonrefundable. Payment fees apply to booked merchandise sales plus shipping. This is contribution before advertising, salaries, rent, tax and inventory holding costs, **not net profit or channel ROI**.

Monthly metrics use the original order date and include later refunds. They describe mature order cohorts, not calendar cash flow or statutory revenue recognition. Unit return rate uses returned units / delivered units. Customer cohorts use first observed delivered purchase; activity is distinct purchasing customers divided by original cohort size, not continuous subscription retention. Future cohort cells remain blank.

## Explanatory charts

### Growth and margin tell different stories
![Growth and margin tell different stories](charts/01_growth_and_margin.png)
Shading marks November promotions. Monthly values attribute later refunds to the original order month.

### Where merchandise value becomes contribution
![Where merchandise value becomes contribution](charts/02_contribution_waterfall.png)
Product cost is net of restockable returns. Marketing, overhead, tax and inventory holding costs are excluded.

### Repeat purchasing by customer cohort
![Repeat purchasing by customer cohort](charts/03_customer_cohorts.png)
Each cell is distinct active customers / original cohort size. Blank cells are unobserved, not zero.

### Where returns concentrate
![Where returns concentrate](charts/04_category_returns.png)
Unit-weighted rates; baskets and return events are not interchangeable denominators.

### Discount depth and returns: compare within category
![Discount depth and returns: compare within category](charts/05_discount_return_heatmap.png)
Association only: promotion timing, product selection and customer mix also vary.

### How quickly do returns arrive?
![How quickly do returns arrive?](charts/06_return_lag_ecdf.png)
One return event per line in this simulation. Sales end Dec 2025; returns observed through Feb 15, 2026.

### Channel value and delivery reliability
![Channel value and delivery reliability](charts/07_channel_decision_matrix.png)
Bubble area represents delivered orders. Contribution excludes acquisition spend; this is not channel ROI.

## Recommended decisions
1. Review November promotion economics by product and basket, including fulfilment and return costs. Run a controlled test before attributing margin changes to discounts.
2. Investigate high-return categories through size guides, product descriptions and supplier quality reviews. Monitor refund value and restock recovery, not only event counts.
3. Improve delivery capacity during peaks; compare promise accuracy and contribution together.
4. Investigate missing channel attribution before allocating acquisition budgets. Add advertising expenditure before calculating channel ROI.
5. Review repeat-purchase cohorts with comparable observation windows. Do not interpret recent cohorts' unobserved months as churn.

## Reproduce the project
Python 3.10+ and SQLite (included with Python) are used. Extract the ZIP first. Open a terminal in the project folder containing requirements.txt:

```bash
python -m pip install -r requirements.txt
python pipeline.py
```

On Windows, `py` may replace `python`. You can double-click RUN_WINDOWS.bat instead. Existing raw CSVs are used. To regenerate the raw synthetic data explicitly, run `python generate_data.py` first. To regenerate only charts, findings and dashboard from the existing database, run `python analysis/analyze.py`. These commands overwrite generated outputs including README.md, so preserve personal edits separately.

## Repository contents
| Path | Purpose |
|---|---|
| data/raw/ | Five complete source CSVs |
| data/clean/ | Clean tables, quarantine list, order economics |
| sql/ | Staging schema, cleaning, transformation, analysis, validation |
| analysis/analyze.py | All chart and findings code |
| analysis/findings.md | Executive brief |
| charts/ | Seven explanatory PNGs |
| reports/ | SQL result CSVs and validation JSON |
| dashboard/index.html | Offline executive summary, using adjacent chart files |
| retail.sqlite | Ready-to-query database |
| generate_data.py | Seeded generator |
| pipeline.py | Reproducible workflow |

Upload this folder's contents to GitHub with README.md at the repository root. Keep chart paths intact. Do not upload .venv or __pycache__. The HTML dashboard is a static summary, not a Power BI or Tableau workbook; keep its parent project folders together when opening it locally.

## Limitations and next steps
This is synthetic, not calibrated company data. No causal conclusions are supported. Demand is not inventory-constrained; stockouts, exchanges, partial cancellations, multiple returns per line, customer addresses and supplier invoices are not modeled. Refunds are assumed approved and processed on return date. Restocking is valued at full original cost; real recoverable value may differ. All sales are modeled excluding tax and all costs are fictional NGN assumptions. A real extension would add inventory, acquisition spend, tax handling and cash-event dates. Descriptive point estimates are shown without statistical significance claims.

## Skills demonstrated
Relational modeling, SQL staging and cleaning, audit reconciliation, safe multi-table joins, contribution accounting, return-window maturity, customer cohort analysis, explanatory visualization, reproducibility and business communication.
