# CustomerProductView.py
import streamlit as st
import mysql.connector
import pandas as pd
from mysql.connector import Error
from datetime import datetime


def get_db_connection():
    try:
        return mysql.connector.connect(
            host="localhost",
            user="root",
            password="root",
            database="Corporate IT Solutions"
        )
    except Error as e:
        st.error(f"Database error: {e}")
        return None


def get_customer_products(customer_id=None):
    """Retrieve products associated with customers"""
    conn = get_db_connection()
    if conn:
        try:
            query = """
                    SELECT c.customer_name,
                           p.product_name,
                           p.product_type,
                           l.quantity,
                           l.issue_date,
                           l.expiry_date,
                           l.license_id
                    FROM licenses l
                             JOIN customers c ON l.customer_id = c.customer_id
                             JOIN products p ON l.product_id = p.product_id \
                    """
            params = ()

            if customer_id:
                query += " WHERE c.customer_id = %s"
                params = (customer_id,)

            query += " ORDER BY l.expiry_date ASC"

            cursor = conn.cursor(dictionary=True)
            cursor.execute(query, params)
            return cursor.fetchall()
        except Error as e:
            st.error(f"Database error: {e}")
            return []
        finally:
            if conn.is_connected():
                conn.close()
    return []


def get_all_customers():
    """Retrieve all customers for dropdown"""
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT customer_id, customer_name FROM customers ORDER BY customer_name")
            return cursor.fetchall()
        except Error as e:
            st.error(f"Database error: {e}")
            return []
        finally:
            if conn.is_connected():
                conn.close()
    return []

def get_customer_count():
    """Get total number of customers"""
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM customers")
            return cursor.fetchone()[0]
        except Error as e:
            st.error(f"Database error: {e}")
            return 0
        finally:
            if conn.is_connected():
                conn.close()
    return 0


def get_license_stats():
    """Get active and expired license counts"""
    conn = get_db_connection()
    if conn:
        try:
            query = """
                    SELECT SUM(CASE WHEN expiry_date >= CURDATE() THEN 1 ELSE 0 END) as active, \
                           SUM(CASE WHEN expiry_date < CURDATE() THEN 1 ELSE 0 END)  as expired
                    FROM licenses \
                    """
            cursor = conn.cursor(dictionary=True)
            cursor.execute(query)
            return cursor.fetchone()
        except Error as e:
            st.error(f"Database error: {e}")
            return {'active': 0, 'expired': 0}
        finally:
            if conn.is_connected():
                conn.close()
    return {'active': 0, 'expired': 0}



def show_customer_product_view():
    st.set_page_config(page_title="Customer Product View", layout="wide")

    if 'logged_in' not in st.session_state or not st.session_state.logged_in:
        st.warning("Please log in to access this page.")
        return

    st.title("Customer Product View")


    total_customers = int(get_customer_count())

    license_stats_raw = get_license_stats()
    license_stats = {
        'active': int(license_stats_raw['active']),
        'expired': int(license_stats_raw['expired']),
    }

    # Create metrics columns
    with st.expander("📊 License Metrics", expanded=True):
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                label="Total Customers",
                value=total_customers,
                delta="View all customers",
                help="Total number of customers"
            )

        with col2:
            st.metric(
                label="Active Licenses",
                value=license_stats['active'],
                delta="See details",
                help="Licenses currently in use"
            )

        with col3:
            st.metric(
                label="Expired Licenses",
                value=license_stats['expired'],
                delta="Needs attention",
                delta_color="inverse",
                help="Licenses requiring renewal"
            )

    # ===== LICENSE STATUS VISUALIZATION =====


    # Get all customers for dropdown
    customers = get_all_customers()
    customer_options = {f"{c['customer_id']} - {c['customer_name']}": c['customer_id'] for c in customers}

    # Get product data
    products = get_customer_products()

    if not products:
        st.info("No data uploaded - no customer products found in the database")
        return

    if products:
        # Convert to DataFrame
        df = pd.DataFrame(products)

        # Convert dates to datetime.date objects
        df['issue_date'] = pd.to_datetime(df['issue_date']).dt.date
        df['expiry_date'] = pd.to_datetime(df['expiry_date']).dt.date

        # Get current date as date object
        current_date = datetime.now().date()

        # Add status column
        df['status'] = df['expiry_date'].apply(
            lambda x: "Active" if x >= current_date else "Expired"
        )

        # Add filtering options
        st.subheader("Filters")
        col1, col2 = st.columns(2)

        with col1:
            # Customer filter
            all_customers = ["All Customers"] + sorted(df['customer_name'].unique().tolist())
            selected_customer = st.selectbox(
                "Filter by Customer",
                options=all_customers,
                key="customer_filter"
            )

            # Product name filter
            all_products = ["All Products"] + sorted(df['product_name'].unique().tolist())
            selected_product = st.selectbox(
                "Filter by Product Name",
                options=all_products,
                key="product_filter"
            )

        with col2:
            # Product type filter
            all_types = ["All Types"] + sorted(df['product_type'].unique().tolist())
            selected_type = st.selectbox(
                "Filter by Product Type",
                options=all_types,
                key="type_filter"
            )

            # Status filter
            status_options = ["All Statuses", "Active", "Expired"]
            selected_status = st.selectbox(
                "Filter by Status",
                options=status_options,
                key="status_filter"
            )

        # Apply filters
        filtered_df = df.copy()

        if selected_customer != "All Customers":
            filtered_df = filtered_df[filtered_df['customer_name'] == selected_customer]

        if selected_product != "All Products":
            filtered_df = filtered_df[filtered_df['product_name'] == selected_product]

        if selected_type != "All Types":
            filtered_df = filtered_df[filtered_df['product_type'] == selected_type]

        if selected_status != "All Statuses":
            filtered_df = filtered_df[filtered_df['status'] == selected_status]

        # Display results
        st.subheader("Customer Products")

        # Reorder columns for display with new names
        display_df = filtered_df[[
            'customer_name',
            'product_name',
            'product_type',
            'quantity',
            'issue_date',
            'expiry_date',
            'status'
        ]]

        # Rename columns for display
        display_df = display_df.rename(columns={
            'customer_name': 'Customer',
            'product_name': 'Product',
            'product_type': 'Product Type',
            'quantity': 'Quantity',
            'issue_date': 'Issue Date',
            'expiry_date': 'Expiry Date',
            'status': 'Status'
        })

        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,  # This removes the index column
            column_config={
                "Quantity": st.column_config.NumberColumn(format="%d"),
                "Issue Date": st.column_config.DateColumn(),
                "Expiry Date": st.column_config.DateColumn()
            }
        )




if __name__ == "__main__":
    show_customer_product_view()