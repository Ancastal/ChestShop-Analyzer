import pandas as pd
from sqlalchemy import create_engine
import streamlit as st
import matplotlib.pyplot as plt
import plotly.express as px
from streamlit_option_menu import option_menu

st.set_page_config(page_title="Price Tracker", page_icon=":moneybag:")

selected = option_menu(None, ["Price Tracker", "Sales", "Purchases", "About"], orientation="horizontal")

def get_common_price(item, quantity):
    try:
        most_common_price = df[(df["item_name"] == item) & (df["quantity"] == quantity)]["price"].mode()[0]
    except:
        most_common_price = df[(df["item_name"] == item)]["price"].div(df["quantity"]).median()
        most_common_price *= quantity
    return most_common_price

def get_average_price(item, quantity):
    try:
        average_price = df[(df["item_name"] == item) & (df["quantity"] == quantity)]["price"].mean()[0]
    except:
        average_price = df[(df["item_name"] == 'Painting')]["price"].div(df["quantity"]).mean()
        average_price *= int(quantity)
    return average_price

# Create a function to plot the mean prices over time
def plot_means(mean_prices, item):
    fig = px.line(mean_prices, x=mean_prices.index, y=mean_prices.values, labels={'x': 'Date', 'y': 'Average Price'}, title=f'{item} Price Change Over Time')
    return fig

with open("static/style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# The rest of your code remains unchanged

# Replace the line 'st.plotly_chart(plot_means(mean_prices))' with the following line:


@st.cache_data
def get_data(transaction_type) -> pd.DataFrame:
    engine = create_engine(f"sqlite:///{transaction_type}.db", echo=False)
    try:
        with engine.connect() as connection:
            df = pd.read_sql("SELECT * FROM transactions", con=connection)
        return df
    except:
        st.error("Failed to load data from the database")

if selected == "Price Tracker":
    df = get_data('bought_transactions')
    st.markdown("<h1 style='text-align: center;'>Price Tracker</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center;'>A simple app to track prices of items in BusinessCraft</h3>", unsafe_allow_html=True)
    st.divider()

    col1, col2 = st.columns([3, 1])
    with col1:
        item = st.selectbox("Select the item", df["item_name"].unique(), index=0)
    with col2:
        quantity = st.text_input("Qty", "10")

    if st.button("Get price"):
        st.text(f"The most common price for {quantity} {item} is {get_common_price(item, int(quantity)):.2f} Krunas")
        st.text(f"The average price for {quantity} {item} is {get_average_price(item, quantity):.2f} Krunas")
        st.divider()
        st.text(f"The median price for {item} is {df[(df['item_name'] == item)]['price'].median():.2f} Krunas")
        st.text(f"The minimum price for {item} is {df[(df['item_name'] == item)]['price'].min():.2f} Krunas")
        st.text(f"The maximum price for {item} is {df[(df['item_name'] == item)]['price'].max():.2f} Krunas")
        st.text(f"The total number of transactions for {item} is {df[(df['item_name'] == item)]['price'].count():.2f}")
        st.text(f"The total amount of Krunas spent on {item} is {df[(df['item_name'] == item)]['price'].sum():.2f} Krunas")
        # Group the filtered data by 'timestamp' and calculate the mean price for each date
        mean_prices = df[df['item_name'] == item].groupby('timestamp')['price'].mean()
        st.plotly_chart(plot_means(mean_prices, item), use_container_width=True)
elif selected == 'Sales':
    df = get_data('sales_transactions')
    st.markdown("<h1 style='text-align: center;'>Player Sales</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center;'>A simple app to track Sales in BusinessCraft</h3>", unsafe_allow_html=True)
    st.divider()
    username = st.selectbox("Select the seller", df["seller"].unique(), index=0)
    if st.button("Get Sales"):
        st.dataframe(df[(df["seller"] == username) & (df["action"] == "sold")])
elif selected == 'Purchases':
    df = get_data('bought_transactions')
    st.markdown("<h1 style='text-align: center;'>Player Purchases</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center;'>A simple app to track player purchases in BusinessCraft</h3>", unsafe_allow_html=True)
    st.divider()
    username = st.selectbox("Select the player", df["username"].unique(), index=0)
    if st.button("Get Purchases"):
        st.dataframe(df[(df["username"] == username) & (df["action"] == "bought")].drop_duplicates(subset=['item_name', 'price']))

elif selected == 'About':
    st.markdown("<h1 style='text-align: center;'>About Price Tracker</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center;'>Frequently Asked Questions</h3>", unsafe_allow_html=True)
    st.divider()
    st.subheader("What is this app?")
    st.write("This is a simple app to track prices of items in BusinessCraft")
    st.subheader("How does it work?")
    st.write("The app uses the logs from the BusinessCraft server to track prices of items. The logs are parsed using a Python script and the data is stored in a SQLite database. The app uses Streamlit to display the data.")
    st.subheader("Who made this app?")
    st.write("This app was made by Ancastal")
    st.subheader("How can I contribute?")
    st.write("You can contribute to this app by reporting bugs, or by suggesting new features.")
    st.subheader("How can I contact Ancastal?")
    st.write("You can contact Ancastal on Discord: Ancastal#0506")
