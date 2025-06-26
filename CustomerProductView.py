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
                    SELECT c.customer_name, \
                           p.product_name, \
                           p.product_type, \
                           l.quantity, \
                           l.issue_date, \
                           l.expiry_date, \
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


def show_customer_product_view():
    st.set_page_config(page_title="Customer Product View", layout="wide")

    if 'logged_in' not in st.session_state or not st.session_state.logged_in:
        st.warning("Please log in to access this page.")
        return

    st.title("Customer Product View")
    st.markdown("---")

    # Get all customers for dropdown
    customers = get_all_customers()
    customer_options = {f"{c['customer_id']} - {c['customer_name']}": c['customer_id'] for c in customers}

    # Customer selection
    selected_customer = st.selectbox(
        "Select Customer",
        options=["All Customers"] + list(customer_options.keys()),
        key="customer_select"
    )

    # Get product data
    customer_id = customer_options[selected_customer.split(" - ")[0]] if selected_customer != "All Customers" else None
    products = get_customer_products(customer_id)

    if products:
        # Convert to DataFrame
        df = pd.DataFrame(products)

        # Convert dates to datetime.date objects
        df['issue_date'] = pd.to_datetime(df['issue_date']).dt.date
        df['expiry_date'] = pd.to_datetime(df['expiry_date']).dt.date

        # Get current date as date object
        current_date = datetime.now().date()

        # Add filtering options
        st.subheader("Filter Products")
        col1, col2 = st.columns(2)

        with col1:
            # Product type filter
            product_types = df['product_type'].unique()
            selected_types = st.multiselect(
                "Filter by Product Type",
                options=product_types,
                default=product_types,
                key="type_filter"
            )

        with col2:
            # Status filter
            status_options = ["Active", "Expired", "All"]
            selected_status = st.selectbox(
                "Filter by Status",
                options=status_options,
                key="status_filter"
            )

        # Apply filters
        filtered_df = df[df['product_type'].isin(selected_types)]

        if selected_status == "Active":
            filtered_df = filtered_df[filtered_df['expiry_date'] >= current_date]
        elif selected_status == "Expired":
            filtered_df = filtered_df[filtered_df['expiry_date'] < current_date]

        # Display results
        st.subheader("Customer Products")

        # Format the DataFrame for display
        display_df = filtered_df.drop(columns=['license_id'])

        # Add status column
        display_df['status'] = display_df['expiry_date'].apply(
            lambda x: "Active" if x >= current_date else "Expired"
        )

        # Reorder columns
        display_df = display_df[[
            'customer_name', 'product_name', 'product_type',
            'quantity', 'issue_date', 'expiry_date', 'status'
        ]]

        st.dataframe(
            display_df,
            use_container_width=True,
            column_config={
                "quantity": st.column_config.NumberColumn("Quantity", format="%d"),
                "issue_date": st.column_config.DateColumn("Issue Date"),
                "expiry_date": st.column_config.DateColumn("Expiry Date")
            }
        )

        # Show summary metrics
        st.subheader("Summary")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Products", len(filtered_df))
        with col2:
            active = len(filtered_df[filtered_df['expiry_date'] >= current_date])
            st.metric("Active Licenses", active)
        with col3:
            expired = len(filtered_df[filtered_df['expiry_date'] < current_date])
            st.metric("Expired Licenses", expired)
    else:
        st.info("No products found for selected customer")


if __name__ == "__main__":
    show_customer_product_view()