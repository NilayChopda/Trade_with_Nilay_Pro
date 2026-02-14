# SUPER SIMPLE NSE DASHBOARD
from flask import Flask, render_template, jsonify
import os
import pandas as pd

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('dashboard.html')

@app.route('/api/data')
def get_data():
    try:
        # Check if we have scan results
        if os.path.exists('scanner_results'):
            csv_files = os.listdir('scanner_results')
            csv_files = [f for f in csv_files if f.endswith('.csv')]
            if csv_files:
                latest = max(csv_files)
                df = pd.read_csv(f'scanner_results/{latest}')
                return jsonify({
                    'success': True,
                    'last_scan': latest.replace('results_', '').replace('.csv', ''),
                    'stocks_found': len(df),
                    'stocks': df.to_dict('records')[:10]  # Only first 10
                })
    except:
        pass
    
    return jsonify({'success': False, 'stocks_found': 0})

if __name__ == '__main__':
    print("Dashboard: http://localhost:5000")
    app.run(debug=True, port=5001)
