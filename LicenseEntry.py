import streamlit as st
import mysql.connector
from mysql.connector import Error
from datetime import datetime
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


def get_licenses_by_customer(customer_id):
    """Get all licenses for a specific customer"""
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                           SELECT l.license_id,
                                  l.product_id,
                                  p.product_name,
                                  l.quantity,
                                  l.issue_date,
                                  l.installation_date,
                                  l.expiry_date,
                                  l.remarks,
                                  l.validity_period_months
                           FROM licenses l
                                    JOIN products p ON l.product_id = p.product_id
                           WHERE l.customer_id = %s
                           ORDER BY l.issue_date DESC
                           """, (customer_id,))
            return cursor.fetchall()
        except Error as e:
            st.error(f"Database error: {e}")
        finally:
            if conn.is_connected():
                conn.close()
    return []


def save_license(license_data, license_id=None):
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()

            # Check for existing license for this customer-product combination
            customer_id = license_data[0]
            product_id = license_data[1]

            if not license_id:  # Only check for new licenses, not updates
                cursor.execute("""
                               SELECT license_id
                               FROM licenses
                               WHERE customer_id = %s
                                 AND product_id = %s
                               """, (customer_id, product_id))
                existing_license = cursor.fetchone()

                if existing_license:
                    return False, "This customer already has a license for this product. Please use the upgrade section instead."

            if license_id:  # Update existing
                cursor.execute("""
                               UPDATE licenses
                               SET customer_id            = %s,
                                   product_id             = %s,
                                   quantity               = %s,
                                   issue_date             = %s,
                                   installation_date      = %s,
                                   validity_period_months = %s,
                                   remarks                = %s
                               WHERE license_id = %s
                               """, (*license_data, license_id))


            else:  # Insert new
                cursor.execute("""
                               INSERT INTO licenses
                               (customer_id, product_id, quantity, issue_date, installation_date,
                                validity_period_months, remarks)
                               VALUES (%s, %s, %s, %s, %s, %s, %s)
                               """, license_data)
            conn.commit()
            return True, "License record saved successfully!"
        except Error as e:
            return False, f"Database error: {e}"
        finally:
            if conn.is_connected():
                conn.close()
    return False, "Could not connect to database"


def delete_license(license_id):
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM licenses WHERE license_id = %s", (license_id,))
            conn.commit()
            return cursor.rowcount > 0
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
                                  l.remarks,
                                  l.customer_id,
                                  l.product_id,
                                  l.validity_period_months
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


def get_customer_products(customer_id):
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                           SELECT DISTINCT p.product_id, p.product_name, p.default_validity_months
                           FROM licenses l
                                    JOIN products p ON l.product_id = p.product_id
                           WHERE l.customer_id = %s
                           ORDER BY p.product_name
                           """, (customer_id,))
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


def calculate_expiry_date(issue_date, validity_months):
    """Calculate expiry date based on issue date and validity period"""
    from dateutil.relativedelta import relativedelta
    return issue_date + relativedelta(months=+validity_months)

def show_license_entry():
    st.set_page_config(page_title="License Entry", layout="wide")

    if 'logged_in' not in st.session_state or not st.session_state.logged_in:
        st.warning("Please log in to access this page.")
        return

    st.title("License Master")


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
    if 'selected_license' not in st.session_state:
        st.session_state.selected_license = None
    if 'license_data' not in st.session_state:
        st.session_state.license_data = {}
    if 'selected_customer_id' not in st.session_state:
        st.session_state.selected_customer_id = None

    # Get data for dropdowns
    customers = get_customers_for_dropdown()
    products = get_products_for_dropdown()

    # Toggle switch for edit mode
    edit_mode = st.toggle("Edit Mode", value=st.session_state.edit_mode, key="edit_toggle")

    # Add new license form

    if not st.session_state.edit_mode:
        with st.expander("Add New License"):
            with st.form("license_form"):
                col1, col2 = st.columns(2)
                with col1:
                    # Customer dropdown
                    customer_options = {f"{c['customer_id']} - {c['customer_name']}": c['customer_id'] for c in
                                        customers}
                    selected_customer = st.selectbox("Customer*",
                                                     options=["Select customer"] + list(customer_options.keys()))

                    # Product dropdown
                    product_options = {f"{p['product_id']} - {p['product_name']}": p for p in products}
                    selected_product = st.selectbox("Product*",
                                                    options=["Select product"] + list(product_options.keys()))

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

                    # Calculate and display expiry date
                    if selected_product != "Select product" and issue_date:
                        expiry_date = calculate_expiry_date(issue_date, validity_period)
                        st.text(f"Renewal Date: {expiry_date.strftime('%Y-%m-%d')}")

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
                        success, message = save_license(license_data)
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)

        with st.expander("Upgrade License"):
            customer_options = {f"{c['customer_id']} - {c['customer_name']}": c['customer_id'] for c in customers}
            selected_customer = st.selectbox(
                "Select Customer",
                options=["Select a customer"] + list(customer_options.keys()),
                key="upgrade_customer_select"
            )

            if selected_customer != "Select a customer":
                customer_id = customer_options[selected_customer]
                st.session_state.selected_customer_id = customer_id

                # Get licenses for selected customer
                customer_licenses = get_licenses_by_customer(customer_id)

                if customer_licenses:
                    # License selection dropdown
                    license_options = {
                        f"{l['license_id']} - {l['product_name']} (Issued: {l['issue_date']})": l
                        for l in customer_licenses
                    }
                    selected_license = st.selectbox(
                        "Select License to Upgrade",
                        options=["Select a license"] + list(license_options.keys()),
                        key="upgrade_license_select"
                    )

                    if selected_license != "Select a license":
                        selected_license_data = license_options[selected_license]
                        if st.session_state.selected_license != selected_license_data:
                            st.session_state.selected_license = selected_license_data
                            st.session_state.validity_period = selected_license_data['validity_period_months']
                            st.rerun()

                        # Initialize or update expiry date
                        issue_date = st.session_state.selected_license['issue_date']
                        current_validity = st.session_state.get('validity_period',
                                                                st.session_state.selected_license[
                                                                    'validity_period_months'])
                        current_expiry = calculate_expiry_date(issue_date, current_validity)

                        # Display the form
                        with st.form("upgrade_license_form"):
                            col1, col2 = st.columns(2)
                            with col1:
                                st.text_input(
                                    "License ID",
                                    value=st.session_state.selected_license['license_id'],
                                    disabled=True
                                )
                                st.text_input(
                                    "Customer",
                                    value=selected_customer.split(" - ")[1],
                                    disabled=True
                                )
                                st.text_input(
                                    "Product",
                                    value=selected_license.split(" - ")[1],
                                    disabled=True
                                )
                                quantity = st.number_input(
                                    "Quantity*",
                                    min_value=1,
                                    value=st.session_state.selected_license['quantity']
                                )

                            with col2:
                                st.date_input(
                                    "Issue Date",
                                    value=issue_date,
                                    disabled=True
                                )

                                # Validity period input - will update session state on change
                                validity_period = st.number_input(
                                    "Validity Period (months)*",
                                    min_value=1,
                                    value=st.session_state.get('validity_period',
                                                               st.session_state.selected_license[
                                                                   'validity_period_months']),
                                    key="validity_input"
                                )

                                # Display current expiry date
                                st.text(f"Renewal Date: {current_expiry.strftime('%Y-%m-%d')}")

                                remarks = st.text_area(
                                    "Remarks",
                                    value=f"Upgraded on {datetime.now().date()} - {st.session_state.selected_license['remarks']}",
                                    max_chars=500
                                )

                            submit_button = st.form_submit_button("Submit Upgrade")

                        # Update validity period in session state when changed
                        if validity_period != st.session_state.get('validity_period'):
                            st.session_state.validity_period = validity_period
                            st.rerun()

                        if submit_button:
                            # Use product ID from selected license
                            product_id = st.session_state.selected_license['product_id']
                            installation_date = st.session_state.selected_license['installation_date']

                            license_data = (
                                st.session_state.selected_customer_id,
                                product_id,
                                quantity,
                                issue_date,
                                installation_date,
                                validity_period,
                                remarks
                            )

                            success, message = save_license(
                                license_data,
                                st.session_state.selected_license['license_id']
                            )

                            if success:
                                st.success("License updated successfully!")
                                st.session_state.selected_license = None
                                st.session_state.validity_period = None
                                st.rerun()
                            else:
                                st.error(message)
                else:
                    st.info("This customer has no licenses to upgrade")

    if edit_mode != st.session_state.edit_mode:
        st.session_state.edit_mode = edit_mode
        if not edit_mode and st.session_state.selected_license:
            license_data = (
                st.session_state.license_data['customer_id'],
                st.session_state.license_data['product_id'],
                st.session_state.license_data['quantity'],
                st.session_state.license_data['issue_date'],
                st.session_state.license_data['installation_date'],
                st.session_state.license_data['validity_period_months'],
                st.session_state.license_data['remarks'],
                st.session_state.selected_license['license_id']
            )
            if save_license(license_data, st.session_state.selected_license['license_id']):
                st.success("License updated successfully!")
            else:
                st.error("Error updating license")
        st.rerun()

    # Get all licenses
    licenses = get_all_licenses()

    if licenses:
        if st.session_state.edit_mode:
            # Edit mode - show customer selection first
            st.subheader("Edit License")

            # Customer selection dropdown
            customer_options = {f"{c['customer_id']} - {c['customer_name']}": c['customer_id'] for c in customers}
            selected_customer = st.selectbox(
                "Select Customer",
                options=["Select a customer"] + list(customer_options.keys()),
                key="edit_customer_select"
            )

            if selected_customer != "Select a customer":
                customer_id = customer_options[selected_customer]
                st.session_state.selected_customer_id = customer_id

                # Get licenses for selected customer
                customer_licenses = get_licenses_by_customer(customer_id)

                if customer_licenses:
                    # License selection dropdown
                    license_options = {
                        f"{l['license_id']} - {l['product_name']} (Issued: {l['issue_date']})": l
                        for l in customer_licenses
                    }
                    selected_license = st.selectbox(
                        "Select License to Edit",
                        options=["Select a license"] + list(license_options.keys()),
                        key="edit_license_select"
                    )

                    if selected_license != "Select a license":
                        selected_license_data = license_options[selected_license]
                        if st.session_state.selected_license != selected_license_data:
                            st.session_state.selected_license = selected_license_data
                            st.session_state.license_data = {
                                'license_id': selected_license_data['license_id'],
                                'customer_id': customer_id,
                                'product_id': selected_license_data['product_id'],
                                'product_name': selected_license_data['product_name'],
                                'quantity': selected_license_data['quantity'],
                                'issue_date': selected_license_data['issue_date'],
                                'installation_date': selected_license_data['installation_date'],
                                'validity_period_months': selected_license_data['validity_period_months'],
                                'remarks': selected_license_data['remarks']
                            }
                            st.rerun()

                        # Edit form
                        if st.session_state.selected_license:
                            with st.form("edit_license_form"):
                                col1, col2 = st.columns(2)
                                with col1:
                                    # Display license ID as read-only
                                    st.text_input(
                                        "License ID",
                                        value=st.session_state.selected_license['license_id'],
                                        disabled=True
                                    )

                                    # Display customer name as read-only
                                    st.text_input(
                                        "Customer",
                                        value=selected_customer.split(" - ")[1],
                                        disabled=True
                                    )

                                    # Product dropdown
                                    product_options = {f"{p['product_id']} - {p['product_name']}": p['product_id'] for p
                                                       in products}
                                    selected_product = st.selectbox(
                                        "Product*",
                                        options=["Select product"] + list(product_options.keys()),
                                        index=list(product_options.keys()).index(
                                            f"{st.session_state.license_data['product_id']} - {st.session_state.license_data['product_name']}"
                                        ) + 1 if st.session_state.license_data.get('product_id') else 0
                                    )

                                    quantity = st.number_input(
                                        "Quantity*",
                                        min_value=1,
                                        value=st.session_state.license_data['quantity']
                                    )

                                with col2:
                                    issue_date = st.date_input(
                                        "Issue Date*",
                                        value=st.session_state.license_data['issue_date']
                                    )
                                    installation_date = st.date_input(
                                        "Installation Date",
                                        value=st.session_state.license_data['installation_date'] if
                                        st.session_state.license_data['installation_date'] else None
                                    )

                                    validity_period = st.number_input(
                                        "Validity Period (months)*",
                                        min_value=1,
                                        value=st.session_state.license_data['validity_period_months']
                                    )

                                remarks = st.text_area(
                                    "Remarks",
                                    value=st.session_state.license_data['remarks'],
                                    max_chars=500
                                )

                                # Form submission buttons
                                col1, col2, col3 = st.columns([1, 1, 2])
                                with col1:
                                    if st.form_submit_button("Save Changes"):
                                        customer_id = st.session_state.selected_customer_id
                                        product_id = product_options[selected_product]
                                        license_data = (
                                            customer_id,
                                            product_id,
                                            quantity,
                                            issue_date,
                                            installation_date if installation_date else None,
                                            validity_period,
                                            remarks
                                        )
                                        if save_license(license_data, st.session_state.selected_license['license_id']):
                                            st.success("License updated successfully!")
                                            st.session_state.edit_mode = False
                                            st.rerun()
                                        else:
                                            st.error("Error updating license")

                                with col2:
                                    if st.form_submit_button("Delete License", type="primary"):
                                        if st.session_state.get('confirm_delete', False):
                                            if delete_license(st.session_state.selected_license['license_id']):
                                                st.success("License deleted successfully!")
                                                st.session_state.edit_mode = False
                                                st.session_state.selected_license = None
                                                st.rerun()
                                            else:
                                                st.error("Error deleting license")
                                        else:
                                            st.session_state.confirm_delete = True
                                            st.warning("Are you sure? Click Delete License again to confirm.")
                                            st.rerun()
                else:
                    st.info("No licenses found for this customer")
        else:
            # View mode - show interactive table
            st.subheader("Existing Licenses")

            # Convert to DataFrame for display (excluding internal IDs)
            display_licenses = [{
                'License ID': l['license_id'],
                'Customer': l['customer_name'],
                'Product': l['product_name'],
                'Quantity': l['quantity'],
                'Issue Date': l['issue_date'],
                'Installation Date': l['installation_date'],
                'Expiry Date': l['expiry_date'],
                'Remarks': l['remarks']
            } for l in licenses]

            df = pd.DataFrame(display_licenses)

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
    else:
        st.info("No licenses found in the database")


if __name__ == "__main__":
    show_license_entry()