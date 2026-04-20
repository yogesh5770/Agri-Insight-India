import pandas as pd
import json
import numpy as np
from sklearn.linear_model import LinearRegression

class DataManager:
    def __init__(self, csv_path):
        print(f"Loading data from {csv_path}...")
        self.df = pd.read_csv(csv_path)
        # Clean numeric columns - replace missing/invalid with 0
        numeric_cols = self.df.select_dtypes(include=['number']).columns
        self.df[numeric_cols] = self.df[numeric_cols].fillna(0)
        print("Data loaded successfully.")

    def get_states(self):
        """Returns a sorted list of unique states."""
        return sorted(self.df['State Name'].unique().tolist())

    def get_districts(self, state_name):
        """Returns a sorted list of unique districts for a given state."""
        return sorted(self.df[self.df['State Name'] == state_name]['Dist Name'].unique().tolist())

    def get_district_trends(self, state_name, district_name, crop_name, metric='YIELD'):
        """
        Returns time-series data for a crop in a district within a specific state,
        including predictions up to 2030.
        """
        col_match = f"{crop_name.upper()} {metric.upper()}"
        target_col = None
        for col in self.df.columns:
            if crop_name.upper() in col and metric.upper() in col:
                target_col = col
                break
        
        if not target_col:
            print(f"Column not found for {crop_name} {metric}")
            return []

        # Filter by both state and district for uniqueness
        subset = self.df[(self.df['State Name'] == state_name) & (self.df['Dist Name'] == district_name)][['Year', target_col]].sort_values('Year')
        
        # Prepare historical data
        historical_data = []
        for _, row in subset.iterrows():
            historical_data.append({
                'Year': int(row['Year']),
                'Value': float(row[target_col]),
                'is_predicted': False
            })

        if not historical_data:
            return []

        # Prediction Logic using Linear Regression
        try:
            X = subset['Year'].values.reshape(-1, 1)
            y = subset[target_col].values
            
            model = LinearRegression()
            model.fit(X, y)
            
            last_year = int(subset['Year'].max())
            future_years = np.arange(last_year + 1, 2031).reshape(-1, 1)
            predictions = model.predict(future_years)
            
            for i, year in enumerate(future_years.flatten()):
                historical_data.append({
                    'Year': int(year),
                    'Value': max(0, float(predictions[i])), # Ensure no negative yields
                    'is_predicted': True
                })
        except Exception as e:
            print(f"Prediction error: {e}")

        return historical_data

    def get_top_crops(self, state_name, district_name, year=None):
        """Returns the top performing crops in a district for a given year (or latest available)."""
        if year is None:
            year = self.df[(self.df['State Name'] == state_name) & (self.df['Dist Name'] == district_name)]['Year'].max()
        
        row = self.df[(self.df['State Name'] == state_name) & (self.df['Dist Name'] == district_name) & (self.df['Year'] == year)]
        if row.empty:
            return []

        # Find all YIELD columns
        yield_cols = [c for c in self.df.columns if 'YIELD' in c]
        crop_data = []
        for col in yield_cols:
            crop_name = col.split(' ')[0]
            val = row[col].values[0]
            if val > 0:
                crop_data.append({'crop': crop_name, 'yield': float(val)})
        
        # Sort by yield descending
        return sorted(crop_data, key=lambda x: x['yield'], reverse=True)[:10]

# Simple test if run directly
if __name__ == "__main__":
    dm = DataManager('ICRISAT-District Level Data.csv')
    print(dm.get_states()[:5])
