from flask import Flask, render_template, request, jsonify
import pandas as pd
import numpy as np
import plotly.graph_objs as go
import plotly
import json
from scipy.interpolate import make_interp_spline
from datetime import datetime, timedelta

app = Flask(__name__)

def interpolate_points(dates, y_values):
    # Convert dates to ordinal for interpolation
    x = np.array([date.toordinal() for date in dates])
    y = np.array(y_values)
    
    # Create a smooth line using spline interpolation
    x_smooth = np.linspace(x.min(), x.max(), 500)
    spline = make_interp_spline(x, y, k=3)
    y_smooth = spline(x_smooth)
    
    # Convert back to datetime
    x_smooth_dates = [datetime.fromordinal(int(date)) for date in x_smooth]
    
    return x_smooth_dates, y_smooth

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/plot', methods=['POST'])
def plot():
    file = request.files['file']
    birthdate_str = request.form['birthdate']
    start_year = int(request.form.get('start_year', 0))
    end_year = int(request.form.get('end_year', 5))

    if not file:
        return jsonify({"error": "No file uploaded"})

    try:
        birthdate = datetime.strptime(birthdate_str, '%Y-%m-%d')
        data = pd.read_csv(file)
        periods = data['Elapsed Period']
        y_values = data['Y Value']

        # Calculate the dates based on the birthdate and periods
        dates = [birthdate + timedelta(days=365.25 * period) for period in periods]

        # Calculate midpoints between consecutive dates
        mid_dates = [dates[i] + (dates[i+1] - dates[i]) / 2 for i in range(len(dates) - 1)]

        # Include the first and last date for plotting edges
        all_dates = [dates[0]] + mid_dates + [dates[-1]]
        all_y_values = [y_values[0]] + y_values.tolist() + [y_values[-1]]

        # Filter dates for the specified range
        filtered_dates = [date for date in all_dates if start_year <= (date.year - birthdate.year) <= end_year]
        filtered_y_values = [all_y_values[i] for i in range(len(all_dates)) if start_year <= (all_dates[i].year - birthdate.year) <= end_year]

        x_smooth, y_smooth = interpolate_points(filtered_dates, filtered_y_values)

        graph = go.Figure()
        graph.add_trace(go.Scatter(x=filtered_dates, y=filtered_y_values, mode='markers', name='Points'))
        graph.add_trace(go.Scatter(x=x_smooth, y=y_smooth, mode='lines', name='Smooth Line'))

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
            yaxis=dict(range=[-120, 120])  # Updated y-axis range
        )

        graphJSON = json.dumps(graph, cls=plotly.utils.PlotlyJSONEncoder)
        return jsonify({"graph": graphJSON})
    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == '__main__':
    app.run(debug=True)