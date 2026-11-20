import numpy as np
from sklearn.ensemble import RandomForestRegressor
from datetime import date,timedelta
rng=np.random.default_rng(42); X=[]; y=[]
for _ in range(1800):
 m=int(rng.integers(1,13));h=int(rng.integers(0,24));d=float(rng.uniform(15000,90000));r=float(rng.uniform(0,35000));t=float(rng.uniform(5,42))
 peak=22 if h in (7,8,9,18,19,20,21) else 0
 X.append([m,h,d,r,t]);y.append(max(5,55+d/1800-r/1200+peak+max(t-30,0)*1.1+8*np.sin(m/12*2*np.pi)+rng.normal(0,5)))
model=RandomForestRegressor(n_estimators=80,random_state=42).fit(X,y)
def forecast_price(date_text,hour,demand,renewable,temp):
 month=int(date_text.split("-")[1]);return {"price":round(float(model.predict([[month,hour,demand,renewable,temp]])[0]),2),"unit":"demo units/MWh","note":"Synthetic-data estimate, not a live market price."}
def sample_forecast():
 out=[]
 for i in range(12):
  d=date.today()+timedelta(days=i//4);h=[8,14,19,22][i%4];dem=[42000,35000,68000,51000][i%4];ren=[18000,28000,9000,14000][i%4];t=[29,32,30,27][i%4]
  out.append({"date":d.isoformat(),"hour":h,"demand":dem,"renewable":ren,"temp":t,"price":forecast_price(d.isoformat(),h,dem,ren,t)["price"]})
 return out
