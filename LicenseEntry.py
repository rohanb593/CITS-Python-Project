# LicenseEntry.py

import streamlit as st
import mysql.connector
from mysql.connector import Error
from datetime import datetime
import pandas as pd


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


def get_customers_for_dropdown():
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                           SELECT customer_id, customer_name
                           FROM customers
                           ORDER BY customer_name
                           """)
            return cursor.fetchall()
        except Error as e:
            st.error(f"Database error: {e}")
        finally:
            if conn.is_connected():
                conn.close()
    return []


def get_products_for_dropdown():
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                           SELECT product_id, product_name, default_validity_months
                           FROM products
                           ORDER BY product_name
                           """)
            return cursor.fetchall()
        except Error as e:
            st.error(f"Database error: {e}")
        finally:
            if conn.is_connected():
                conn.close()
    return []


def save_license(license_data):
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                           INSERT INTO licenses
                           (customer_id, product_id, quantity, issue_date, installation_date, validity_period_months,
                            remarks)
                           VALUES (%s, %s, %s, %s, %s, %s, %s)
                           """, license_data)
            conn.commit()
            return True
        except Error as e:
            st.error(f"Database error: {e}")
            return False
        finally:
            if conn.is_connected():
                conn.close()
    return False


def get_all_licenses():
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                           SELECT l.license_id,
                                  c.customer_name,
                                  p.product_name,
                                  l.quantity,
                                  l.issue_date,
                                  l.installation_date,
                                  l.expiry_date,
                                  l.remarks
                           FROM licenses l
                                    JOIN customers c ON l.customer_id = c.customer_id
                                    JOIN products p ON l.product_id = p.product_id
                           ORDER BY l.issue_date DESC
                           """)
            return cursor.fetchall()
        except Error as e:
            st.error(f"Database error: {e}")
        finally:
            if conn.is_connected():
                conn.close()
    return []


def show_license_entry():
    st.set_page_config(page_title="License Entry", layout="wide")

    if 'logged_in' not in st.session_state or not st.session_state.logged_in:
        st.warning("Please log in to access this page.")
        return

    st.title("License Entry Form")
    st.markdown("---")

    # Get data for dropdowns
    customers = get_customers_for_dropdown()
    products = get_products_for_dropdown()

    with st.form("license_form"):
        st.subheader("New License Entry")

        col1, col2 = st.columns(2)
        with col1:
            # Customer dropdown
            customer_options = {f"{c['customer_id']} - {c['customer_name']}": c['customer_id'] for c in customers}
            selected_customer = st.selectbox("Customer*", options=["Select customer"] + list(customer_options.keys()))

            # Product dropdown
            product_options = {f"{p['product_id']} - {p['product_name']}": p for p in products}
            selected_product = st.selectbox("Product*", options=["Select product"] + list(product_options.keys()))

            quantity = st.number_input("Quantity*", min_value=1, value=1)

        with col2:
            issue_date = st.date_input("Issue Date*", datetime.now())
            installation_date = st.date_input("Installation Date")

            # Set default validity based on selected product
            default_validity = 12
            if selected_product != "Select product":
                product_data = product_options[selected_product]
                default_validity = product_data['default_validity_months']

            validity_period = st.number_input("Validity Period (months)*",
                                              min_value=1, value=default_validity)

        remarks = st.text_area("Remarks", max_chars=500)

        submitted = st.form_submit_button("Submit")
        if submitted:
            if selected_customer == "Select customer" or selected_product == "Select product":
                st.error("Please select a customer and product")
            else:
                customer_id = customer_options[selected_customer]
                product_id = product_options[selected_product]['product_id']
                license_data = (
                    customer_id,
                    product_id,
                    quantity,
                    issue_date,
                    installation_date if installation_date else None,
                    validity_period,
                    remarks
                )
                if save_license(license_data):
                    st.success("License record saved successfully!")
                    st.rerun()
                else:
                    st.error("Error saving license record")

    # Display existing licenses in a table
    st.subheader("Existing Licenses")
    licenses = get_all_licenses()

    if licenses:
        # Create a DataFrame for display
        df = pd.DataFrame(licenses)
        st.dataframe(df, hide_index=True, use_container_width=True)
    else:
        st.info("No licenses found in the database")


if __name__ == "__main__":
    show_license_entry()