from flask import Flask, render_template, request, jsonify
import json
import os
from datetime import datetime
import uuid
import psycopg2
from psycopg2.extras import Json

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key')

# Database configuration
DATABASE_URL = os.environ.get('DATABASE_URL')

def get_db_connection():
    """Get database connection"""
    if DATABASE_URL:
        return psycopg2.connect(DATABASE_URL)
    return None

def init_db():
    """Initialize database table"""
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute('''
                CREATE TABLE IF NOT EXISTS invoices (
                    id VARCHAR(20) PRIMARY KEY,
                    data JSONB NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()
            cur.close()
            conn.close()
            print("Database initialized successfully")
        except Exception as e:
            print(f"Database init error: {e}")

def load_invoices():
    """Load invoices from database"""
    invoices = []
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute('SELECT data FROM invoices ORDER BY created_at DESC')
            rows = cur.fetchall()
            invoices = [row[0] for row in rows]
            cur.close()
            conn.close()
        except Exception as e:
            print(f"Error loading invoices: {e}")
    return invoices

def save_invoice(invoice):
    """Save invoice to database"""
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute(
                'INSERT INTO invoices (id, data) VALUES (%s, %s)',
                (invoice['id'], Json(invoice))
            )
            conn.commit()
            cur.close()
            conn.close()
            return True
        except Exception as e:
            print(f"Error saving invoice: {e}")
            return False
    return False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate_invoice', methods=['POST'])
def generate_invoice():
    try:
        data = request.json
        
        customer_name = data.get('customer_name', '').strip()
        if not customer_name:
            return jsonify({'success': False, 'error': 'Customer name is required'}), 400
        
        items = data.get('items', [])
        if not items:
            return jsonify({'success': False, 'error': 'At least one item is required'}), 400
        
        invoice = {
            'id': str(uuid.uuid4())[:8],
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
        
        if save_invoice(invoice):
            return jsonify({'success': True, 'invoice_id': invoice['id']})
        else:
            return jsonify({'success': False, 'error': 'Database error'}), 500
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

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
        return "Invoice not found", 404

@app.route('/api/invoices')
def get_invoices_api():
    return jsonify(load_invoices())

# Initialize database on startup
init_db()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
