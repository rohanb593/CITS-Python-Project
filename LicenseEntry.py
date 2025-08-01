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
                                  l.validity_period_months,
                                  l.kwacha_amount,
                                  l.USD_amount
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

            # Check for existing license
            customer_id = license_data[0]
            product_id = license_data[1]

            if not license_id:
                cursor.execute("""
                               SELECT license_id
                               FROM licenses
                               WHERE customer_id = %s
                                 AND product_id = %s
                               """, (customer_id, product_id))
                existing_license = cursor.fetchone()
                if existing_license:
                    return False, "This customer already has a license for this product."

            if license_id:  # Update existing
                cursor.execute("""
                               UPDATE licenses
                               SET customer_id = %s,
                                   product_id = %s,
                                   quantity = %s,
                                   issue_date = %s,
                                   installation_date = %s,
                                   validity_period_months = %s,
                                   remarks = %s,
                                   kwacha_amount = %s,
                                   USD_amount = %s
                               WHERE license_id = %s
                               """, (*license_data, license_id))
            else:  # Insert new
                cursor.execute("""
                               INSERT INTO licenses
                               (customer_id, product_id, quantity, issue_date, installation_date,
                                validity_period_months, remarks, kwacha_amount, USD_amount)
                               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
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
            # First delete associated renewals
            cursor.execute("DELETE FROM renewals WHERE license_id = %s", (license_id,))
            # Then delete the license
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
                                  l.validity_period_months,
                                  l.kwacha_amount,
                                  l.USD_amount
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


def insert_renewal(renewal_data):
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            query = """
                INSERT INTO renewals 
                (license_id, customer_id, product_id, total_quantity, renewal_due_date, 
                 renewal_amount_kwatcha, renewal_amount_USD, status, invoice_no, 
                 client_confirmation_status, remarks, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
            """
            cursor.execute(query, renewal_data)
            conn.commit()
            return True, "Renewal record created successfully!"
        except Error as e:
            return False, f"Database error: {e}"
        finally:
            if conn.is_connected():
                conn.close()
    return False, "Could not connect to database"

def get_renewals_by_license(license_id):
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT 
                    renewal_id,
                    license_id,
                    total_quantity,
                    renewal_due_date,
                    renewal_amount_kwatcha,
                    renewal_amount_USD,
                    status,
                    invoice_no,
                    client_confirmation_status,
                    remarks,
                    created_at
                FROM renewals 
                WHERE license_id = %s
                ORDER BY renewal_due_date DESC
            """, (license_id,))
            return cursor.fetchall()
        except Error as e:
            st.error(f"Database error: {e}")
            return []
        finally:
            if conn.is_connected():
                conn.close()
    return []


def show_license_entry():
    conn = get_db_connection()
    cursor = conn.cursor()
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
                    customer_options = {c['customer_name']: c['customer_id'] for c in customers}
                    selected_customer = st.selectbox("Customer*",
                                                     options=["Select customer"] + list(customer_options.keys()))

                    # Product dropdown
                    product_options = {p['product_name']: p for p in products}
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
                        st.badge(f"Renewal Date: {expiry_date.strftime('%Y-%m-%d')}", icon=":material/check:", color="green")

                amount_col1, amount_col2 = st.columns(2)
                with amount_col1:
                    currency = st.radio("Currency", ["ZMW", "USD"], horizontal=True)
                with amount_col2:
                    amount = st.number_input("Amount (USD)", min_value=0.0, step=0.01, format="%.2f")


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
                            remarks,
                            amount if currency == "ZMW" else None,  # kwacha_amount
                            amount if currency == "USD" else None  # USD_amount
                        )
                        success, message = save_license(license_data)
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)

        with st.expander("Upgrade License"):
            customer_options = {c['customer_name']: c['customer_id'] for c in customers}
            selected_customer = st.selectbox(
                "Select Customer",
                options=["Select a customer"] + list(customer_options.keys()),
                key="upgrade_customer_select"
            )

            if selected_customer != "Select a customer":
                customer_id = customer_options[selected_customer]
                st.session_state.selected_customer_id = customer_id

                customer_licenses = get_licenses_by_customer(customer_id)

                if customer_licenses:
                    license_options = {
                        f"{l['product_name']} (Issued: {l['issue_date'].strftime('%Y-%m-%d')})": l
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
                            st.session_state.original_quantity = selected_license_data['quantity']
                            st.rerun()

                        issue_date = st.session_state.selected_license['issue_date']
                        current_validity = st.session_state.selected_license['validity_period_months']
                        current_expiry = calculate_expiry_date(issue_date, current_validity)

                        # Determine currency type
                        has_kwacha = st.session_state.selected_license.get('kwacha_amount') is not None
                        currency = "ZMW" if has_kwacha else "USD"
                        original_amount = float(st.session_state.selected_license.get(
                            'kwacha_amount' if currency == "ZMW" else 'USD_amount', 0))

                        with st.form("upgrade_license_form"):
                            col1, col2 = st.columns(2)
                            with col1:
                                st.text_input("License ID", value=st.session_state.selected_license['license_id'],
                                              disabled=True)
                                st.text_input("Customer", value=selected_customer, disabled=True)
                                st.text_input("Product", value=selected_license_data['product_name'], disabled=True)
                                st.text_input("Original Quantity", value=st.session_state.original_quantity,
                                              disabled=True)

                                additional_quantity = st.number_input(
                                    "Additional Quantity*",
                                    min_value=0,
                                    value=0,
                                    key="additional_quantity"
                                )
                                new_quantity = st.session_state.original_quantity + additional_quantity



                            with col2:
                                st.date_input("Issue Date", value=issue_date, disabled=True)
                                st.date_input("Installation Date",
                                              value=st.session_state.selected_license['installation_date'],
                                              disabled=True)
                                st.text_input("Validity Period (months)", value=current_validity, disabled=True)
                                st.date_input("Renewal Date", value=current_expiry, disabled=True)
                                st.text_input(
                                    f"Original Amount ({currency})",
                                    value=f"{original_amount:.2f}",
                                    disabled=True
                                )

                                # Additional amount field - only shown if there's an original amount
                            if original_amount > 0:
                                additional_amount = st.number_input(
                                    f"Additional Amount ({currency})",
                                    min_value=0.0,
                                    value=0.0,
                                    format="%.2f",
                                    key="additional_amount"
                                )
                                if currency == "ZMW":
                                    new_kwacha_amount = original_amount + additional_amount
                                    new_usd_amount = None
                                else:
                                    new_usd_amount = original_amount + additional_amount
                                    new_kwacha_amount = None
                            else:
                                additional_amount = 0.0
                                new_kwacha_amount = None if currency == "USD" else 0.0
                                new_usd_amount = None if currency == "ZMW" else 0.0

                            remarks = st.text_area("Remarks", value="", max_chars=500,
                                                   placeholder="Enter upgrade reason or notes")

                            submitted = st.form_submit_button("Submit Upgrade")
                            if submitted:
                                license_data = (
                                    st.session_state.selected_customer_id,
                                    st.session_state.selected_license['product_id'],
                                    new_quantity,
                                    issue_date,
                                    st.session_state.selected_license['installation_date'],
                                    current_validity,
                                    remarks,
                                    new_kwacha_amount,
                                    new_usd_amount
                                )

                                success, message = save_license(
                                    license_data,
                                    st.session_state.selected_license['license_id']
                                )

                                if success:
                                    st.success("License upgraded successfully!")
                                    history_entry = f"\n\nUpgraded on {datetime.now().date()}:\n" \
                                                    f"- Quantity changed from {st.session_state.original_quantity} to {new_quantity}\n" \
                                                    f"- {currency} Amount changed from {original_amount:.2f} to {(original_amount + additional_amount):.2f}\n" \
                                                    f"- Remarks: {remarks}"

                                    updated_remarks = (st.session_state.selected_license[
                                                           'remarks'] or "") + history_entry

                                    cursor = conn.cursor()
                                    cursor.execute("""
                                                   UPDATE licenses
                                                   SET remarks = %s
                                                   WHERE license_id = %s
                                                   """,
                                                   (updated_remarks, st.session_state.selected_license['license_id']))
                                    conn.commit()

                                    st.session_state.selected_license = None
                                    st.session_state.original_quantity = None
                                    st.rerun()
                                else:
                                    st.error(message)

                        with st.expander("Upgrade History"):
                            if st.session_state.selected_license and st.session_state.selected_license['remarks']:
                                # Parse the remarks to show history
                                history_entries = []
                                remarks = st.session_state.selected_license['remarks']

                                # Split remarks by "Upgraded on" to get each upgrade entry
                                upgrades = remarks.split("Upgraded on")[1:]  # Skip first empty part
                                for upgrade in upgrades:
                                    date_part = upgrade.split(":")[0].strip()
                                    details = ":".join(upgrade.split(":")[1:])
                                    history_entries.append({
                                        "Date": date_part,
                                        "Details": details.strip()
                                    })

                                if history_entries:
                                    st.dataframe(pd.DataFrame(history_entries))
                                else:
                                    st.info("No upgrade history found")
                            else:
                                st.info("No upgrade history available")
                else:
                    st.info("This customer has no licenses to upgrade")

        with st.expander("Renew License"):
            customer_options = {c['customer_name']: c['customer_id'] for c in customers}
            selected_customer = st.selectbox(
                "Select Customer",
                options=["Select a customer"] + list(customer_options.keys()),
                key="renew_customer_select"
            )

            if selected_customer != "Select a customer":
                customer_id = customer_options[selected_customer]
                st.session_state.selected_customer_id = customer_id

                customer_licenses = get_licenses_by_customer(customer_id)

                if customer_licenses:
                    license_options = {
                        f"{l['product_name']} (Exp: {l['expiry_date'].strftime('%Y-%m-%d')})": l
                        for l in customer_licenses
                    }
                    selected_license = st.selectbox(
                        "Select License to Renew",
                        options=["Select a license"] + list(license_options.keys()),
                        key="renew_license_select"
                    )

                    if selected_license != "Select a license":
                        selected_license_data = license_options[selected_license]
                        current_date = datetime.now().date()
                        renewal_due_date = calculate_expiry_date(current_date,
                                                                 selected_license_data['validity_period_months'])

                        # Determine currency type
                        has_kwacha = selected_license_data.get('kwacha_amount') is not None
                        currency = "ZMW" if has_kwacha else "USD"
                        original_amount = float(
                            selected_license_data.get('kwacha_amount' if currency == "ZMW" else 'USD_amount', 0))

                        with st.form("renew_license_form"):
                            col1, col2 = st.columns(2)
                            with col1:
                                st.text_input("License ID", value=selected_license_data['license_id'], disabled=True)
                                st.text_input("Product", value=selected_license_data['product_name'], disabled=True)
                                st.text_input("Original Quantity", value=selected_license_data['quantity'],
                                              disabled=True)
                                st.text_input("Original Validity (months)",
                                              value=selected_license_data['validity_period_months'], disabled=True)
                                st.text_input(
                                    f"Original Amount ({currency})",
                                    value=f"{original_amount:.2f}",
                                    disabled=True
                                )

                            with col2:
                                st.text_input("Customer", value=selected_customer, disabled=True)
                                st.date_input("Renewal Due Date", value=renewal_due_date, disabled=True)
                                new_quantity = st.number_input(
                                    "New Quantity*",
                                    min_value=1,
                                    value=selected_license_data['quantity']
                                )
                                new_validity = st.number_input(
                                    "New Validity (months)*",
                                    min_value=1,
                                    value=selected_license_data['validity_period_months']
                                )
                                new_amount = st.number_input(
                                    f"New Amount ({currency})*",
                                    min_value=0.0,
                                    format="%.2f",
                                    value=original_amount
                                )

                            invoice_no = st.text_input("Invoice Number")
                            status = st.selectbox(
                                "Status*",
                                options=["Pending", "Paid", "Overdue", "Cancelled", "Draft"],
                                index=0
                            )
                            client_confirmation_status = st.selectbox(
                                "Client Confirmation",
                                options=["Pending", "Confirmed", "Denied"],
                                index=0
                            )
                            remarks = st.text_area("Remarks", max_chars=500, placeholder="Enter renewal details")

                            submitted = st.form_submit_button("Submit Renewal")
                            if submitted:
                                # Calculate currency amounts
                                kwacha_amount = new_amount if currency == "ZMW" else None
                                usd_amount = new_amount if currency == "USD" else None

                                # Create renewal history
                                renewal_history = f"""
                                Renewed on {current_date}:
                                - Quantity: {selected_license_data['quantity']} → {new_quantity}
                                - Validity: {selected_license_data['validity_period_months']} → {new_validity} months
                                - Amount: {original_amount:.2f} → {new_amount:.2f} {currency}
                                - Remarks: {remarks}
                                """

                                # Update license record
                                license_update_data = (
                                    customer_id,
                                    selected_license_data['product_id'],
                                    new_quantity,
                                    current_date,
                                    selected_license_data['installation_date'],
                                    new_validity,
                                    (selected_license_data['remarks'] or "") + renewal_history,
                                    kwacha_amount,
                                    usd_amount,
                                    selected_license_data['license_id']
                                )

                                # Save license update
                                update_success, update_message = save_license(
                                    license_data=license_update_data[:-1],
                                    license_id=license_update_data[-1]
                                )

                                if update_success:
                                    # Create renewal record
                                    renewal_data = (
                                        selected_license_data['license_id'],
                                        customer_id,
                                        selected_license_data['product_id'],
                                        new_quantity,
                                        renewal_due_date,
                                        kwacha_amount,
                                        usd_amount,
                                        status,
                                        invoice_no,
                                        client_confirmation_status,
                                        remarks
                                    )

                                    renew_success, renew_message = insert_renewal(renewal_data)

                                    if renew_success:
                                        st.success("License renewed successfully!")
                                        st.rerun()
                                    else:
                                        st.error(f"Renewal record failed: {renew_message}")
                                else:
                                    st.error(f"License update failed: {update_message}")

                        # Show previous renewals for this license
                        st.subheader("Renewal History")
                        renewals = get_renewals_by_license(selected_license_data['license_id'])
                        if renewals:
                            renewals_df = pd.DataFrame(renewals)
                            renewals_df['renewal_due_date'] = pd.to_datetime(renewals_df['renewal_due_date']).dt.date
                            renewals_df['created_at'] = pd.to_datetime(renewals_df['created_at']).dt.strftime(
                                '%Y-%m-%d %H:%M')

                            if not renewals_df.empty:
                                renewals_df['renewal_amount_kwatcha'] = renewals_df['renewal_amount_kwatcha'].apply(
                                    lambda x: f"ZMW {x:,.2f}" if pd.notnull(x) else "N/A"
                                )
                                renewals_df['renewal_amount_USD'] = renewals_df['renewal_amount_USD'].apply(
                                    lambda x: f"USD {x:,.2f}" if pd.notnull(x) else "N/A"
                                )

                                st.dataframe(renewals_df[[
                                    'renewal_id',
                                    'total_quantity',
                                    'renewal_due_date',
                                    'renewal_amount_kwatcha',
                                    'renewal_amount_USD',
                                    'status',
                                    'invoice_no',
                                    'client_confirmation_status',
                                    'remarks',
                                    'created_at'
                                ]])
                        else:
                            st.info("No previous renewals found for this license")
                else:
                    st.info("This customer has no licenses to renew")

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
            st.subheader("Edit License")
            customer_options = {c['customer_name']: c['customer_id'] for c in customers}
            selected_customer = st.selectbox(
                "Select Customer",
                options=["Select a customer"] + list(customer_options.keys()),
                key="edit_customer_select"
            )

            if selected_customer != "Select a customer":
                customer_id = customer_options[selected_customer]
                st.session_state.selected_customer_id = customer_id

                customer_licenses = get_licenses_by_customer(customer_id)

                if customer_licenses:
                    license_options = {
                        f"{l['product_name']} (Issued: {l['issue_date'].strftime('%Y-%m-%d')})": l
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
                                'remarks': selected_license_data['remarks'],
                                'kwacha_amount': selected_license_data.get('kwacha_amount'),
                                'USD_amount': selected_license_data.get('USD_amount')
                            }
                            st.rerun()

                        if st.session_state.selected_license:
                            with st.form("edit_license_form"):
                                col1, col2 = st.columns(2)
                                with col1:
                                    st.text_input(
                                        "License ID",
                                        value=st.session_state.selected_license['license_id'],
                                        disabled=True
                                    )
                                    st.text_input(
                                        "Customer",
                                        value=selected_customer,
                                        disabled=True
                                    )

                                    product_options = {p['product_name']: p['product_id'] for p in products}
                                    # Get current product index
                                    current_product = st.session_state.license_data.get('product_name',
                                                                                        "Select product")
                                    product_list = list(product_options.keys())
                                    try:
                                        current_index = product_list.index(
                                            current_product) + 1  # +1 to account for "Select product"
                                    except ValueError:
                                        current_index = 0

                                    selected_product = st.selectbox(
                                        "Product*",
                                        options=["Select product"] + product_list,
                                        index=current_index
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

                                    # Determine currency type
                                    has_kwacha = st.session_state.license_data.get('kwacha_amount') is not None
                                    currency = "ZMW" if has_kwacha else "USD"
                                    original_amount = float(st.session_state.license_data.get(
                                        'kwacha_amount' if currency == "ZMW" else 'USD_amount', 0))

                                    amount = st.number_input(
                                        f"Amount ({currency})*",
                                        min_value=0.0,
                                        format="%.2f",
                                        value=original_amount
                                    )

                                remarks = st.text_area(
                                    "Remarks",
                                    value=st.session_state.license_data['remarks'],
                                    max_chars=500
                                )

                                col1, col2, col3 = st.columns([1, 1, 2])
                                with col1:
                                    save_clicked = st.form_submit_button("Save Changes")
                                    if save_clicked:
                                        if selected_product == "Select product":
                                            st.error("Please select a valid product")
                                        else:
                                            customer_id = st.session_state.selected_customer_id
                                            product_id = product_options[selected_product]
                                            license_data = (
                                                customer_id,
                                                product_id,
                                                quantity,
                                                issue_date,
                                                installation_date if installation_date else None,
                                                validity_period,
                                                remarks,
                                                amount if currency == "ZMW" else None,
                                                amount if currency == "USD" else None
                                            )
                                            success, message = save_license(
                                                license_data,
                                                st.session_state.selected_license['license_id']
                                            )
                                            if success:
                                                st.success("License updated successfully!")
                                                st.session_state.edit_mode = False
                                                st.rerun()
                                            else:
                                                st.error(message)

                                with col2:
                                    if st.form_submit_button("Delete License", type="primary"):
                                        if delete_license(st.session_state.selected_license['license_id']):
                                            st.success("License deleted successfully!")
                                            st.session_state.edit_mode = False
                                            st.session_state.selected_license = None
                                            st.rerun()
                                        else:
                                            st.error("Error deleting license")
        else:
            # View mode - show interactive table
            st.subheader("Existing Licenses")

            display_licenses = [{
                'Customer': l['customer_name'],
                'Product': l['product_name'],
                'Quantity': l['quantity'],
                'Installation Date': l['installation_date'],
                'Issue Date': l['issue_date'],
                'Validity Period': f"{l['validity_period_months']} months",
                'Expiry Date': l['expiry_date'],
                'Amount (ZMW)': l['kwacha_amount'],
                'Amount (USD)': l['USD_amount'],
                'Remarks': l['remarks']
            } for l in licenses]

            df = pd.DataFrame(display_licenses)
            # Format the date columns to remove time
            df['Installation Date'] = pd.to_datetime(df['Installation Date']).dt.strftime('%Y-%m-%d')
            df['Issue Date'] = pd.to_datetime(df['Issue Date']).dt.strftime('%Y-%m-%d')
            df['Expiry Date'] = pd.to_datetime(df['Expiry Date']).dt.strftime('%Y-%m-%d')

            # Display DataFrame without the index
            st.dataframe(df, hide_index=True)


    else:
        st.info("No licenses found in the database")


if __name__ == "__main__":
    show_license_entry()