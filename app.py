from flask import Flask, render_template, request, jsonify
import json
import os
from datetime import datetime
import uuid

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key')

# Simple in-memory storage for Vercel
invoices_db = []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate_invoice', methods=['POST'])
def generate_invoice():
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        customer_name = data.get('customer_name', '').strip()
        if not customer_name:
            return jsonify({'success': False, 'error': 'Customer name required'}), 400
        
        # ✅ FIX: items ko alag naam se store karein
        items_list = data.get('items', [])
        if not items_list or len(items_list) == 0:
            return jsonify({'success': False, 'error': 'Items required'}), 400
        
        # ✅ FIX: Valid items ko process karein
        valid_items = []
        for item in items_list:
            if isinstance(item, dict) and 'name' in item and 'quantity' in item and 'price' in item:
                valid_items.append({
                    'name': str(item.get('name', '')),
                    'quantity': float(item.get('quantity', 0)),
                    'price': float(item.get('price', 0))
                })
        
        if not valid_items:
            return jsonify({'success': False, 'error': 'No valid items found'}), 400
        
        # ✅ FIX: 'items' ki jagah 'item_list' use karein
        invoice = {
            'id': str(uuid.uuid4())[:8].upper(),
            'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'customer_name': customer_name,
            'customer_email': data.get('customer_email', ''),
            'customer_phone': data.get('customer_phone', ''),
            'item_list': valid_items,  # ✅ Changed from 'items' to 'item_list'
            'subtotal': float(data.get('subtotal', 0)),
            'tax': float(data.get('tax', 0)),
            'tax_rate': float(data.get('tax_rate', 10)),
            'total': float(data.get('total', 0)),
            'status': 'paid'
        }
        
        invoices_db.append(invoice)
        
        return jsonify({
            'success': True,
            'invoice_id': invoice['id']
        })
    
    except Exception as e:
        print(f"Error in generate_invoice: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/invoices')
def view_invoices():
    return render_template('invoices.html', invoices=invoices_db)

@app.route('/invoice/<invoice_id>')
def view_invoice(invoice_id):
    invoice = None
    for inv in invoices_db:
        if inv['id'] == invoice_id:
            invoice = inv
            break
    
    if invoice:
        # ✅ FIX: Ensure item_list exists and is a list
        if 'item_list' not in invoice or not isinstance(invoice['item_list'], list):
            invoice['item_list'] = []
        return render_template('invoice.html', invoice=invoice)
    else:
        return "Invoice not found", 404

@app.route('/api/invoices')
def get_invoices_api():
    return jsonify(invoices_db)

@app.route('/health')
def health():
    return jsonify({'status': 'healthy', 'invoices': len(invoices_db)})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
