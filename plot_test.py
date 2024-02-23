import pandas as pd
from statsmodels.tsa.arima.model import ARIMA

# Load the data into a pandas DataFrame
data = pd.read_csv('your_data.csv', parse_dates=['date'], index_col='date')

# Reverse the order of the DataFrame
data = data[::-1]

# Split the data into training and test sets
train_size = int(len(data) * 0.8)
train_data, test_data = data, data.iloc[train_size:]

# Train the ARIMA model
order = (train_data.shape[0], 1, 0)  # Order parameters (p, d, q) for ARIMA
model = ARIMA(train_data['ROI'], order=order)
model_fit = model.fit()

# Make predictions for the next month (February 2024)
next_month_prediction = model_fit.forecast(steps=1).iloc[0]

print("Predicted ROI for February 2024:", next_month_prediction)
