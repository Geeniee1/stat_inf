import pandas as pd
df = pd.read_csv('/Users/edwind/Desktop/statinf_project/python_code/data/cleaned_data/final_departures.csv')
df['is_delayed'] = df['delay_minutes'] > 3
df.to_csv('/Users/edwind/Desktop/statinf_project/python_code/data/cleaned_data/final_departures.csv', index=False)