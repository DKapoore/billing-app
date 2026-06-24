from flask import Flask, render_template, request, jsonify
import json
import os
from datetime import datetime
import uuid

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key')

# Vercel environment detection
def is_vercel():
    return os.environ.get('VERCEL_ENV') or os.environ.get('NOW_REGION')

def get_invoices_path():
    """Get the correct path for invoices.json"""
    if is_vercel():
        return '/tmp/invoices.json'
    return 'invoices.json'

INVOICES_FILE = get_invoices_path()

def load_invoices():
    """Load invoices from JSON file"""
    try:
        if os.path.exists(INVOICES_FILE):
            with open(INVOICES_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading invoices: {e}")
    return []

def save_invoices(invoices):
    """Save invoices to JSON file"""
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(INVOICES_FILE), exist_ok=True)
        
        with open(INVOICES_FILE, 'w') as f:
            json.dump(invoices, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving invoices: {e}")
        return False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate_invoice', methods=['POST'])
def generate_invoice():
    """Generate a new invoice"""
    try:
        # Get JSON data
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False, 
                'error': 'No data provided'
            }), 400
        
        # Validate customer name
        customer_name = data.get('customer_name', '').strip()
        if not customer_name:
            return jsonify({
                'success': False, 
                'error': 'Customer name is required'
            }), 400
        
        # Validate items
        items = data.get('items', [])
        if not items or len(items) == 0:
            return jsonify({
                'success': False, 
                'error': 'At least one item is required'
            }), 400
        
        # Create invoice object
        invoice = {
            'id': str(uuid.uuid4())[:8].upper(),
            'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'customer_name': customer_name,
            'customer_email': data.get('customer_email', ''),
            'customer_phone': data.get('customer_phone', ''),
            'items': items,
            'subtotal': float(data.get('subtotal', 0)),
            'tax': float(data.get('tax', 0)),
            'tax_rate': float(data.get('tax_rate', 10)),
            'total': float(data.get('total', 0)),
            'status': 'paid'
        }
        
        # Save to storage
        invoices = load_invoices()
        invoices.append(invoice)
        
        if save_invoices(invoices):
            return jsonify({
                'success': True, 
                'invoice_id': invoice['id'],
                'message': 'Invoice created successfully'
            })
        else:
            return jsonify({
                'success': False, 
                'error': 'Failed to save invoice'
            }), 500
    
    except Exception as e:
        print(f"Error in generate_invoice: {str(e)}")
        return jsonify({
            'success': False, 
            'error': str(e)
        }), 400

@app.route('/invoices')
def view_invoices():
    invoices = load_invoices()
    return render_template('invoices.html', invoices=invoices)

@app.route('/invoice/<invoice_id>')
def view_invoice(invoice_id):
    invoices = load_invoices()
    invoice = next((inv for inv in invoices if inv['id'] == invoice_id), None)
    
    if invoice:
        return render_template('invoice.html', invoice=invoice)
    else:
        return render_template('invoice.html', invoice=None, error='Invoice not found')

@app.route('/api/invoices')
def get_invoices_api():
    try:
        invoices = load_invoices()
        return jsonify(invoices)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/invoice/<invoice_id>')
def get_invoice_api(invoice_id):
    try:
        invoices = load_invoices()
        invoice = next((inv for inv in invoices if inv['id'] == invoice_id), None)
        
        if invoice:
            return jsonify(invoice)
        else:
            return jsonify({'error': 'Invoice not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Health check endpoint
@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'environment': 'vercel' if is_vercel() else 'local',
        'storage': '/tmp' if is_vercel() else 'local'
    })

# Vercel serverless handler
def handler(request, context):
    return app(request, context)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
