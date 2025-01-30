from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
from datetime import datetime

app = Flask(__name__)
CORS(app)

def is_valid_npi(npi):
    return str(npi).isdigit() and len(str(npi)) == 10

def is_valid_cpt(cpt_code):
    return str(cpt_code).replace("-", "").isdigit() and 4 <= len(str(cpt_code)) <= 6

def is_valid_icd10(icd10_code):
    code = str(icd10_code).upper()
    return code[0].isalpha() and len(code) >= 3 and code[1:].replace(".", "").isalnum()

def analyze_claim(row):
    risks = []
    if not is_valid_cpt(row['cpt_code']):
        risks.append(f"Invalid CPT code: {row['cpt_code']}")
    if not is_valid_icd10(row['icd10_code']):
        risks.append(f"Invalid ICD10 code: {row['icd10_code']}")
    if row['prior_auth_required'].lower() == 'yes' and row['prior_auth_provided'].lower() != 'yes':
        risks.append("Missing prior authorization")
    if not is_valid_npi(row['provider_npi']):
        risks.append(f"Invalid NPI: {row['provider_npi']}")
    if row['network_status'].lower() == 'out':
        risks.append("Out-of-network service")
    risk_level = "High" if len(risks) > 1 else "Medium" if risks else "Low"
    return {
        'claim_id': row['claim_id'],
        'patient_id': row['patient_id'],
        'service_date': row['service_date'],
        'cpt_code': row['cpt_code'],
        'icd10_code': row['icd10_code'],
        'denial_risks': risks,
        'risk_level': risk_level
    }

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    file = request.files['file']
    if file.filename == '' or not file.filename.endswith('.csv'):
        return jsonify({'error': 'Invalid file'}), 400
    try:
        df = pd.read_csv(file)
        required_columns = ['claim_id', 'patient_id', 'service_date', 'cpt_code', 'icd10_code', 'provider_npi', 'network_status', 'prior_auth_required', 'prior_auth_provided']
        if not all(col in df.columns for col in required_columns):
            return jsonify({'error': 'Missing required columns'}), 400
        results = [analyze_claim(row) for _, row in df.iterrows()]
        return jsonify({
            'results': results,
            'total_claims': len(results),
            'high_risk_claims': sum(1 for r in results if r['risk_level'] == 'High'),
            'processed_at': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)  # <-- Added debug mode
