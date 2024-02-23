import pandas as pd
from prophet import Prophet

def predict_current_month(date , y):
       # Load the data into a DataFrame
       data = pd.DataFrame({
       'ds': date,
       'y': y
       })

       # Convert the date column to datetime type
       data['ds'] = pd.to_datetime(data['ds'])

       # Filter the data to include only the last 6 months
       last_6_months_data = data.tail(12)

       # Initialize Prophet model
       model = Prophet()

       # Fit the model to the data
       model.fit(last_6_months_data)

       # Make future predictions for February
       future_dates_february = pd.date_range(start='2023-02-01', periods=1, freq='ME')
       future_dates_february_df = pd.DataFrame({'ds': future_dates_february})
       forecast_february = model.predict(future_dates_february_df)

       # Print the forecasted data for February
       predicted_score = forecast_february[['ds', 'yhat_lower', 'yhat_upper', 'yhat']]
       print(predicted_score)
       return (predicted_score)
