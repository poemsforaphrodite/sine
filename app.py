from flask import Flask, render_template, request, jsonify
import pandas as pd
import numpy as np
import plotly.graph_objs as go
import plotly
import json
from datetime import datetime, timedelta
from scipy.interpolate import CubicSpline

app = Flask(__name__)

# Read the CSV data
dates_df = pd.read_csv('dates.csv')
periods_df = pd.read_csv('periods.csv')

# Ensure the Date and Average Date columns are in datetime format
dates_df['Period Beginning Times'] = pd.to_datetime(dates_df['Period Beginning Times'])
dates_df['Average Date'] = pd.to_datetime(dates_df['Average Date'])

def generate_spline_curve(dates, y_values):
    # Convert dates to numeric values for fitting
    dates_numeric = np.array([(date - dates[0]).days for date in dates])
    
    # Create the spline interpolator
    spline = CubicSpline(dates_numeric, y_values)
    
    # Generate a dense range of x values for a smooth curve
    x_dense = np.linspace(dates_numeric.min(), dates_numeric.max(), 1000)
    
    # Generate spline values
    spline_y_values = spline(x_dense)
    
    # Convert x_dense back to datetime
    dates_dense = [dates[0] + timedelta(days=int(x)) for x in x_dense]
    
    return dates_dense, spline_y_values

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/plot', methods=['POST'])
def plot():
    birthdate_str = request.form['birthdate']
    start_year = int(request.form.get('start_year', 0))
    end_year = int(request.form.get('end_year', 5))

    try:
        birthdate = datetime.strptime(birthdate_str, '%Y-%m-%d')

        # Repeat the periods to match the length of dates_df
        periods = periods_df['Elapsed Period']
        y_values = periods_df['Y Value']
        repeated_y_values = np.tile(y_values, len(dates_df) // len(y_values) + 1)[:len(dates_df)]

        # Filter dates for the specified range
        avg_dates = dates_df['Average Date']
        filtered_dates = [date for date in avg_dates if start_year <= (date.year - birthdate.year) <= end_year]

        # Generate spline curve values for the filtered dates
        spline_dates, spline_y_values = generate_spline_curve(filtered_dates, repeated_y_values[:len(filtered_dates)])

        graph = go.Figure()
        graph.add_trace(go.Scatter(x=filtered_dates, y=repeated_y_values[:len(filtered_dates)], mode='markers', name='Points'))
        graph.add_trace(go.Scatter(x=spline_dates, y=spline_y_values, mode='lines', name='Spline Curve'))

        graph.update_layout(
            title='Life Cycle Visualization',
            xaxis_title='Date',
            yaxis_title='Harmonic (Lucky/Unlucky)',
            xaxis=dict(
                tickformat='%Y-%m-%d',
                rangeslider=dict(visible=True),
                rangeselector=dict(
                    buttons=list([
                        dict(count=1, label="1y", step="year", stepmode="backward"),
                        dict(count=5, label="5y", step="year", stepmode="backward"),
                        dict(count=10, label="10y", step="year", stepmode="backward"),
                        dict(step="all")
                    ])
                )
            ),
            yaxis=dict(range=[-120, 120])  # Updated y-axis range for spline curve
        )

        graphJSON = json.dumps(graph, cls=plotly.utils.PlotlyJSONEncoder)
        return jsonify({"graph": graphJSON})
    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == '__main__':
    app.run(debug=True)