import pandas as pd
import streamlit as st
import mysql.connector
from mysql.connector import Error
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


def get_all_customers():
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                           SELECT customer_id, customer_name, contact_person, email, phone, location
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


def is_customer_exists(customer_name):
    """Check if a customer with the same name already exists"""
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM customers WHERE customer_name = %s", (customer_name,))
            return cursor.fetchone()[0] > 0
        except Error as e:
            st.error(f"Database error: {e}")
            return True  # Assume exists to prevent duplicates on error
        finally:
            if conn.is_connected():
                conn.close()
    return True  # Assume exists if connection fails

def save_customer(customer_data, customer_id=None):
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            if customer_id:  # Update existing
                cursor.execute("""
                               UPDATE customers
                               SET customer_name  = %s,
                                   contact_person = %s,
                                   email          = %s,
                                   phone          = %s,
                                   location       = %s
                               WHERE customer_id = %s
                               """, (*customer_data, customer_id))
            else:  # Insert new
                # First check if customer with same name exists
                if is_customer_exists(customer_data[0]):
                    st.error("A customer with this name already exists")
                    return False

                cursor.execute("""
                               INSERT INTO customers (customer_name, contact_person, email, phone, location)
                               VALUES (%s, %s, %s, %s, %s)
                               """, customer_data)
            conn.commit()
            return True
        except Error as e:
            st.error(f"Database error: {e}")
            return False
        finally:
            if conn.is_connected():
                conn.close()
    return False



def delete_customer(customer_id):
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM customers WHERE customer_id = %s", (customer_id,))
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



def show_customer_master():
    st.set_page_config(page_title="Customer Master", layout="wide")

    if 'logged_in' not in st.session_state or not st.session_state.logged_in:
        st.warning("Please log in to access this page.")
        return

    st.title("Customer Master")


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

    # Initialize session state
    if 'edit_mode' not in st.session_state:
        st.session_state.edit_mode = False
    if 'selected_customer' not in st.session_state:
        st.session_state.selected_customer = None
    if 'customer_data' not in st.session_state:
        st.session_state.customer_data = {}

    # Toggle switch for edit mode
    edit_mode = st.toggle("Edit Mode", value=st.session_state.edit_mode, key="edit_toggle")

    # Add new customer form (always visible)
    if not st.session_state.edit_mode:
        with st.expander("Add New Customer"):
            with st.form("add_customer_form"):
                col1, col2 = st.columns(2)
                with col1:
                    customer_name = st.text_input("Customer Name*", max_chars=100)
                    contact_person = st.text_input("Contact Person*", max_chars=100)
                    email = st.text_input("Email*", max_chars=100)
                with col2:
                    phone = st.text_input("Phone*", max_chars=20)
                    location = st.text_input("Location*", max_chars=100)

                if st.form_submit_button("Add Customer"):
                    if not all([customer_name, contact_person, email, phone, location]):
                        st.error("Please fill all required fields (*)")
                    else:
                        customer_data = (customer_name, contact_person, email, phone, location)
                        if save_customer(customer_data):
                            st.success("Customer added successfully!")
                            st.rerun()
                        else:
                            st.error("Error adding customer - customer name may already exist")

    if edit_mode != st.session_state.edit_mode:
        st.session_state.edit_mode = edit_mode
        if not edit_mode:  # Just turned off - save changes
            if st.session_state.selected_customer:
                customer_data = (
                    st.session_state.customer_data['customer_name'],
                    st.session_state.customer_data['contact_person'],
                    st.session_state.customer_data['email'],
                    st.session_state.customer_data['phone'],
                    st.session_state.customer_data['location'],
                    st.session_state.selected_customer['customer_id']
                )
                if save_customer(customer_data, st.session_state.selected_customer['customer_id']):
                    st.success("Customer updated successfully!")
                else:
                    st.error("Error updating customer")
        st.rerun()

    # Get all customers
    customers = get_all_customers()

    if customers:
        if st.session_state.edit_mode:
            # Edit mode - show dropdown and form
            st.subheader("Edit Customer")

            # Customer selection dropdown
            customer_options = {f"{c['customer_id']} - {c['customer_name']}": c for c in customers}
            selected_option = st.selectbox(
                "Select Customer to Edit",
                options=["Select a customer"] + list(customer_options.keys()),
                key="customer_select"
            )

            if selected_option != "Select a customer":
                selected_customer = customer_options[selected_option]
                if st.session_state.selected_customer != selected_customer:
                    st.session_state.selected_customer = selected_customer
                    st.session_state.customer_data = selected_customer.copy()
                    st.rerun()

                # Edit form
                if st.session_state.selected_customer:
                    with st.form("edit_customer_form"):
                        col1, col2 = st.columns(2)
                        with col1:
                            # Display customer ID as read-only
                            st.text_input(
                                "Customer ID",
                                value=st.session_state.selected_customer['customer_id'],
                                disabled=True
                            )

                            # Editable fields
                            new_customer_name = st.text_input(
                                "Customer Name*",
                                value=st.session_state.customer_data['customer_name'],
                                max_chars=100
                            )
                            new_contact_person = st.text_input(
                                "Contact Person*",
                                value=st.session_state.customer_data['contact_person'],
                                max_chars=100
                            )
                            new_customer_email = st.text_input(
                                "Email*",
                                value=st.session_state.customer_data['email'],
                                max_chars=100
                            )
                        with col2:
                            new_customer_phone = st.text_input(
                                "Phone*",
                                value=st.session_state.customer_data['phone'],
                                max_chars=20
                            )
                            new_customer_location = st.text_input(
                                "Location*",
                                value=st.session_state.customer_data['location'],
                                max_chars=100
                            )

                        # Form submission buttons
                        col1, col2, col3 = st.columns([1, 1, 2])
                        with col1:
                            if st.form_submit_button("Save Changes"):
                                customer_data = (
                                    new_customer_name,
                                    new_contact_person,
                                    new_customer_email,
                                    new_customer_phone,
                                    new_customer_location

                                )
                                if save_customer(customer_data, st.session_state.selected_customer['customer_id']):
                                    st.success("Customer updated successfully!")
                                    st.session_state.edit_mode = False
                                    st.rerun()
                                else:
                                    st.error("Error updating customer")

                        with col2:
                            if st.form_submit_button("Delete Customer", type="primary"):
                                if st.session_state.get('confirm_delete', False):
                                    if delete_customer(st.session_state.selected_customer['customer_id']):
                                        st.success("Customer deleted successfully!")
                                        st.session_state.edit_mode = False
                                        st.session_state.selected_customer = None
                                        st.rerun()
                                    else:
                                        st.error("Error deleting customer")
                                else:
                                    st.session_state.confirm_delete = True
                                    st.warning("Are you sure? Click Delete Customer again to confirm.")
                                    st.rerun()
        else:
            # View mode - show interactive table
            st.subheader("Customer List")



            # Convert to DataFrame and rename columns for display
            display_columns = {
                'customer_name': 'Customer',
                'contact_person': 'Contact Person',
                'email': 'Email',
                'phone': 'Phone',
                'location': 'Location'
            }

            # Create display DataFrame with renamed columns but keep original data with IDs
            df = pd.DataFrame(customers)
            display_df = df.rename(columns=display_columns)[list(display_columns.values())]

            # Configure AgGrid for display
            gb = GridOptionsBuilder.from_dataframe(display_df)
            gb.configure_default_column(editable=False)
            gb.configure_selection('single')
            grid_options = gb.build()

            # Display the grid
            grid_response = AgGrid(
                display_df,
                gridOptions=grid_options,
                update_mode=GridUpdateMode.SELECTION_CHANGED,
                fit_columns_on_grid_load=True,
                height=400
            )
    else:
        st.info("No customers found in the database")


if __name__ == "__main__":
    show_customer_master()