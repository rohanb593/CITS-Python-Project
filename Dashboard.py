# Dashboard.py
import mysql
import streamlit as st
import pandas as pd
from datetime import datetime
from mysql.connector import Error
import smtplib
import plotly.express as px
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

def get_customer_count():
    """Get total number of customers"""
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT COALESCE(COUNT(*), 0) FROM customers")
            count = cursor.fetchone()[0]
            return int(count) if count is not None else 0
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
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT 
                    COALESCE(SUM(CASE WHEN expiry_date >= CURDATE() THEN 1 ELSE 0 END), 0) as active,
                    COALESCE(SUM(CASE WHEN expiry_date < CURDATE() THEN 1 ELSE 0 END), 0) as expired
                FROM licenses
            """)
            result = cursor.fetchone()
            return {
                'active': int(result['active']) if result['active'] is not None else 0,
                'expired': int(result['expired']) if result['expired'] is not None else 0
            }
        except Error as e:
            st.error(f"Database error: {e}")
            return {'active': 0, 'expired': 0}
        finally:
            if conn.is_connected():
                conn.close()
    return {'active': 0, 'expired': 0}


# Add this to Dashboard.py after the existing metrics section

def get_expiring_licenses():
    """Get licenses that are expired or expiring soon"""
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)

            # Get already expired licenses
            cursor.execute("""
                           SELECT l.license_id,
                                  c.customer_name,
                                  p.product_name,
                                  l.quantity,
                                  l.expiry_date,
                                  DATEDIFF(l.expiry_date, CURDATE()) as days_remaining
                           FROM licenses l
                                    JOIN customers c ON l.customer_id = c.customer_id
                                    JOIN products p ON l.product_id = p.product_id
                           WHERE l.expiry_date < CURDATE()
                           ORDER BY l.expiry_date ASC
                           """)
            expired = cursor.fetchall()

            # Get licenses expiring within 21 days (3 weeks)
            cursor.execute("""
                           SELECT l.license_id,
                                  c.customer_name,
                                  p.product_name,
                                  l.quantity,
                                  l.expiry_date,
                                  DATEDIFF(l.expiry_date, CURDATE()) as days_remaining
                           FROM licenses l
                                    JOIN customers c ON l.customer_id = c.customer_id
                                    JOIN products p ON l.product_id = p.product_id
                           WHERE l.expiry_date >= CURDATE()
                             AND l.expiry_date <= DATE_ADD(CURDATE(), INTERVAL 21 DAY)
                           ORDER BY l.expiry_date ASC
                           """)
            expiring_soon = cursor.fetchall()

            return {
                'expired': expired,
                'expiring_soon': expiring_soon
            }

        except Error as e:
            st.error(f"Database error: {e}")
            return {'expired': [], 'expiring_soon': []}
        finally:
            if conn.is_connected():
                conn.close()
    return {'expired': [], 'expiring_soon': []}


def show_license_renewal_section():
    """Display tables for expired and soon-to-expire licenses"""
    st.subheader("License Renewal Status")

    licenses = get_expiring_licenses()

    # Add this check:
    if not licenses['expired'] and not licenses['expiring_soon']:
        st.info("No data uploaded - no license renewal information available")
        return

    # Rest of the existing function...
    # Expired licenses table
    with st.expander("⚠️ Expired Licenses (Needs Immediate Attention)", expanded=True):
        if licenses['expired']:
            expired_df = pd.DataFrame(licenses['expired'])
            # Remove license_id column
            expired_df = expired_df.drop(columns=['license_id'])
            expired_df['days_remaining'] = expired_df['days_remaining'].apply(lambda x: f"Expired {abs(x)} days ago")

            st.dataframe(
                expired_df,
                column_config={
                    "customer_name": "Customer",
                    "product_name": "Product",
                    "quantity": st.column_config.NumberColumn("Quantity", format="%d"),
                    "expiry_date": st.column_config.DateColumn("Expiry Date"),
                    "days_remaining": "Status"
                },
                use_container_width=True,
                hide_index=True
            )
        else:
            st.success("No expired licenses found!")

    # Expiring soon table
    with st.expander("🔔 Licenses Expiring Soon (Within 3 Weeks)", expanded=True):
        if licenses['expiring_soon']:
            expiring_df = pd.DataFrame(licenses['expiring_soon'])
            # Remove license_id column
            expiring_df = expiring_df.drop(columns=['license_id'])
            expiring_df['days_remaining'] = expiring_df['days_remaining'].apply(
                lambda x: f"Expires in {x} days" if x > 0 else "Expires today"
            )

            st.dataframe(
                expiring_df,
                column_config={
                    "customer_name": "Customer",
                    "product_name": "Product",
                    "quantity": st.column_config.NumberColumn("Quantity", format="%d"),
                    "expiry_date": st.column_config.DateColumn("Expiry Date"),
                    "days_remaining": "Status"
                },
                use_container_width=True,
                hide_index=True
            )
        else:
            st.success("No licenses expiring in the next 3 weeks!")


def show_pie_charts():
    """Display two pie charts showing actual counts"""
    # Get license stats
    license_stats = get_license_stats()

    # Get product count
    products = get_all_products()
    product_count = len(products) if products else 0

    # Get customer count
    customer_count = get_customer_count()

    # Only show the chart if we have some data
    if customer_count > 0 or product_count > 0 or license_stats['active'] > 0 or license_stats['expired'] > 0:
        # System Totals Pie Chart (Counts only)
        totals = {
            'Products': product_count,
            'Customers': customer_count,
            'Active Licenses': license_stats['active'],
            'Expired Licenses': license_stats['expired']
        }

        fig1 = px.pie(
            names=list(totals.keys()),
            values=list(totals.values()),
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        fig1.update_traces(
            texttemplate='%{label}<br>%{value}',
            textposition='inside',
            hoverinfo='label+value',
            hole=0.3,
            textfont_size=16
        )
        fig1.update_layout(showlegend=False)
        st.plotly_chart(fig1, use_container_width=True)
    else:
        st.info("No data available for visualization")




# Add these helper functions if not already present
def get_all_products():
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT product_id FROM products")
            return cursor.fetchall()
        except Error as e:
            st.error(f"Database error: {e}")
            return []
        finally:
            if conn.is_connected():
                conn.close()
    return []


def get_all_licenses():
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT license_id FROM licenses")
            return cursor.fetchall()
        except Error as e:
            st.error(f"Database error: {e}")
            return []
        finally:
            if conn.is_connected():
                conn.close()
    return []

def show_dashboard():
    st.set_page_config(page_title="Dashboard", layout="wide")

    if 'logged_in' not in st.session_state or not st.session_state.logged_in:
        st.warning("Please log in to access this page.")
        return

    st.title("Corporate IT Solutions Dashboard")

    # Get data
    total_customers = get_customer_count()  # This now returns an int
    license_stats = get_license_stats()  # This now returns dict with int values

    with st.expander("📊 License Metrics", expanded=True):
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                label="Total Customers",
                value=str(total_customers),  # Convert to string to be safe
                delta="View all customers",
                help="Total number of customers"
            )

        with col2:
            st.metric(
                label="Active Licenses",
                value=str(license_stats['active']),
                delta="See details",
                help="Licenses currently in use"
            )

        with col3:
            st.metric(
                label="Expired Licenses",
                value=str(license_stats['expired']),
                delta="Needs attention",
                delta_color="inverse",
                help="Licenses requiring renewal"
            )

    # Rest of your dashboard code...

    # ===== LICENSE STATUS VISUALIZATION =====
    col1, col2 = st.columns([6,2])

    with col1:
        licenses = get_expiring_licenses()
        if not licenses['expired'] and not licenses['expiring_soon']:
            st.info("No data uploaded - no license renewal information available")
        else:
            show_license_renewal_section()

    with col2:
        show_pie_charts()






if __name__ == "__main__":
    show_dashboard()


