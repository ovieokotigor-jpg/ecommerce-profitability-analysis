"""Seeded, fictional retail operations; no network or personal information."""
import random,csv,copy
from pathlib import Path
from datetime import date,timedelta
P=Path(__file__).resolve().parent
def generate():
 r=random.Random(271828); raw=P/'data/raw';raw.mkdir(parents=True,exist_ok=True)
 def save(name,rows):
  with (raw/(name+'.csv')).open('w',newline='',encoding='utf-8') as f:
   w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 cats=['Fashion','Electronics','Home','Beauty']; base=[16000,62000,25000,11000]
 customers=[]
 for i in range(1,6001):
  customers.append(dict(customer_id=i,signup_date=(date(2023,7,1)+timedelta(days=r.randrange(860))).isoformat(),region=r.choices(['Lagos','Abuja','South South','South East','Other'],[.40,.20,.15,.12,.13])[0]))
 products=[]
 for i in range(1,121):
  k=(i-1)//30; price=round(base[k]*r.lognormvariate(0,.45)/100)*100
  products.append(dict(product_id=i,product_name=f'{cats[k]} product {i}',category=cats[k],list_price_ngn=price,reference_unit_cost_ngn=round(price*r.uniform(.43,.72),2)))
 days=[date(2024,1,1)+timedelta(days=i) for i in range(731)]
 weights=[(1+.0007*i)*(2.2 if d.month==11 else 1.4 if d.month==12 else .8 if d.month==2 else 1)*([.9,.9,1,1,1.2,1.3,1.1][d.weekday()]) for i,d in enumerate(days)]
 dates=sorted(r.choices(days,weights,k=25000)); propensity={c['customer_id']:r.paretovariate(2) for c in customers}
 orders=[];items=[];returns=[]; active=[]; waiting=sorted(customers,key=lambda c:c['signup_date']); pos=0
 for oid,d in enumerate(dates,1):
  while pos<len(waiting) and waiting[pos]['signup_date']<=d.isoformat():active.append(waiting[pos]);pos+=1
  c=r.choices(active,[propensity[x['customer_id']] for x in active])[0]
  promo=d.month==11 or r.random()<.15
  channel=r.choices(['Organic','Paid social','Email','Marketplace'],[.30,.35 if promo else .20,.20,.15])[0]
  cancelled=r.random()<(.045 if channel=='Paid social' else .025)
  ship_days=max(1,round(r.gauss(3 if c['region']=='Lagos' else 5,1.3)+(2 if d.month==11 else 0)))
  delivered=None if cancelled else d+timedelta(days=ship_days)
  orders.append(dict(order_id=oid,customer_id=c['customer_id'],order_date=d.isoformat(),delivery_date=delivered.isoformat() if delivered else '',promised_delivery_date=(d+timedelta(days=4 if c['region']=='Lagos' else 6)).isoformat(),order_status='Cancelled' if cancelled else 'Delivered',channel=channel,shipping_fee_ngn=0 if promo else r.choice([1000,1500,2000]),fulfilment_cost_ngn=0 if cancelled else (1800 if c['region']=='Lagos' else 3000)+r.randrange(600),payment_fee_rate=.015))
  basket=r.choices([1,2,3,4],[.48,.32,.15,.05])[0]; chosen=set()
  for j in range(basket):
   cat=r.choices(cats,[.40 if promo else .30,.20,.25,.15])[0]
   choices=[p for p in products if p['category']==cat and p['product_id'] not in chosen]; p=r.choice(choices);chosen.add(p['product_id'])
   qty=r.choices([1,2,3],[.82,.15,.03])[0]; disc=r.choice([.15,.20,.25,.30]) if promo else r.choices([0,.05,.10],[.75,.15,.10])[0]
   price=round(p['list_price_ngn']*(1+.00025*(d-days[0]).days),2)
   cost=round(p['reference_unit_cost_ngn']*(1+.00033*(d-days[0]).days),2)
   lid=len(items)+1
   items.append(dict(order_item_id=lid,order_id=oid,product_id=p['product_id'],quantity=qty,unit_price_ngn=price,discount_rate=disc,unit_cost_ngn=cost))
   prob={'Fashion':.19,'Electronics':.065,'Home':.08,'Beauty':.035}[cat]+(.035 if disc>=.2 else 0)+(.025 if ship_days>6 else 0)
   if not cancelled and r.random()<prob:
    rq=r.randint(1,qty); rd=delivered+timedelta(days=min(30,max(1,round(r.gammavariate(2,5)))))
    returns.append(dict(return_id=len(returns)+1,order_item_id=lid,return_date=rd.isoformat(),returned_quantity=rq,reason=r.choice(['Size or fit','Changed mind']) if cat=='Fashion' else r.choice(['Damaged','Not as described','Changed mind']),restockable=int(r.random()<(.8 if cat=='Fashion' else .55)),handling_cost_ngn=r.choice([600,800,1200])))
 # Disjoint injected item issues; dimensions and returns retain original IDs.
 for t in r.sample(orders,300):t['channel']=''
 for t in r.sample(orders,400):t['order_status']=' '+t['order_status'].lower()+' '
 for t in r.sample(orders,200):t['order_date']=date.fromisoformat(t['order_date']).strftime('%d/%m/%Y')
 bad=r.sample(items,70)
 for t in bad[:50]:t['quantity']=-t['quantity']
 for t in bad[50:]:t['product_id']=999999
 raworders=orders+[copy.deepcopy(t) for t in r.sample(orders,150)]
 for name,rows in [('customers',customers),('products',products),('orders',raworders),('order_items',items),('returns',returns)]:save(name,rows)
 print('Generated', {n:len(v) for n,v in [('orders',raworders),('order_items',items),('returns',returns)]})
if __name__=='__main__':generate()
