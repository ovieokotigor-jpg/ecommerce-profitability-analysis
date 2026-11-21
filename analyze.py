"""Explanatory analysis from SQL-prepared tables; regenerates charts, dashboard, README."""
from pathlib import Path
import sqlite3,json,html
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter
P=Path(__file__).resolve().parents[1]
plt.rcParams.update({'font.family':'DejaVu Sans','axes.spines.top':False,'axes.spines.right':False,'axes.titleweight':'bold','axes.labelcolor':'#334155','text.color':'#142d45','axes.edgecolor':'#cbd5e1','figure.facecolor':'#f8fafc','axes.facecolor':'#f8fafc','savefig.facecolor':'#f8fafc','font.size':10})
TEAL='#087f8c';CORAL='#da6559';NAVY='#193b57';GOLD='#d59b32'
charts=[]
def finish(fig,name,title,note):
 fig.suptitle(title,x=.08,ha='left',fontsize=16,fontweight='bold');fig.text(.08,.025,note,fontsize=9,color='#64748b');fig.tight_layout(rect=[.03,.07,.98,.92]);fig.savefig(P/'charts'/name,dpi=160);plt.close(fig);charts.append((name,title,note))
def report(n):return pd.read_csv(P/'reports'/f'{n}.csv')
c=sqlite3.connect(P/'retail.sqlite'); e=pd.read_sql('SELECT * FROM order_economics',c);c.close()
m=report('monthly');cat=report('category');channel=report('channel');disc=report('discount_bands');co=report('cohort');lag=report('return_lag');prod=report('product_concentration')
# 1: Separate axes aligned by month avoid misleading dual-axis comparisons.
fig,ax=plt.subplots(2,1,figsize=(12,6),sharex=True);x=np.arange(len(m))
ax[0].plot(x,m.net_revenue/1e6,color=TEAL,lw=2.5,label='Net merchandise revenue');ax[0].plot(x,m.contribution/1e6,color=NAVY,lw=2.5,label='Contribution');ax[0].set_ylabel('NGN millions');ax[0].legend(frameon=False)
ax[1].plot(x,m.contribution_margin*100,color=CORAL,lw=2.5);ax[1].set_ylabel('Contribution margin (%)');ax[1].set_xticks(x[::2],m.month[::2],rotation=35,ha='right')
for a in ax:
 for ix,mon in enumerate(m.month):
  if mon.endswith('-11'):a.axvspan(ix-.45,ix+.45,color=GOLD,alpha=.15)
finish(fig,'01_growth_and_margin.png','Growth and margin tell different stories','Shading marks November promotions. Monthly values attribute later refunds to the original order month.')
# 2: Exact contribution bridge.
values=[e.gross_sales.sum(),-e.discount_value.sum(),-e.refunds.sum(),e.shipping_fee_ngn.sum(),-e.retained_cogs.sum(),-e.fulfilment_cost_ngn.sum(),-e.payment_fees.sum(),-e.return_handling.sum()]
labels=['Gross sales','Discounts','Refunds','Shipping\nfees','Net product\ncost','Fulfilment','Payment\nfees','Return\nhandling','Contribution'];fig,ax=plt.subplots(figsize=(12,6));total=0
for i,v in enumerate(values):
 ax.bar(i,v/1e6,bottom=total/1e6,color=TEAL if v>0 else CORAL,width=.68);total+=v
 ax.text(i,total/1e6+8,f'{v/1e6:+,.1f}',ha='center',fontsize=9)
assert abs(total-e.contribution.sum())<.01
ax.bar(8,total/1e6,color=NAVY,width=.68);ax.text(8,total/1e6+8,f'{total/1e6:,.1f}',ha='center');ax.set_xticks(range(9),labels,rotation=25,ha='right');ax.set_ylabel('NGN millions')
finish(fig,'02_contribution_waterfall.png','Where merchandise value becomes contribution','Product cost is net of restockable returns. Marketing, overhead, tax and inventory holding costs are excluded.')
# 3: Cohorts using first observed delivered purchase; future cells blank.
cohorts=sorted(co.cohort.unique());mat=np.full((len(cohorts),12),np.nan)
for i,k in enumerate(cohorts):
 n=co[(co.cohort==k)&(co.age_month==0)].active_customers.iloc[0];end=(2025-int(k[:4]))*12+12-int(k[5:])
 for j in range(min(11,end)+1):
  v=co[(co.cohort==k)&(co.age_month==j)].active_customers;mat[i,j]=(v.iloc[0] if len(v) else 0)/n
fig,ax=plt.subplots(figsize=(11,8));im=ax.imshow(mat,cmap='YlGnBu',vmin=0,vmax=1,aspect='auto')
for i in range(len(cohorts)):
 for j in range(12):
  if np.isfinite(mat[i,j]):ax.text(j,i,f'{mat[i,j]:.0%}',ha='center',va='center',fontsize=7,color='white' if mat[i,j]>.6 else NAVY)
ax.set_yticks(range(len(cohorts)),cohorts);ax.set_xticks(range(12));ax.set_xlabel('Months since first observed delivered purchase');fig.colorbar(im,ax=ax,label='Cohort active share')
finish(fig,'03_customer_cohorts.png','Repeat purchasing by customer cohort','Each cell is distinct active customers / original cohort size. Blank cells are unobserved, not zero.')
# 4: Category unit-return lollipop.
fig,ax=plt.subplots(figsize=(10,5));cat=cat.sort_values('unit_return_rate');y=np.arange(len(cat));ax.hlines(y,0,cat.unit_return_rate,color='#cbd5e1',lw=5);ax.scatter(cat.unit_return_rate,y,s=150,color=CORAL)
for i,(_,r) in enumerate(cat.iterrows()):ax.text(r.unit_return_rate+.005,i,f'{r.unit_return_rate:.1%} • {int(r.units):,} units',va='center')
ax.set_yticks(y,cat.category);ax.xaxis.set_major_formatter(PercentFormatter(1));ax.set_xlim(0,cat.unit_return_rate.max()*1.6);ax.set_xlabel('Returned units / delivered units')
finish(fig,'04_category_returns.png','Where returns concentrate','Unit-weighted rates; baskets and return events are not interchangeable denominators.')
# 5: Promotion exposure x category matrix.
bands=['0%','1–10%','11–20%','21–30%'];v=disc.pivot(index='category',columns='discount_band',values='return_rate').reindex(columns=bands);n=disc.pivot(index='category',columns='discount_band',values='units').reindex(columns=bands)
fig,ax=plt.subplots(figsize=(10,5));im=ax.imshow(v,cmap='YlOrRd',vmin=0,vmax=max(.3,float(v.max().max())),aspect='auto')
for i in range(len(v)):
 for j in range(4):ax.text(j,i,f'{v.iloc[i,j]:.1%}\n{int(n.iloc[i,j]):,} units',ha='center',va='center',fontsize=10)
ax.set_xticks(range(4),bands);ax.set_yticks(range(len(v)),v.index);ax.set_xlabel('Line discount band');fig.colorbar(im,ax=ax,label='Unit return rate')
finish(fig,'05_discount_return_heatmap.png','Discount depth and returns: compare within category','Association only: promotion timing, product selection and customer mix also vary.')
# 6: Empirical lag curve, all returns fully matured.
fig,ax=plt.subplots(figsize=(10,5))
for k,g in lag.groupby('category'):
 a=np.sort(g.days_after_delivery);ax.step(a,np.arange(1,len(a)+1)/len(a),where='post',label=f'{k} (n={len(a):,})',lw=2)
ax.set_xlabel('Days after delivery');ax.set_ylabel('Cumulative share of return events');ax.yaxis.set_major_formatter(PercentFormatter(1));ax.legend(frameon=False)
finish(fig,'06_return_lag_ecdf.png','How quickly do returns arrive?','One return event per line in this simulation. Sales end Dec 2025; returns observed through Feb 15, 2026.')
# 7: Channel value vs service, bubble area is order count.
fig,ax=plt.subplots(figsize=(10,5));ax.scatter(channel.on_time_rate*100,channel.contribution_per_order,s=channel.orders/9,color=TEAL,alpha=.7,edgecolors='white')
for _,r in channel.iterrows():ax.annotate(r.channel,(r.on_time_rate*100,r.contribution_per_order),xytext=(8,8),textcoords='offset points')
ax.axhline(e.contribution.mean(),color=NAVY,ls='--',alpha=.5);ax.axvline(e.on_time.mean()*100,color=NAVY,ls='--',alpha=.5);ax.margins(.2);ax.set_xlabel('On-time delivered orders (%)');ax.set_ylabel('Contribution per delivered order (NGN)')
finish(fig,'07_channel_decision_matrix.png','Channel value and delivery reliability','Bubble area represents delivered orders. Contribution excludes acquisition spend; this is not channel ROI.')
# Results and publishing artifacts.
audit=json.loads((P/'reports/validation.json').read_text());net=e.net_merchandise_revenue.sum();contr=e.contribution.sum();margin=contr/(net+e.shipping_fee_ngn.sum());ret=e.returned_units.sum()/e.units.sum();worst=cat.iloc[-1]
nov=m[m.month.str.endswith('-11')];other=m[~m.month.str.endswith('-11')];novmargin=nov.contribution.sum()/((e[e.order_date.str[5:7]=='11'].net_merchandise_revenue+e[e.order_date.str[5:7]=='11'].shipping_fee_ngn).sum());othere=e[e.order_date.str[5:7]!='11'];othermargin=othere.contribution.sum()/(othere.net_merchandise_revenue+othere.shipping_fee_ngn).sum()
findings=f'''- Net merchandise revenue: **NGN {net:,.0f}**, after discounts and observed refunds.
- Contribution: **NGN {contr:,.0f}**; contribution margin **{margin:.1%}** of net merchandise revenue plus shipping fees.
- Unit return rate: **{ret:.1%}**. {worst.category} has the highest category rate at **{worst.unit_return_rate:.1%}**.
- November contribution margin is **{novmargin:.1%}**, versus **{othermargin:.1%}** across other months. This comparison is descriptive, not the causal effect of discounts.
- On-time delivery among delivered orders: **{e.on_time.mean():.1%}**. Cancelled orders are excluded from this metric and must be monitored separately.
'''
counts='\n'.join(f'| {k} | {v:,} |' for k,v in audit['counts'].items())
readme=f'''# Retail Profitability: Growth, Discounts and Returns

**SQL · Python · Customer cohorts · Unit economics · Data quality**

## Executive summary
This end-to-end portfolio investigates a fictional Nigerian online retailer selling Fashion, Electronics, Home and Beauty products. The business question is: **does sales growth translate into contribution after discounts, returns and fulfilment costs?** The audience is the commercial director, merchandising manager and customer operations team.

All records and prices are synthetic. Patterns are plausible simulation assumptions, not estimates of real Nigerian retail performance. No real personal information is used.

## Findings calculated from the cleaned data
{findings}
## Dataset
Sales cover January 2024–December 2025. Return observation extends to February 15, 2026, allowing all generated 30-day return windows to mature. Dimensions contain 6,000 fictional customers and 120 products. One order contains one to four unique product lines; customers may make repeat purchases. One return event per line may return some or all units. Cancelled orders retain their booked basket but contribute no sales, refunds, payment or fulfilment costs in the model.

| Table/stage | Rows |
|---|---:|
{counts}

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
'''
for name,title,note in charts:readme+=f'\n### {title}\n![{title}](charts/{name})\n{note}\n'
readme+='''
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
'''
(P/'README.md').write_text(readme);(P/'analysis/findings.md').write_text('# Executive findings\n\n'+findings+'\nReview promotions, return-prone categories and peak fulfilment. These are investigation priorities, not causal findings.\n')
# Responsive static dashboard with full chart images; no external dependencies.
cards=[('Net revenue',f'NGN {net/1e6:,.1f}m'),('Contribution margin',f'{margin:.1%}'),('Unit return rate',f'{ret:.1%}'),('Delivered orders',f'{len(e):,}')]
body=''.join(f'<div class="card"><small>{a}</small><strong>{b}</strong></div>' for a,b in cards)
panels=''.join(f'<figure><img src="../charts/{n}" alt="{html.escape(t)}"></figure>' for n,t,_ in [charts[0],charts[1],charts[3],charts[6]])
(P/'dashboard/index.html').write_text('''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Retail profitability</title><style>body{margin:0;background:#eef3f7;color:#193b57;font:15px system-ui}main{max-width:1500px;margin:auto;padding:25px}h1{margin:0;font-size:32px}p{color:#526678}.cards{display:grid;grid-template-columns:repeat(4,1fr);gap:15px;margin:22px 0}.card{background:white;border-top:4px solid #087f8c;border-radius:8px;padding:16px}small,strong{display:block}strong{font-size:27px;margin-top:8px}.plots{display:grid;grid-template-columns:1fr 1fr;gap:15px}figure{margin:0;background:#f8fafc;border-radius:8px;overflow:hidden}img{width:100%;display:block}footer{margin-top:18px;font-size:12px}@media(max-width:750px){.cards,.plots{grid-template-columns:1fr 1fr}.plots{grid-template-columns:1fr}}@media print{main{padding:5px}h1{font-size:24px}.card{padding:6px}.cards{margin:10px 0}footer{font-size:9px}@page{size:A3 landscape;margin:8mm}}</style><main><h1>Retail profitability | Growth worth keeping</h1><p>2024–2025 order cohorts • Fictional Nigerian retailer • Mature returns through 15 February 2026</p><section class="cards">'''+body+'</section><section class="plots">'+panels+'</section><footer>Static executive summary. Contribution excludes marketing, overhead and tax. Monthly refunds follow the original order month. All data is synthetic. See README.md for methods and limitations.</footer></main></html>')
(P/'reports/environment.json').write_text(json.dumps({'python':__import__('sys').version,'pandas':pd.__version__,'numpy':np.__version__,'matplotlib':matplotlib.__version__},indent=2))
print(findings);print('Created seven charts, README, findings and offline dashboard.')
