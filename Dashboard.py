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
    st.markdown("---")
    st.subheader("License Renewal Status")

    licenses = get_expiring_licenses()

    # Expired licenses table
    with st.expander("⚠️ Expired Licenses (Needs Immediate Attention)", expanded=True):
        if licenses['expired']:
            expired_df = pd.DataFrame(licenses['expired'])
            expired_df['days_remaining'] = expired_df['days_remaining'].apply(lambda x: f"Expired {abs(x)} days ago")

            st.dataframe(
                expired_df,
                column_config={
                    "license_id": "License ID",
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
            expiring_df['days_remaining'] = expiring_df['days_remaining'].apply(
                lambda x: f"Expires in {x} days" if x > 0 else "Expires today"
            )

            st.dataframe(
                expiring_df,
                column_config={
                    "license_id": "License ID",
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
    st.markdown("---")


    col1, col2 = st.columns(2)

    with col1:
        # System Totals Pie Chart (Counts only)

        totals = {
            'Products': len(get_all_products()),
            'Customers': get_customer_count(),
            'Licenses': len(get_all_licenses())
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

    with col2:
        # License Status Pie Chart (Counts only)

        stats = get_license_stats()
        status_data = {
            'Active': stats['active'],
            'Expired': stats['expired']
        }

        fig2 = px.pie(
            names=list(status_data.keys()),
            values=list(status_data.values()),
            color=list(status_data.keys()),
            color_discrete_map={
                'Active': '#2ecc71',  # Green
                'Expired': '#e74c3c'  # Red
            }
        )
        fig2.update_traces(
            texttemplate='%{label}<br>%{value}',
            textposition='inside',
            hoverinfo='label+value',
            hole=0.3,
            textfont_size=16
        )
        fig2.update_layout(showlegend=False)
        st.plotly_chart(fig2, use_container_width=True)


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
    st.markdown("---")



    # Get data

    total_customers = int(get_customer_count())

    license_stats_raw = get_license_stats()
    license_stats = {
        'active': int(license_stats_raw['active']),
        'expired': int(license_stats_raw['expired']),
    }

    # Create metrics columns
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

    show_pie_charts()
    show_license_renewal_section()






if __name__ == "__main__":
    show_dashboard()


