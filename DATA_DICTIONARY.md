# Data dictionary

All money is synthetic Nigerian naira (NGN), excluding tax. Blank CSV fields are NULL, not zero. Rates are fractions unless a chart labels percentages. Dates contain no times. Row counts exclude CSV headers. All IDs are numeric.

## customers

| Column | Definition |
|---|---|
| `customer_id` | Integer customer key. PK in customers; FK in orders. Synthetic ID, no names/contact information. |
| `signup_date` | ISO date customer registered; must not follow an order date. |
| `region` | Customer region grouping; used for simulated delivery duration and cost. |

## products

| Column | Definition |
|---|---|
| `product_id` | Integer product key. PK in products; FK in items. Twenty raw item references intentionally invalid. |
| `product_name` | Fictional generic product label. |
| `category` | Fashion, Electronics, Home or Beauty. |
| `list_price_ngn` | Reference catalog price at start of simulation, NGN excluding tax; use item transaction prices for sales. |
| `reference_unit_cost_ngn` | Reference starting product cost, NGN per unit. Transaction costs vary over time. |

## orders

| Column | Definition |
|---|---|
| `order_id` | Integer order key. PK in cleaned orders; FK in items. Raw orders contain 150 duplicate copies. |
| `customer_id` | Integer customer key. PK in customers; FK in orders. Synthetic ID, no names/contact information. |
| `order_date` | Order date; normally ISO YYYY-MM-DD, 200 raw values use DD/MM/YYYY. Analysis period attribution uses this date. |
| `delivery_date` | ISO actual delivery date; NULL/blank for cancelled orders. |
| `promised_delivery_date` | ISO customer delivery promise, retained on cancellation. |
| `order_status` | Delivered or Cancelled; 400 raw labels have whitespace/lowercase differences. Clean values lowercase. |
| `channel` | Organic, Paid social, Email or Marketplace; 300 raw blanks become Unknown, not imputed. |
| `shipping_fee_ngn` | Booked shipping charge in NGN; zero on promotion. For cancelled orders this is an uncharged quote, excluded from economics. |
| `fulfilment_cost_ngn` | Outbound delivery and handling cost in NGN per order; zero on cancellation. Not multiplied by item count. |
| `payment_fee_rate` | Payment processing proportion, 0.015. Applies to delivered booked merchandise sales plus shipping; assumed nonrefundable. |

## order_items

| Column | Definition |
|---|---|
| `order_item_id` | Integer line primary key in items; FK in returns. Product unique within an order. |
| `order_id` | Integer order key. PK in cleaned orders; FK in items. Raw orders contain 150 duplicate copies. |
| `product_id` | Integer product key. PK in products; FK in items. Twenty raw item references intentionally invalid. |
| `quantity` | Booked units per line, 1–3 normally; 50 negative raw errors. Cancelled baskets retain booked quantities. |
| `unit_price_ngn` | Transaction unit selling price before discounts, NGN excluding tax. |
| `discount_rate` | Discount fraction, 0–0.30; 0.20 means 20%. |
| `unit_cost_ngn` | Transaction unit product cost, NGN. Snapshot appropriate to order date. |

## returns

| Column | Definition |
|---|---|
| `return_id` | Integer return event primary key. |
| `order_item_id` | Integer line primary key in items; FK in returns. Product unique within an order. |
| `return_date` | ISO return/refund date, 1–30 days after actual delivery. Observation continues beyond sales period. |
| `returned_quantity` | Units returned from the line; positive and no more than original quantity. |
| `reason` | Size or fit, Changed mind, Damaged or Not as described; category-dependent. |
| `restockable` | Integer binary flag; 1 means returned units fully recover original product cost, 0 means no cost recovery. |
| `handling_cost_ngn` | Return-event processing cost, NGN, charged once per returned line. |

## Derived tables and fields

Clean customers/products/orders/order_items/returns retain the input fields, with typed numeric columns, normalized dates/status and Unknown channel. quarantine_orders has order_id plus a textual reason; all source evidence remains in raw tables. orders_normalized and items_normalized are intermediate staging results.

line_economics contains delivered lines only. Its inherited fields are documented above; order_date, channel and order_status come from orders and category comes from products.

| Derived field | Definition |
|---|---|
| gross_sales | quantity × unit_price_ngn, NGN |
| discount_value | gross_sales × discount_rate, NGN |
| booked_sales | gross_sales − discount_value, NGN |
| returned_units | Sum returned_quantity for this line; zero if no return |
| refund_value | returned_units × discounted unit price, NGN |
| retained_cogs | (quantity − restockable returned units) × unit_cost_ngn, NGN |
| return_handling | Sum handling_cost_ngn, zero if no return |

order_economics contains one delivered order. It retains all order fields, customer region and aggregated gross_sales, discount_value, booked_sales, retained_cogs and return_handling.

| Additional field | Definition |
|---|---|
| refunds | Sum line refund_value, NGN |
| units | Sum line quantity |
| returned_units | Sum returned units across order lines |
| net_merchandise_revenue | booked_sales − refunds, NGN |
| payment_fees | (booked_sales + shipping_fee_ngn) × payment_fee_rate, NGN |
| contribution | net merchandise revenue + shipping fees − retained COGS − fulfilment − payment fees − return handling, NGN |
| on_time | 1 when delivered by promised delivery date, else 0; cancelled orders absent |

## Analytical exports

monthly groups delivered orders by original order month: orders is the count; discounts, refunds, net_revenue and contribution are summed NGN; contribution_margin is contribution/(net revenue+shipping fees); on_time_rate is on-time/ delivered orders.

category reports overlapping category order counts (an order can span categories), delivered units, returned units, unit_return_rate, net_revenue and merchandise_contribution (net revenue minus retained product cost and return handling, before order-level costs). Do not sum category order counts to obtain company-wide order counts.

channel reports delivered orders, net revenue, contribution, contribution_per_order and on_time_rate. discount_bands uses line-level discount ranges crossed with category, and reports lines, units, return_rate and merchandise_contribution. cohort has first observed delivered-purchase month, integer age_month and distinct active_customers; divide by age-zero customer count for rates. product_concentration ranks product_id by net_revenue. return_lag contains return_id, category and integer days_after_delivery. See SQL for exact formulas.

## Interpretation boundaries

These data have no advertising spend, inventory balance or tax ledger. Contribution is not net profit; channel performance is not ROI. Restock recovery and nonrefundable fees are explicit scenario assumptions. All later refunds are attributed back to original order date for mature cohort economics, not cash reporting.
