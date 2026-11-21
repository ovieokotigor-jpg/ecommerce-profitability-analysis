"""Run with: python pipeline.py. Raw staging remains inspectable."""
from pathlib import Path
import sqlite3,csv,json,re,subprocess,sys
P=Path(__file__).resolve().parent
def queries(path):
 parts=re.split(r'-- name: (\w+)\n',path.read_text())
 return list(zip(parts[1::2],parts[2::2]))
def run():
 for d in ['data/clean','reports','charts','dashboard','analysis']:(P/d).mkdir(parents=True,exist_ok=True)
 if not (P/'data/raw/orders.csv').exists():
  from generate_data import generate
  generate()
 c=sqlite3.connect(P/'retail.sqlite')
 numeric={'customer_id','product_id','order_id','order_item_id','return_id','quantity','returned_quantity','restockable','discount_rate','payment_fee_rate'}
 schema=[]
 for path in sorted((P/'data/raw').glob('*.csv')):
  rows=list(csv.DictReader(path.open()));cols=list(rows[0]);table='raw_'+path.stem
  # Reject malformed numeric strings before SQLite can silently coerce them to zero.
  for row in rows:
   for k,v in row.items():
    if k in numeric or k.endswith('_ngn'):
     if not re.fullmatch(r'-?\d+(\.\d+)?',v):raise ValueError(f'Malformed number {table}.{k}: {v!r}')
  c.execute(f'DROP TABLE IF EXISTS {table}')
  ddl=f'CREATE TABLE {table} ('+','.join('"'+x+'" TEXT' for x in cols)+');'
  schema.append(ddl);c.execute(ddl);c.executemany(f'INSERT INTO {table} VALUES ('+','.join('?' for _ in cols)+')',[list(r.values()) for r in rows]);c.commit()
 (P/'sql/00_staging_schema.sql').write_text('\n'.join(schema))
 for name in ['01_clean.sql','02_transform.sql']:c.executescript((P/'sql'/name).read_text())
 checks={name:c.execute(sql).fetchone()[0] for name,sql in queries(P/'sql/04_validation.sql')}
 assert not any(checks.values()),checks
 assert c.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
 def export(sql,path):
  q=c.execute(sql)
  with path.open('w',newline='') as f:
   w=csv.writer(f);w.writerow([x[0] for x in q.description]);w.writerows(q.fetchall())
 for name in ['customers','products','orders','order_items','returns','quarantine_orders','order_economics']:export('SELECT * FROM '+name,P/'data/clean'/f'{name}.csv')
 for name,sql in queries(P/'sql/03_analysis.sql'):export(sql,P/'reports'/f'{name}.csv')
 counts={t:c.execute('SELECT COUNT(*) FROM '+t).fetchone()[0] for t in ['raw_orders','orders_normalized','orders','raw_order_items','order_items','raw_returns','returns','quarantine_orders']}
 assert counts['raw_orders']==25150 and counts['orders_normalized']==25000
 assert counts['orders']+counts['quarantine_orders']==25000
 audit={'counts':counts,'duplicates_removed':150,'checks':checks,'return_observation_end':'2026-02-15','sales_window':'2024-01-01 through 2025-12-31'}
 (P/'reports/validation.json').write_text(json.dumps(audit,indent=2));c.close();print(json.dumps(audit,indent=2))
 subprocess.run([sys.executable,str(P/'analysis/analyze.py')],check=True)
if __name__=='__main__':run()
