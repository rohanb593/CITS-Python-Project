# ProductMaster.py
import streamlit as st
import mysql.connector
from mysql.connector import Error
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode


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


def get_all_products():
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                           SELECT product_id, product_name, product_type, license_unit, default_validity_months
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


def save_product(product_data, product_id=None):
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            if product_id:  # Update existing
                cursor.execute("""
                               UPDATE products
                               SET product_name            = %s,
                                   product_type            = %s,
                                   license_unit            = %s,
                                   default_validity_months = %s
                               WHERE product_id = %s
                               """, (*product_data, product_id))
            else:  # Insert new
                cursor.execute("""
                               INSERT INTO products (product_name, product_type, license_unit, default_validity_months)
                               VALUES (%s, %s, %s, %s)
                               """, product_data)
            conn.commit()
            return True
        except Error as e:
            st.error(f"Database error: {e}")
            return False
        finally:
            if conn.is_connected():
                conn.close()
    return False


def delete_product(product_id):
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM products WHERE product_id = %s", (product_id,))
            conn.commit()
            return cursor.rowcount > 0
        except Error as e:
            st.error(f"Database error: {e}")
            return False
        finally:
            if conn.is_connected():
                conn.close()
    return False

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
def show_product_master():
    st.set_page_config(page_title="Product Master", layout="wide")

    if 'logged_in' not in st.session_state or not st.session_state.logged_in:
        st.warning("Please log in to access this page.")
        return

    st.title("Product Master")




    total_customers = int(get_customer_count())

    license_stats_raw = get_license_stats()
    license_stats = {
        'active': int(license_stats_raw['active']),
        'expired': int(license_stats_raw['expired']),
    }
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

    # Initialize session state for edit mode
    if 'edit_mode' not in st.session_state:
        st.session_state.edit_mode = False
    if 'selected_product' not in st.session_state:
        st.session_state.selected_product = None
    if 'product_data' not in st.session_state:
        st.session_state.product_data = []

    # Toggle switch for edit mode
    edit_mode = st.toggle("Edit Mode", value=st.session_state.edit_mode, key="edit_toggle")

    if not st.session_state.edit_mode:

        with st.expander("Add New Product"):
            with st.form("add_product_form"):
                product_name = st.text_input("Product Name*", max_chars=100)
                col1, col2 = st.columns(2)
                with col1:
                    product_type = st.selectbox("Product Type*", ["Software", "OS", "Hardware"])
                    license_unit = st.selectbox("License Unit*", ["User", "Device"])
                with col2:
                    validity = st.number_input("Default Validity (months)*", min_value=1, max_value=120, value=12)

                if st.form_submit_button("Add Product"):
                    if not product_name:
                        st.error("Please fill all required fields (*)")
                    else:
                        product_data = (product_name, product_type, license_unit, validity)
                        if save_product(product_data):
                            st.success("Product added successfully!")
                            st.rerun()
                        else:
                            st.error("Error adding product")

    if edit_mode != st.session_state.edit_mode:
        st.session_state.edit_mode = edit_mode
        if not edit_mode:  # Just turned off - save changes
            if st.session_state.selected_product:
                product_data = (
                    st.session_state.product_data['product_name'],
                    st.session_state.product_data['product_type'],
                    st.session_state.product_data['license_unit'],
                    st.session_state.product_data['default_validity_months'],
                    st.session_state.selected_product['product_id']
                )
                if save_product(product_data, st.session_state.selected_product['product_id']):
                    st.success("Product updated successfully!")
                else:
                    st.error("Error updating product")
        st.rerun()

    # Get all products
    products = get_all_products()

    if products:
        if st.session_state.edit_mode:
            # Edit mode - show dropdown and form
            st.subheader("Edit Product")

            # Product selection dropdown
            product_options = {f"{p['product_id']} - {p['product_name']}": p for p in products}
            selected_option = st.selectbox(
                "Select Product to Edit",
                options=["Select a product"] + list(product_options.keys()),
                key="product_select"
            )

            if selected_option != "Select a product":
                selected_product = product_options[selected_option]
                if st.session_state.selected_product != selected_product:
                    st.session_state.selected_product = selected_product
                    st.session_state.product_data = selected_product.copy()
                    st.rerun()


                # Edit form
                if st.session_state.selected_product:
                    with st.form("edit_product_form"):
                        col1, col2 = st.columns(2)
                        with col1:
                            # Display product ID as read-only
                            st.text_input(
                                "Product ID",
                                value=st.session_state.selected_product['product_id'],
                                disabled=True
                            )

                            # Editable product name
                            new_product_name = st.text_input(
                                "Product Name*",
                                value=st.session_state.product_data['product_name'],
                                max_chars=100
                            )

                            # Editable product type
                            new_product_type = st.selectbox(
                                "Product Type*",
                                ["Software", "OS", "Hardware"],
                                index=["Software", "OS", "Hardware"].index(
                                    st.session_state.product_data['product_type']
                                )
                            )
                        with col2:
                            # Editable license unit
                            new_license_unit = st.selectbox(
                                "License Unit*",
                                ["User", "Device"],
                                index=["User", "Device"].index(
                                    st.session_state.product_data['license_unit']
                                )
                            )

                            # Editable validity months
                            new_validity_months = st.number_input(
                                "Default Validity (months)*",
                                min_value=1,
                                max_value=120,
                                value=st.session_state.product_data['default_validity_months']
                            )

                        # Form submission buttons in columns
                        col1, col2, col3 = st.columns([1, 1, 2])
                        with col1:
                            if st.form_submit_button("Save Changes"):
                                # Prepare the update data - don't include ID in product_data
                                product_data = (
                                    new_product_name,
                                    new_product_type,
                                    new_license_unit,
                                    new_validity_months
                                )

                                if save_product(product_data, st.session_state.selected_product['product_id']):
                                    st.success("Product updated successfully!")
                                    st.session_state.edit_mode = False
                                    st.rerun()
                                else:
                                    st.error("Error updating product")

                        # ADD DELETE BUTTON
                        with col2:
                            if st.form_submit_button("Delete Product", type="primary"):
                                # Confirm before deleting
                                if st.session_state.get('confirm_delete', False):
                                    if delete_product(st.session_state.selected_product['product_id']):
                                        st.success("Product deleted successfully!")
                                        st.session_state.edit_mode = False
                                        st.session_state.selected_product = None
                                        st.rerun()
                                    else:
                                        st.error("Error deleting product")
                                else:
                                    st.session_state.confirm_delete = True
                                    st.warning("Are you sure? Click Delete Product again to confirm.")
                                    st.rerun()
        else:
            # View mode - show interactive table
            st.subheader("Product List")

            # Convert to DataFrame
            df = pd.DataFrame(products)

            # Configure AgGrid for display
            gb = GridOptionsBuilder.from_dataframe(df)
            gb.configure_default_column(editable=False)
            gb.configure_selection('single')
            grid_options = gb.build()

            # Display the grid
            grid_response = AgGrid(
                df,
                gridOptions=grid_options,
                update_mode=GridUpdateMode.SELECTION_CHANGED,
                fit_columns_on_grid_load=True,
                height=400
            )

            # Add new product form

    else:
        st.info("No products found in the database")


if __name__ == "__main__":
    show_product_master()