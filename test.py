import streamlit as st
import pandas as pd

# Sample data
data = {
    "Customer": ["Alice", "Bob", "Charlie", "Diana"],
    "Fruit": ["Apple, Banana", "Orange, Mango", "Grapes, Watermelon", "Kiwi, Peach"],
    "Vegetable": ["Carrot, Spinach", "Broccoli, Potato", "Tomato, Cucumber", "Pepper, Onion"]
}

# Create DataFrame
df = pd.DataFrame(data)


def show_customer_details(customer_name):
    customer_data = df[df["Customer"] == customer_name].iloc[0]

    with st.dialog(f"Details for {customer_name}"):
        st.subheader(f"Customer: {customer_name}")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Fruits**")
            for fruit in customer_data["Fruit"].split(", "):
                st.write(f"- {fruit}")
        with col2:
            st.markdown("**Vegetables**")
            for veg in customer_data["Vegetable"].split(", "):
                st.write(f"- {veg}")

        if st.button("Close", type="primary"):
            st.rerun()


def show_test():
    st.title("Customer Produce Preferences")
    st.write("Click on a customer name to see their details:")

    # Display the table with clickable rows
    st.data_editor(
        df,
        column_config={
            "Customer": st.column_config.Column(
                "Customer",
                help="Customer names",
                width="medium",
            ),
            "Fruit": st.column_config.Column(
                "Fruits",
                help="Favorite fruits",
                width="medium",
            ),
            "Vegetable": st.column_config.Column(
                "Vegetables",
                help="Favorite vegetables",
                width="medium",
            ),
        },
        hide_index=True,
        use_container_width=True,
        disabled=["Customer", "Fruit", "Vegetable"],
        key="customer_table"
    )

    # Check for row selection
    if st.session_state.get("customer_table", {}).get("edited_rows"):
        selected_row_index = next(iter(st.session_state.customer_table["edited_rows"]))
        customer_name = df.iloc[selected_row_index]["Customer"]
        show_customer_details(customer_name)


def main():
    show_test()


if __name__ == "__main__":
    main()
