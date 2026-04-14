# app.py
import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from streamlit_option_menu import option_menu
import hashlib
import shutil
import os

# Page configuration
st.set_page_config(
    page_title="Incredible Studios · Retail & Wholesale Hub",
    page_icon="🏪",
    layout="wide",
    initial_sidebar_state="auto"
)

# Custom CSS for styling
st.markdown("""
<style>
    /* Main container styling */
    .main {
        background: linear-gradient(135deg, #fef9e8 0%, #eef4fa 100%);
    }
    
    /* Card styling */
    .glass-card {
        background: rgba(255, 255, 255, 0.85);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 245, 220, 0.6);
        border-radius: 1.75rem;
        padding: 1.25rem;
        transition: all 0.2s ease;
        box-shadow: 0 8px 20px -8px rgba(0, 0, 0, 0.08);
    }
    
    .glass-card:hover {
        transform: translateY(-2px);
        background: rgba(255, 255, 255, 0.92);
        box-shadow: 0 20px 28px -12px rgba(0, 0, 0, 0.12);
    }
    
    /* Metric cards */
    .metric-card {
        background: rgba(255, 255, 255, 0.9);
        border-radius: 1.5rem;
        padding: 1rem;
        border-left: 6px solid;
        margin-bottom: 0.5rem;
        transition: all 0.2s;
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    
    /* Button styling */
    .stButton > button {
        border-radius: 2rem;
        transition: all 0.2s;
        font-weight: 500;
    }
    
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    
    /* Delete button warning */
    .delete-warning {
        background-color: #fee2e2;
        border-left: 4px solid #ef4444;
        padding: 0.5rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    
    /* Dataframe styling */
    .dataframe {
        border-radius: 1rem;
        overflow: hidden;
    }
    
    /* Hide default Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 5px;
        height: 5px;
    }
    ::-webkit-scrollbar-track {
        background: #ffe6cc;
        border-radius: 20px;
    }
    ::-webkit-scrollbar-thumb {
        background: #f59e0b;
        border-radius: 20px;
    }
</style>
""", unsafe_allow_html=True)

# Database setup
def init_db():
    conn = sqlite3.connect('eunice_mart.db', check_same_thread=False)
    c = conn.cursor()
    
    # Products table
    c.execute('''CREATE TABLE IF NOT EXISTS products
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT NOT NULL,
                  category TEXT,
                  unit TEXT,
                  stock_qty INTEGER DEFAULT 0,
                  price REAL,
                  wholesale_price REAL,
                  type TEXT,
                  icon TEXT,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    # Orders table
    c.execute('''CREATE TABLE IF NOT EXISTS orders
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  order_number TEXT UNIQUE,
                  customer_name TEXT,
                  type TEXT,
                  amount REAL,
                  status TEXT,
                  date TEXT,
                  items TEXT)''')
    
    # Customers table
    c.execute('''CREATE TABLE IF NOT EXISTS customers
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT UNIQUE,
                  segment TEXT,
                  last_order TEXT,
                  credit REAL DEFAULT 0,
                  phone TEXT,
                  email TEXT,
                  address TEXT)''')
    
    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  email TEXT UNIQUE,
                  password TEXT,
                  name TEXT,
                  role TEXT,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    # Settings table
    c.execute('''CREATE TABLE IF NOT EXISTS settings
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  key TEXT UNIQUE,
                  value TEXT)''')
    
    # Insert demo data if empty
    c.execute("SELECT COUNT(*) FROM products")
    if c.fetchone()[0] == 0:
        demo_products = [
            ("Voltic Natural 1.5L", "mineral water", "bottle", 340, 4.50, 38.00, "retail", "fa-droplet"),
            ("Coca-Cola 2L", "soda", "bottle", 125, 12.00, 110.00, "both", "fa-glass-cheers"),
            ("Special Ice Sachet", "mineral water", "sachet (40pcs)", 580, 12.00, 105.00, "retail", "fa-ice-cream"),
            ("Pepsi Can Crate", "wholesale", "24 cans", 48, 110.00, 102.00, "wholesale", "fa-cubes"),
            ("Schweppes Mix Pack", "soda", "18 bottles", 76, 72.00, 68.00, "both", "fa-flask"),
            ("Everest 5L Jug", "water dispenser", "jug", 42, 18.00, 95.00, "retail", "fa-jug-detergent"),
        ]
        c.executemany("INSERT INTO products (name, category, unit, stock_qty, price, wholesale_price, type, icon) VALUES (?,?,?,?,?,?,?,?)", demo_products)
    
    c.execute("SELECT COUNT(*) FROM orders")
    if c.fetchone()[0] == 0:
        demo_orders = [
            ("EM-2403", "Nana Akua Stores", "wholesale", 2400.00, "paid", "2026-03-22", None),
            ("EM-2402", "Osu Spot Retail", "retail", 340.00, "pending", "2026-03-21", None),
            ("EM-2401", "Madina Depot", "wholesale", 6200.00, "shipped", "2026-03-20", None),
            ("EM-2400", "Aburi Wholesale Hub", "wholesale", 4850.00, "paid", "2026-03-19", None),
        ]
        c.executemany("INSERT INTO orders (order_number, customer_name, type, amount, status, date, items) VALUES (?,?,?,?,?,?,?)", demo_orders)
    
    c.execute("SELECT COUNT(*) FROM customers")
    if c.fetchone()[0] == 0:
        demo_customers = [
            ("Nana Akua Stores", "wholesale", "2 days ago", 0, "+233 XX XXX XXXX", "nana@akuastores.com", "Accra"),
            ("Osu Spot", "retail", "yesterday", 120.00, "+233 XX XXX XXXX", "osu@spot.com", "Osu, Accra"),
            ("Madina Depot", "wholesale", "3 days ago", 2300.00, "+233 XX XXX XXXX", "madina@depot.com", "Madina"),
            ("Spintex Mart", "retail", "5 days ago", 0, "+233 XX XXX XXXX", "spintex@mart.com", "Spintex"),
            ("Tema Wholesale Ltd", "wholesale", "1 week ago", 4200.00, "+233 XX XXX XXXX", "tema@wholesale.com", "Tema"),
        ]
        c.executemany("INSERT INTO customers (name, segment, last_order, credit, phone, email, address) VALUES (?,?,?,?,?,?,?)", demo_customers)
    
    c.execute("SELECT COUNT(*) FROM users")
    if c.fetchone()[0] == 0:
        hashed_password = hashlib.sha256("demo123".encode()).hexdigest()
        c.execute("INSERT INTO users (email, password, name, role) VALUES (?,?,?,?)", 
                  ("demo@incredible.com", hashed_password, "Eunice Amoah", "manager"))
    
    # Initialize settings
    c.execute("SELECT COUNT(*) FROM settings WHERE key = 'store_name'")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO settings (key, value) VALUES (?, ?)", ("store_name", "Incredible Studios"))
    c.execute("SELECT COUNT(*) FROM settings WHERE key = 'store_slogan'")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO settings (key, value) VALUES (?, ?)", ("store_slogan", "retail & wholesale hub"))
    
    conn.commit()
    conn.close()

init_db()

# Database helper functions
def get_db_connection():
    return sqlite3.connect('eunice_mart.db', check_same_thread=False)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def get_products():
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT * FROM products ORDER BY id", conn)
    conn.close()
    return df

def get_product_by_id(product_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM products WHERE id = ?", (product_id,))
    product = c.fetchone()
    conn.close()
    if product:
        return {
            'id': product[0],
            'name': product[1],
            'category': product[2],
            'unit': product[3],
            'stock_qty': product[4],
            'price': product[5],
            'wholesale_price': product[6],
            'type': product[7],
            'icon': product[8]
        }
    return None

def add_product(name, category, unit, stock_qty, price, wholesale_price, type):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("INSERT INTO products (name, category, unit, stock_qty, price, wholesale_price, type, icon) VALUES (?,?,?,?,?,?,?,?)",
              (name, category, unit, stock_qty, price, wholesale_price, type, "fa-box"))
    conn.commit()
    conn.close()
    return True

def update_product(product_id, name, category, unit, stock_qty, price, wholesale_price, type):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("""UPDATE products 
                 SET name = ?, category = ?, unit = ?, stock_qty = ?, price = ?, wholesale_price = ?, type = ?
                 WHERE id = ?""",
              (name, category, unit, stock_qty, price, wholesale_price, type, product_id))
    conn.commit()
    conn.close()

def delete_product(product_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("DELETE FROM products WHERE id = ?", (product_id,))
    conn.commit()
    conn.close()

def get_orders():
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT * FROM orders ORDER BY date DESC", conn)
    conn.close()
    return df

def get_order_by_id(order_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
    order = c.fetchone()
    conn.close()
    if order:
        return {
            'id': order[0],
            'order_number': order[1],
            'customer_name': order[2],
            'type': order[3],
            'amount': order[4],
            'status': order[5],
            'date': order[6]
        }
    return None

def add_order(order_number, customer_name, type, amount, status, items=None):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("INSERT INTO orders (order_number, customer_name, type, amount, status, date, items) VALUES (?,?,?,?,?,?,?)",
              (order_number, customer_name, type, amount, status, datetime.now().strftime("%Y-%m-%d"), items))
    conn.commit()
    conn.close()

def update_order(order_id, customer_name, type, amount, status):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("UPDATE orders SET customer_name = ?, type = ?, amount = ?, status = ? WHERE id = ?",
              (customer_name, type, amount, status, order_id))
    conn.commit()
    conn.close()

def delete_order(order_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("DELETE FROM orders WHERE id = ?", (order_id,))
    conn.commit()
    conn.close()

def get_customers():
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT * FROM customers", conn)
    conn.close()
    return df

def get_customer_by_id(customer_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM customers WHERE id = ?", (customer_id,))
    customer = c.fetchone()
    conn.close()
    if customer:
        return {
            'id': customer[0],
            'name': customer[1],
            'segment': customer[2],
            'last_order': customer[3],
            'credit': customer[4],
            'phone': customer[5] if len(customer) > 5 else "",
            'email': customer[6] if len(customer) > 6 else "",
            'address': customer[7] if len(customer) > 7 else ""
        }
    return None

def add_customer(name, segment, credit=0, phone="", email="", address=""):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("INSERT INTO customers (name, segment, last_order, credit, phone, email, address) VALUES (?,?,?,?,?,?,?)",
              (name, segment, "new", credit, phone, email, address))
    conn.commit()
    conn.close()

def update_customer(customer_id, name, segment, credit, phone, email, address):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("UPDATE customers SET name = ?, segment = ?, credit = ?, phone = ?, email = ?, address = ? WHERE id = ?",
              (name, segment, credit, phone, email, address, customer_id))
    conn.commit()
    conn.close()

def delete_customer(customer_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("DELETE FROM customers WHERE id = ?", (customer_id,))
    conn.commit()
    conn.close()

def get_users():
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT id, email, name, role, created_at FROM users", conn)
    conn.close()
    return df

def add_user(email, password, name, role):
    conn = get_db_connection()
    c = conn.cursor()
    hashed_pw = hash_password(password)
    c.execute("INSERT INTO users (email, password, name, role) VALUES (?,?,?,?)",
              (email, hashed_pw, name, role))
    conn.commit()
    conn.close()

def update_user(user_id, email, name, role):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("UPDATE users SET email = ?, name = ?, role = ? WHERE id = ?",
              (email, name, role, user_id))
    conn.commit()
    conn.close()

def delete_user(user_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()

def update_user_password(user_id, new_password):
    conn = get_db_connection()
    c = conn.cursor()
    hashed_pw = hash_password(new_password)
    c.execute("UPDATE users SET password = ? WHERE id = ?", (hashed_pw, user_id))
    conn.commit()
    conn.close()

def authenticate_user(email, password):
    conn = get_db_connection()
    c = conn.cursor()
    hashed_pw = hash_password(password)
    c.execute("SELECT * FROM users WHERE email = ? AND password = ?", (email, hashed_pw))
    user = c.fetchone()
    conn.close()
    return user

def get_setting(key):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT value FROM settings WHERE key = ?", (key,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else None

def update_setting(key, value):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()

# Session state initialization
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_name' not in st.session_state:
    st.session_state.user_name = None
if 'user_role' not in st.session_state:
    st.session_state.user_role = None
if 'edit_product_id' not in st.session_state:
    st.session_state.edit_product_id = None
if 'edit_order_id' not in st.session_state:
    st.session_state.edit_order_id = None
if 'edit_customer_id' not in st.session_state:
    st.session_state.edit_customer_id = None
if 'show_add_product' not in st.session_state:
    st.session_state.show_add_product = False
if 'show_add_order' not in st.session_state:
    st.session_state.show_add_order = False
if 'show_add_customer' not in st.session_state:
    st.session_state.show_add_customer = False

# Authentication pages
def login_page():
    store_name = get_setting("store_name")
    store_slogan = get_setting("store_slogan")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown(f"""
        <div style="text-align: center; margin-bottom: 2rem;">
            <i class="fas fa-leaf" style="font-size: 3rem; color: #10b981;"></i>
            <h1 style="background: linear-gradient(135deg, #0f5e5e, #d97706); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 2.5rem;">{store_name}</h1>
            <p style="color: #6b7280;">{store_slogan}</p>
        </div>
        """, unsafe_allow_html=True)
        
        with st.form("login_form"):
            email = st.text_input("Email", value="demo@incredible.com")
            password = st.text_input("Password", type="password", value="demo123")
            submitted = st.form_submit_button("Access Dashboard", use_container_width=True)
            
            if submitted:
                user = authenticate_user(email, password)
                if user:
                    st.session_state.logged_in = True
                    st.session_state.user_name = user[3]
                    st.session_state.user_role = user[4]
                    st.rerun()
                else:
                    st.error("Invalid credentials. Use demo@incredible.com / demo123")

# CRUD Modal Components
def product_crud_modal():
    if st.session_state.edit_product_id is not None:
        product = get_product_by_id(st.session_state.edit_product_id)
        if product:
            st.markdown("### ✏️ Edit Product")
            
            with st.form("edit_product_form"):
                name = st.text_input("Product Name", value=product['name'])
                category = st.text_input("Category", value=product['category'])
                unit = st.text_input("Unit", value=product['unit'])
                stock_qty = st.number_input("Stock Quantity", value=int(product['stock_qty']))
                price = st.number_input("Retail Price (GH₵)", value=float(product['price']))
                wholesale_price = st.number_input("Wholesale Price (GH₵)", value=float(product['wholesale_price']))
                type_options = ["retail", "wholesale", "both"]
                type_index = type_options.index(product['type']) if product['type'] in type_options else 0
                type_selected = st.selectbox("Type", type_options, index=type_index)
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button("💾 Save Changes", use_container_width=True):
                        update_product(product['id'], name, category, unit, stock_qty, price, wholesale_price, type_selected)
                        st.success("Product updated successfully!")
                        st.session_state.edit_product_id = None
                        st.rerun()
                with col2:
                    if st.form_submit_button("❌ Cancel", use_container_width=True):
                        st.session_state.edit_product_id = None
                        st.rerun()
    elif st.session_state.show_add_product:
        st.markdown("### ➕ Add New Product")
        with st.form("add_product_form"):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Product Name")
                category = st.text_input("Category")
                unit = st.text_input("Unit")
            with col2:
                stock_qty = st.number_input("Stock Quantity", min_value=0)
                price = st.number_input("Retail Price (GH₵)", min_value=0.0, step=0.5)
                wholesale_price = st.number_input("Wholesale Price (GH₵)", min_value=0.0, step=0.5)
            type_selected = st.selectbox("Type", ["retail", "wholesale", "both"])
            
            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("➕ Add Product", use_container_width=True):
                    if name and category:
                        add_product(name, category, unit, stock_qty, price, wholesale_price, type_selected)
                        st.success(f"Product '{name}' added successfully!")
                        st.session_state.show_add_product = False
                        st.rerun()
                    else:
                        st.error("Please fill in required fields")
            with col2:
                if st.form_submit_button("❌ Cancel", use_container_width=True):
                    st.session_state.show_add_product = False
                    st.rerun()

def order_crud_modal():
    if st.session_state.edit_order_id is not None:
        order = get_order_by_id(st.session_state.edit_order_id)
        if order:
            st.markdown("### ✏️ Edit Order")
            
            with st.form("edit_order_form"):
                customer_name = st.text_input("Customer Name", value=order['customer_name'])
                type_options = ["retail", "wholesale"]
                type_index = type_options.index(order['type']) if order['type'] in type_options else 0
                type_selected = st.selectbox("Order Type", type_options, index=type_index)
                amount = st.number_input("Amount (GH₵)", value=float(order['amount']), min_value=0.0)
                status_options = ["pending", "paid", "shipped", "delivered"]
                status_index = status_options.index(order['status']) if order['status'] in status_options else 0
                status_selected = st.selectbox("Status", status_options, index=status_index)
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button("💾 Save Changes", use_container_width=True):
                        update_order(order['id'], customer_name, type_selected, amount, status_selected)
                        st.success("Order updated successfully!")
                        st.session_state.edit_order_id = None
                        st.rerun()
                with col2:
                    if st.form_submit_button("❌ Cancel", use_container_width=True):
                        st.session_state.edit_order_id = None
                        st.rerun()
    elif st.session_state.show_add_order:
        st.markdown("### ➕ Create New Order")
        with st.form("add_order_form"):
            col1, col2 = st.columns(2)
            with col1:
                order_num = st.text_input("Order Number", value=f"EM-{datetime.now().strftime('%y%m%d%H%M%S')}")
                customer_name = st.text_input("Customer Name")
            with col2:
                type_selected = st.selectbox("Order Type", ["retail", "wholesale"])
                amount = st.number_input("Amount (GH₵)", min_value=0.0, step=10.0)
            status_selected = st.selectbox("Status", ["pending", "paid", "shipped", "delivered"])
            
            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("➕ Create Order", use_container_width=True):
                    if customer_name and amount > 0:
                        add_order(order_num, customer_name, type_selected, amount, status_selected)
                        st.success(f"Order {order_num} created successfully!")
                        st.session_state.show_add_order = False
                        st.rerun()
                    else:
                        st.error("Please fill in all fields")
            with col2:
                if st.form_submit_button("❌ Cancel", use_container_width=True):
                    st.session_state.show_add_order = False
                    st.rerun()

def customer_crud_modal():
    if st.session_state.edit_customer_id is not None:
        customer = get_customer_by_id(st.session_state.edit_customer_id)
        if customer:
            st.markdown("### ✏️ Edit Customer")
            
            with st.form("edit_customer_form"):
                name = st.text_input("Business Name", value=customer['name'])
                segment_options = ["retail", "wholesale"]
                segment_index = segment_options.index(customer['segment']) if customer['segment'] in segment_options else 0
                segment_selected = st.selectbox("Segment", segment_options, index=segment_index)
                credit = st.number_input("Credit (GH₵)", value=float(customer['credit']), min_value=0.0)
                phone = st.text_input("Phone", value=customer.get('phone', ''))
                email = st.text_input("Email", value=customer.get('email', ''))
                address = st.text_area("Address", value=customer.get('address', ''))
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button("💾 Save Changes", use_container_width=True):
                        update_customer(customer['id'], name, segment_selected, credit, phone, email, address)
                        st.success("Customer updated successfully!")
                        st.session_state.edit_customer_id = None
                        st.rerun()
                with col2:
                    if st.form_submit_button("❌ Cancel", use_container_width=True):
                        st.session_state.edit_customer_id = None
                        st.rerun()
    elif st.session_state.show_add_customer:
        st.markdown("### ➕ Add New Customer")
        with st.form("add_customer_form"):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Business Name")
                segment_selected = st.selectbox("Segment", ["retail", "wholesale"])
            with col2:
                credit = st.number_input("Credit Limit (GH₵)", min_value=0.0, step=100.0)
            phone = st.text_input("Phone Number")
            email = st.text_input("Email Address")
            address = st.text_area("Address")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("➕ Add Customer", use_container_width=True):
                    if name:
                        add_customer(name, segment_selected, credit, phone, email, address)
                        st.success(f"Customer '{name}' added successfully!")
                        st.session_state.show_add_customer = False
                        st.rerun()
                    else:
                        st.error("Please enter customer name")
            with col2:
                if st.form_submit_button("❌ Cancel", use_container_width=True):
                    st.session_state.show_add_customer = False
                    st.rerun()

# Main app pages
def dashboard_page():
    store_name = get_setting("store_name")
    st.markdown(f'<h2 style="font-size: 1.875rem; font-weight: 700;"><i class="fas fa-chart-line" style="color: #0d9488;"></i> {store_name} Dashboard</h2>', unsafe_allow_html=True)
    
    products_df = get_products()
    orders_df = get_orders()
    customers_df = get_customers()
    
    # Metrics
    today_str = datetime.now().strftime("%Y-%m-%d")
    total_revenue_today = orders_df[orders_df['date'] == today_str]['amount'].sum() if not orders_df.empty else 0
    wholesale_orders = len(orders_df[orders_df['type'] == 'wholesale']) if not orders_df.empty else 0
    retail_customers = len(customers_df[customers_df['segment'] == 'retail']) if not customers_df.empty else 0
    low_stock = len(products_df[products_df['stock_qty'] < 50]) if not products_df.empty else 0
    total_products = len(products_df)
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card" style="border-left-color: #0d9488;">
            <p style="color: #6b7280; font-size: 0.75rem;">Today's revenue</p>
            <p style="font-size: 1.5rem; font-weight: 800;">GH₵ {total_revenue_today:,.0f}</p>
            <span style="color: #059669;">+22% vs yesterday</span>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card" style="border-left-color: #d97706;">
            <p style="color: #6b7280; font-size: 0.75rem;">Wholesale orders</p>
            <p style="font-size: 1.5rem; font-weight: 800;">{wholesale_orders}</p>
            <span style="color: #d97706;">+8 new today</span>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card" style="border-left-color: #e11d48;">
            <p style="color: #6b7280; font-size: 0.75rem;">Active customers</p>
            <p style="font-size: 1.5rem; font-weight: 800;">{retail_customers}</p>
            <span style="color: #e11d48;">+12 this week</span>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-card" style="border-left-color: #65a30d;">
            <p style="color: #6b7280; font-size: 0.75rem;">Low stock alerts</p>
            <p style="font-size: 1.5rem; font-weight: 800;">{low_stock}</p>
            <span style="color: #65a30d;">restock soon</span>
        </div>
        """, unsafe_allow_html=True)
    
    with col5:
        st.markdown(f"""
        <div class="metric-card" style="border-left-color: #8b5cf6;">
            <p style="color: #6b7280; font-size: 0.75rem;">Total Products</p>
            <p style="font-size: 1.5rem; font-weight: 800;">{total_products}</p>
            <span style="color: #8b5cf6;">in inventory</span>
        </div>
        """, unsafe_allow_html=True)
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.subheader("Weekly Performance (GH₵)")
        if not orders_df.empty:
            orders_df_copy = orders_df.copy()
            orders_df_copy['date'] = pd.to_datetime(orders_df_copy['date'])
            weekly = orders_df_copy.groupby(orders_df_copy['date'].dt.day_name())['amount'].sum().reindex(
                ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            ).fillna(0)
            fig = px.bar(x=weekly.index, y=weekly.values, color=weekly.values, 
                        color_continuous_scale='Tealgrn', title="Sales by Day")
            fig.update_layout(showlegend=False, height=300, margin=dict(l=0, r=0, t=40, b=0))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No order data available")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.subheader("Recent Orders")
        if not orders_df.empty:
            recent_orders = orders_df.head(5)[['order_number', 'customer_name', 'amount', 'status']]
            for _, row in recent_orders.iterrows():
                col_a, col_b, col_c = st.columns([2, 1.5, 1])
                with col_a:
                    st.write(f"📦 {row['order_number']}")
                with col_b:
                    st.write(f"{row['customer_name']}")
                with col_c:
                    status_color = "🟢" if row['status'] == 'paid' else "🟡" if row['status'] == 'pending' else "🔵"
                    st.write(f"{status_color} {row['status']}")
        else:
            st.info("No orders found")
        st.markdown('</div>', unsafe_allow_html=True)

def products_page():
    st.markdown('<h2 style="font-size: 1.875rem; font-weight: 700;"><i class="fas fa-cubes"></i> Inventory Management</h2>', unsafe_allow_html=True)
    
    # Search and filter
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        search = st.text_input("🔍 Search products...", placeholder="Search by name or category", key="product_search")
    with col2:
        category_filter = st.selectbox("Filter by Type", ["All", "retail", "wholesale", "both"], key="product_filter")
    with col3:
        if st.button("➕ Add New Product", use_container_width=True):
            st.session_state.edit_product_id = None
            st.session_state.show_add_product = True
    
    products_df = get_products()
    
    # Apply filters
    if search:
        products_df = products_df[products_df['name'].str.contains(search, case=False) | 
                                   products_df['category'].str.contains(search, case=False)]
    if category_filter != "All":
        products_df = products_df[products_df['type'] == category_filter]
    
    # CRUD Modal
    if st.session_state.show_add_product or st.session_state.edit_product_id is not None:
        with st.expander("📦 Product Management", expanded=True):
            product_crud_modal()
    
    # Display products in table with action buttons
    if not products_df.empty:
        st.markdown("### 📋 Product List")
        
        # Use a container for each product to avoid state conflicts
        for idx, (_, product) in enumerate(products_df.iterrows()):
            with st.container():
                cols = st.columns([2, 1.5, 1, 1, 1, 0.7, 0.7])
                with cols[0]:
                    st.write(f"**{product['name']}**")
                with cols[1]:
                    st.write(product['category'])
                with cols[2]:
                    st.write(f"{product['stock_qty']} {product['unit']}")
                with cols[3]:
                    st.write(f"GH₵ {product['price']:.2f}")
                with cols[4]:
                    if product['type'] == 'retail':
                        st.write("🟢 Retail")
                    elif product['type'] == 'wholesale':
                        st.write("🔵 Wholesale")
                    else:
                        st.write("🟣 Both")
                with cols[5]:
                    edit_key = f"edit_product_{product['id']}"
                    if st.button("✏️", key=edit_key):
                        st.session_state.edit_product_id = int(product['id'])
                        st.session_state.show_add_product = True
                        st.rerun()
                with cols[6]:
                    delete_key = f"delete_product_{product['id']}"
                    if delete_key not in st.session_state:
                        st.session_state[delete_key] = False
                    
                    if st.button("🗑️", key=f"delete_btn_{product['id']}"):
                        if not st.session_state[delete_key]:
                            st.session_state[delete_key] = True
                            st.warning(f"⚠️ Click again to delete '{product['name']}'")
                        else:
                            delete_product(product['id'])
                            st.success(f"Product '{product['name']}' deleted!")
                            st.session_state[delete_key] = False
                            st.rerun()
                st.divider()
    else:
        st.info("No products found")

def orders_page():
    st.markdown('<h2 style="font-size: 1.875rem; font-weight: 700;"><i class="fas fa-clipboard-list"></i> Order Management</h2>', unsafe_allow_html=True)
    
    orders_df = get_orders()
    
    # CRUD Modal
    if st.button("➕ Create New Order", use_container_width=True):
        st.session_state.edit_order_id = None
        st.session_state.show_add_order = True
    
    if st.session_state.show_add_order or st.session_state.edit_order_id is not None:
        with st.expander("📝 Order Management", expanded=True):
            order_crud_modal()
    
    # Display orders table
    if not orders_df.empty:
        st.markdown("### 📋 All Orders")
        
        for _, order in orders_df.iterrows():
            with st.container():
                cols = st.columns([1.5, 1.5, 1, 1, 1, 0.7, 0.7])
                with cols[0]:
                    st.write(f"**{order['order_number']}**")
                with cols[1]:
                    st.write(order['customer_name'])
                with cols[2]:
                    st.write("🟢 Retail" if order['type'] == 'retail' else "🔵 Wholesale")
                with cols[3]:
                    st.write(f"GH₵ {order['amount']:,.2f}")
                with cols[4]:
                    if order['status'] == 'paid':
                        st.write("✅ Paid")
                    elif order['status'] == 'pending':
                        st.write("⏳ Pending")
                    elif order['status'] == 'shipped':
                        st.write("🚚 Shipped")
                    else:
                        st.write("📦 Delivered")
                with cols[5]:
                    if st.button("✏️", key=f"edit_order_{order['id']}"):
                        st.session_state.edit_order_id = int(order['id'])
                        st.session_state.show_add_order = True
                        st.rerun()
                with cols[6]:
                    delete_key = f"delete_order_{order['id']}"
                    if delete_key not in st.session_state:
                        st.session_state[delete_key] = False
                    
                    if st.button("🗑️", key=f"delete_order_btn_{order['id']}"):
                        if not st.session_state[delete_key]:
                            st.session_state[delete_key] = True
                            st.warning(f"⚠️ Click again to delete order {order['order_number']}")
                        else:
                            delete_order(order['id'])
                            st.success(f"Order {order['order_number']} deleted!")
                            st.session_state[delete_key] = False
                            st.rerun()
                st.divider()
    else:
        st.info("No orders found")

def customers_page():
    st.markdown('<h2 style="font-size: 1.875rem; font-weight: 700;"><i class="fas fa-handshake"></i> Customer Management</h2>', unsafe_allow_html=True)
    
    customers_df = get_customers()
    
    # CRUD Modal
    if st.button("➕ Add New Customer", use_container_width=True):
        st.session_state.edit_customer_id = None
        st.session_state.show_add_customer = True
    
    if st.session_state.show_add_customer or st.session_state.edit_customer_id is not None:
        with st.expander("👥 Customer Management", expanded=True):
            customer_crud_modal()
    
    # Display customers
    if not customers_df.empty:
        st.markdown("### 📋 Customer Directory")
        
        for idx, (_, customer) in enumerate(customers_df.iterrows()):
            with st.container():
                cols = st.columns([2, 1, 1, 1.5, 0.7, 0.7])
                with cols[0]:
                    st.write(f"**{customer['name']}**")
                with cols[1]:
                    st.write("🟢 Retail" if customer['segment'] == 'retail' else "🔵 Wholesale")
                with cols[2]:
                    st.write(f"GH₵ {customer['credit']:,.2f}")
                with cols[3]:
                    phone = customer.get('phone', '')
                    st.write(f"📞 {phone}" if phone else "—")
                with cols[4]:
                    if st.button("✏️", key=f"edit_cust_{customer['id']}"):
                        st.session_state.edit_customer_id = int(customer['id'])
                        st.session_state.show_add_customer = True
                        st.rerun()
                with cols[5]:
                    delete_key = f"delete_cust_{customer['id']}"
                    if delete_key not in st.session_state:
                        st.session_state[delete_key] = False
                    
                    if st.button("🗑️", key=f"delete_cust_btn_{customer['id']}"):
                        if not st.session_state[delete_key]:
                            st.session_state[delete_key] = True
                            st.warning(f"⚠️ Click again to delete '{customer['name']}'")
                        else:
                            delete_customer(customer['id'])
                            st.success(f"Customer '{customer['name']}' deleted!")
                            st.session_state[delete_key] = False
                            st.rerun()
                st.divider()
    else:
        st.info("No customers found")

def reports_page():
    st.markdown('<h2 style="font-size: 1.875rem; font-weight: 700;"><i class="fas fa-chart-column"></i> Sales Reports & Analytics</h2>', unsafe_allow_html=True)
    
    orders_df = get_orders()
    products_df = get_products()
    
    if not orders_df.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            # Sales by type pie chart
            sales_by_type = orders_df.groupby('type')['amount'].sum()
            fig1 = px.pie(values=sales_by_type.values, names=sales_by_type.index, 
                         title="Sales Distribution by Type", color_discrete_sequence=['#0d9488', '#d97706'])
            st.plotly_chart(fig1, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            # Sales trend
            orders_df_copy = orders_df.copy()
            orders_df_copy['date'] = pd.to_datetime(orders_df_copy['date'])
            daily_sales = orders_df_copy.groupby('date')['amount'].sum().reset_index()
            fig2 = px.line(daily_sales, x='date', y='amount', title="Sales Trend",
                          labels={'amount': 'Revenue (GH₵)', 'date': 'Date'})
            fig2.update_traces(line_color='#0d9488', line_width=3)
            st.plotly_chart(fig2, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Summary metrics
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Revenue", f"GH₵ {orders_df['amount'].sum():,.2f}")
        with col2:
            st.metric("Average Order Value", f"GH₵ {orders_df['amount'].mean():,.2f}")
        with col3:
            st.metric("Total Orders", len(orders_df))
        with col4:
            st.metric("Pending Orders", len(orders_df[orders_df['status'] == 'pending']))
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Stock report
        st.markdown('<div class="glass-card" style="margin-top: 1rem;">', unsafe_allow_html=True)
        st.subheader("Inventory Status")
        low_stock_df = products_df[products_df['stock_qty'] < 50]
        if not low_stock_df.empty:
            st.warning(f"⚠️ {len(low_stock_df)} products are low on stock")
            st.dataframe(low_stock_df[['name', 'stock_qty', 'unit']], use_container_width=True, hide_index=True)
        else:
            st.success("All products have sufficient stock levels")
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Export option
        if st.button("📥 Export Report (CSV)", use_container_width=True):
            csv = orders_df.to_csv(index=False)
            st.download_button("Download Orders CSV", csv, "eunice_mart_orders.csv", "text/csv")
    else:
        st.info("No order data available for reporting")

def settings_page():
    st.markdown('<h2 style="font-size: 1.875rem; font-weight: 700;"><i class="fas fa-sliders-h"></i> Business Settings</h2>', unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["🏪 Store Settings", "👥 User Management", "⚙️ System Preferences"])
    
    with tab1:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.subheader("Store Information")
            
            store_name = st.text_input("Store Name", value=get_setting("store_name") or "Incredible Studios")
            store_slogan = st.text_input("Store Slogan", value=get_setting("store_slogan") or "retail & wholesale hub")
            
            if st.button("💾 Save Store Information", use_container_width=True):
                update_setting("store_name", store_name)
                update_setting("store_slogan", store_slogan)
                st.success("Store information updated successfully!")
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.subheader("Tax & Pricing")
            tax_rate = st.number_input("Wholesale Tax Rate (%)", min_value=0.0, max_value=100.0, value=3.0, step=0.5)
            markup = st.number_input("Retail Markup (%)", min_value=0.0, max_value=200.0, value=25.0, step=5.0)
            if st.button("💾 Save Tax Settings", use_container_width=True):
                update_setting("tax_rate", str(tax_rate))
                update_setting("markup", str(markup))
                st.success(f"Tax settings updated: {tax_rate}% tax, {markup}% markup")
            st.markdown('</div>', unsafe_allow_html=True)
    
    with tab2:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.subheader("User Management")
        
        # Add new user
        with st.expander("➕ Add New User", expanded=False):
            with st.form("add_user_form"):
                col1, col2 = st.columns(2)
                with col1:
                    new_email = st.text_input("Email")
                    new_name = st.text_input("Full Name")
                with col2:
                    new_password = st.text_input("Password", type="password")
                    new_role = st.selectbox("Role", ["manager", "staff", "viewer"])
                
                if st.form_submit_button("Add User", use_container_width=True):
                    if new_email and new_password and new_name:
                        try:
                            add_user(new_email, new_password, new_name, new_role)
                            st.success(f"User {new_name} added successfully!")
                            st.rerun()
                        except sqlite3.IntegrityError:
                            st.error("Email already exists!")
                    else:
                        st.error("Please fill in all fields")
        
        # Display users
        users_df = get_users()
        if not users_df.empty:
            st.markdown("### Existing Users")
            for _, user in users_df.iterrows():
                with st.container():
                    cols = st.columns([2, 1.5, 1, 1, 0.7])
                    with cols[0]:
                        st.write(f"**{user['name']}**")
                    with cols[1]:
                        st.write(user['email'])
                    with cols[2]:
                        if user['role'] == 'manager':
                            st.write("🟢 Manager")
                        elif user['role'] == 'staff':
                            st.write("🔵 Staff")
                        else:
                            st.write("⚪ Viewer")
                    with cols[3]:
                        reset_key = f"reset_pw_{user['id']}"
                        if reset_key not in st.session_state:
                            st.session_state[reset_key] = False
                        
                        if st.button("🔑", key=f"reset_btn_{user['id']}"):
                            st.session_state[reset_key] = not st.session_state[reset_key]
                        
                        if st.session_state[reset_key]:
                            new_pw = st.text_input("New Password", type="password", key=f"new_pw_{user['id']}")
                            if st.button("Update Password", key=f"update_pw_{user['id']}"):
                                if new_pw:
                                    update_user_password(user['id'], new_pw)
                                    st.success("Password updated!")
                                    st.session_state[reset_key] = False
                                    st.rerun()
                    with cols[4]:
                        if user['email'] != "demo@incredible.com":
                            delete_key = f"delete_user_{user['id']}"
                            if delete_key not in st.session_state:
                                st.session_state[delete_key] = False
                            
                            if st.button("🗑️", key=f"delete_user_btn_{user['id']}"):
                                if not st.session_state[delete_key]:
                                    st.session_state[delete_key] = True
                                    st.warning(f"⚠️ Click again to delete {user['name']}")
                                else:
                                    delete_user(user['id'])
                                    st.success(f"User {user['name']} deleted!")
                                    st.session_state[delete_key] = False
                                    st.rerun()
                    st.divider()
        st.markdown('</div>', unsafe_allow_html=True)
    
    with tab3:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.subheader("Notification Settings")
        email_notifications = st.checkbox("Email notifications for new orders", value=True)
        low_stock_alerts = st.checkbox("Low stock alerts", value=True)
        weekly_report = st.checkbox("Weekly sales report", value=True)
        
        if st.button("💾 Save Notification Settings", use_container_width=True):
            update_setting("email_notifications", str(email_notifications))
            update_setting("low_stock_alerts", str(low_stock_alerts))
            update_setting("weekly_report", str(weekly_report))
            st.success("Notification preferences saved!")
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Data Management
        st.markdown('<div class="glass-card" style="margin-top: 1rem;">', unsafe_allow_html=True)
        st.subheader("Data Management")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📤 Backup Database", use_container_width=True):
                backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
                shutil.copy('eunice_mart.db', backup_name)
                with open(backup_name, "rb") as f:
                    st.download_button("Download Backup", f, backup_name, "application/octet-stream")
        
        with col2:
            if st.button("🔄 Reset Demo Data", use_container_width=True):
                confirm_key = "confirm_reset"
                if confirm_key not in st.session_state:
                    st.session_state[confirm_key] = False
                
                if not st.session_state[confirm_key]:
                    st.session_state[confirm_key] = True
                    st.warning("⚠️ Click again to confirm reset all data!")
                else:
                    os.remove('eunice_mart.db')
                    init_db()
                    st.success("Database reset to demo data!")
                    st.session_state[confirm_key] = False
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# Main navigation
def main():
    if not st.session_state.logged_in:
        login_page()
        return
    
    # Sidebar navigation
    with st.sidebar:
        store_name = get_setting("store_name") or "Incredible Studios"
        st.markdown(f"""
        <div style="text-align: center; margin-bottom: 2rem;">
            <div style="width: 60px; height: 60px; background: linear-gradient(135deg, #0d9488, #d97706); border-radius: 9999px; display: flex; align-items: center; justify-content: center; margin: 0 auto 0.75rem auto;">
                <i class="fas fa-hand-holding-droplet" style="font-size: 2rem; color: white;"></i>
            </div>
            <h3 style="margin: 0;">{store_name}</h3>
            <p style="font-size: 0.75rem; color: #6b7280;">retail + wholesale hub</p>
            <hr>
            <p style="font-size: 0.875rem;"><i class="fas fa-user-circle"></i> {st.session_state.user_name}</p>
            <p style="font-size: 0.75rem; color: #6b7280;">Role: {st.session_state.user_role}</p>
        </div>
        """, unsafe_allow_html=True)
        
        selected = option_menu(
            menu_title=None,
            options=["Dashboard", "Products", "Orders", "Customers", "Reports", "Settings"],
            icons=["chart-pie", "boxes", "truck", "users", "chart-line", "gear"],
            menu_icon="cast",
            default_index=0,
            styles={
                "container": {"padding": "0!important", "background-color": "transparent"},
                "icon": {"color": "#d97706", "font-size": "1rem"},
                "nav-link": {"font-size": "0.9rem", "text-align": "left", "margin": "0.25rem 0", "border-radius": "0.75rem"},
                "nav-link-selected": {"background-color": "#f97316"},
            }
        )
        
        st.markdown("<hr>", unsafe_allow_html=True)
        if st.button("🚪 Logout", use_container_width=True):
            # Clear all session state
            for key in list(st.session_state.keys()):
                if key not in ['logged_in', 'user_name', 'user_role']:
                    del st.session_state[key]
            st.session_state.logged_in = False
            st.session_state.user_name = None
            st.session_state.user_role = None
            st.rerun()
    
    # Page router
    if selected == "Dashboard":
        dashboard_page()
    elif selected == "Products":
        products_page()
    elif selected == "Orders":
        orders_page()
    elif selected == "Customers":
        customers_page()
    elif selected == "Reports":
        reports_page()
    elif selected == "Settings":
        settings_page()
    
    # Footer
    store_name = get_setting("store_name") or "Incredible Studios"
    st.markdown(f"""
    <hr>
    <div style="text-align: center; font-size: 0.75rem; color: #6b7280; padding: 1rem;">
        <i class="fas fa-store"></i> {store_name} © 2026 — retail & wholesale ecosystem
        <i class="fas fa-leaf" style="margin-left: 0.5rem; color: #10b981;"></i> sustainable sourcing
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()