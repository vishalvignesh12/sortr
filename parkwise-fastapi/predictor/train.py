import pandas as pd
import numpy as np
from xgboost import XGBRegressor
import joblib, os

# create toy dataset
N=1000
df = pd.DataFrame({
    'time_of_day': np.random.randint(0,24,N),
    'elapsed_minutes': np.random.randint(1,120,N),
    'vehicle_type': np.random.randint(0,3,N),
    'remaining': np.random.randint(1,60,N)
})
X = df[['time_of_day','elapsed_minutes','vehicle_type']]
y = df['remaining']
model = XGBRegressor(n_estimators=50)
model.fit(X,y)
os.makedirs('models', exist_ok=True)
joblib.dump(model, 'models/xgb_model.joblib')
print("Saved model to models/xgb_model.joblib")