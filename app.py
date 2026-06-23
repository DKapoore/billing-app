from flask import Flask, render_template, request, jsonify, session
import json
import os
from datetime import datetime
import uuid

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Change this in production

# Data storage
INVOICES_FILE = 'invoices.json'

def load_invoices():
    """Load invoices from JSON file"""
    if os.path.exists(INVOICES_FILE):
        with open(INVOICES_FILE, 'r') as f:
            return json.load(f)
    return []

def save_invoices(invoices):
    """Save invoices to JSON file"""
    with open(INVOICES_FILE, 'w') as f:
        json.dump(invoices, f, indent=2)

@app.route('/')
def index():
    """Home page - billing form"""
    return render_template('index.html')

@app.route('/generate_invoice', methods=['POST'])
def generate_invoice():
    """Generate a new invoice"""
    try:
        data = request.json
        
        # Create invoice object
        invoice = {
            'id': str(uuid.uuid4())[:8],
            'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'customer_name': data.get('customer_name', ''),
            'customer_email': data.get('customer_email', ''),
            'customer_phone': data.get('customer_phone', ''),
            'items': data.get('items', []),
            'subtotal': float(data.get('subtotal', 0)),
            'tax': float(data.get('tax', 0)),
            'tax_rate': float(data.get('tax_rate', 10)),
            'total': float(data.get('total', 0)),
            'status': 'paid'
        }
        
        # Save to storage
        invoices = load_invoices()
        invoices.append(invoice)
        save_invoices(invoices)
        
        return jsonify({'success': True, 'invoice_id': invoice['id']})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/invoices')
def view_invoices():
    """View all invoices"""
    invoices = load_invoices()
    return render_template('invoices.html', invoices=invoices)

@app.route('/invoice/<invoice_id>')
def view_invoice(invoice_id):
    """View a specific invoice"""
    invoices = load_invoices()
    invoice = next((inv for inv in invoices if inv['id'] == invoice_id), None)
    
    if invoice:
        return render_template('invoice.html', invoice=invoice)
    else:
        return "Invoice not found", 404

@app.route('/api/invoices')
def get_invoices_api():
    """API endpoint to get all invoices"""
    return jsonify(load_invoices())

@app.route('/api/invoice/<invoice_id>')
def get_invoice_api(invoice_id):
    """API endpoint to get a specific invoice"""
    invoices = load_invoices()
    invoice = next((inv for inv in invoices if inv['id'] == invoice_id), None)
    
    if invoice:
        return jsonify(invoice)
    else:
        return jsonify({'error': 'Invoice not found'}), 404

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)