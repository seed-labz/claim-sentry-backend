from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import numpy as np
from datetime import datetime

app = Flask(__name__)
CORS(app)

def check_cpt_icd10_match(row):
    """Simulate CPT-ICD10 compatibility check"""
    # In a real implementation, this would check against a database of valid combinations
    return np.random.choice([True, False], p=[0.8, 0.2])

def check_prior_auth(row):
    """Check if prior authorization is required and present"""
    # Simulate checking if the procedure requires prior auth and if it's present
    return np.random.choice([True, False], p=[0.9, 0.1])

def is_valid_npi(npi):
    """Basic NPI validation"""
    return len(str(npi)) == 10 and str(npi).isdigit()

def analyze_claim(row):
    """Analyze a single claim for potential denial risks"""
    risks = []
    if not check_cpt_icd10_match(row):
        risks.append("CPT code may not support the ICD-10 diagnosis")
    if not check_prior_auth(row):
        risks.append("Missing required prior authorization")
    if 'provider_npi' in row and not is_valid_npi(row['provider_npi']):
        risks.append("Invalid provider NPI")
    if 'network_status' in row and row['network_status'].lower() == 'out':
        risks.append("Out-of-network service may not be covered")

    print(f"Analyzing claim: {row.to_dict()}")  # DEBUG PRINT
    print(f"Risks found: {risks}")  # DEBUG PRINT

    return risks


@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not file.filename.endswith('.csv'):
        return jsonify({'error': 'File must be a CSV'}), 400
    
    try:
        # Read CSV file
        df = pd.read_csv(file)
        
        # Process each claim
        results = []
        for index, row in df.iterrows():
            risks = analyze_claim(row)
            
            result = {
                'claim_id': str(row.get('claim_id', f'CLAIM_{index}')),
                'patient_id': str(row.get('patient_id', 'N/A')),
                'service_date': str(row.get('service_date', 'N/A')),
                'cpt_code': str(row.get('cpt_code', 'N/A')),
                'icd10_code': str(row.get('icd10_code', 'N/A')),
                'amount': float(row.get('amount', 0.0)),
                'provider': str(row.get('provider_name', 'N/A')),
                'denial_risks': risks,
                'risk_level': 'High' if len(risks) > 1 else 'Medium' if len(risks) == 1 else 'Low'
            }
            results.append(result)
        
        return jsonify({
            'results': results,
            'total_claims': len(results),
            'high_risk_claims': sum(1 for r in results if r['risk_level'] == 'High'),
            'processed_at': datetime.now().isoformat()
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
