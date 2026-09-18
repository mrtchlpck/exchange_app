import streamlit as st
import requests
import pandas as pd
import plotly.express as px


# -----------------------------
# PAGE CONFIG
# -----------------------------
st.set_page_config(
    page_title="Currency Exchange Explorer",
    page_icon="💱",
    layout="wide"
)


# -----------------------------
# CURRENCY DATA
# -----------------------------
CURRENCY_NAMES = {
    "USD": "US Dollar",
    "EUR": "Euro",
    "GBP": "British Pound",
    "DKK": "Danish Krone",
    "SEK": "Swedish Krona",
    "NOK": "Norwegian Krone",
    "PLN": "Polish Zloty",
    "CHF": "Swiss Franc",
    "CZK": "Czech Koruna",
    "HUF": "Hungarian Forint",
    "RON": "Romanian Leu",
    "BGN": "Bulgarian Lev",
    "ISK": "Icelandic Krona",
    "CAD": "Canadian Dollar",
    "MXN": "Mexican Peso",
    "BRL": "Brazilian Real",
    "ARS": "Argentine Peso",
    "CLP": "Chilean Peso",
    "COP": "Colombian Peso",
    "PEN": "Peruvian Sol",
    "JPY": "Japanese Yen",
    "CNY": "Chinese Yuan",
    "KRW": "South Korean Won",
    "INR": "Indian Rupee",
    "IDR": "Indonesian Rupiah",
    "THB": "Thai Baht",
    "MYR": "Malaysian Ringgit",
    "SGD": "Singapore Dollar",
    "PHP": "Philippine Peso",
    "VND": "Vietnamese Dong",
    "AUD": "Australian Dollar",
    "NZD": "New Zealand Dollar",
    "ZAR": "South African Rand",
    "EGP": "Egyptian Pound",
    "NGN": "Nigerian Naira",
    "KES": "Kenyan Shilling",
    "MAD": "Moroccan Dirham",
    "AED": "UAE Dirham",
    "SAR": "Saudi Riyal",
    "ILS": "Israeli New Shekel",
    "TRY": "Turkish Lira",
    "RUB": "Russian Ruble",
}


# -----------------------------
# CONTINENT MAPPING
# -----------------------------
CONTINENTS = {
    "Europe": [
        "EUR", "GBP", "DKK", "SEK", "NOK", "PLN",
        "CHF", "CZK", "HUF", "RON", "BGN", "ISK",
        "TRY", "RUB"
    ],

    "North America": [
        "USD", "CAD", "MXN"
    ],

    "South America": [
        "BRL", "ARS", "CLP", "COP", "PEN"
    ],

    "Asia": [
        "JPY", "CNY", "KRW", "INR", "IDR", "THB",
        "MYR", "SGD", "PHP", "VND", "AED", "SAR",
        "ILS"
    ],

    "Africa": [
        "ZAR", "EGP", "NGN", "KES", "MAD"
    ],

    "Oceania": [
        "AUD", "NZD"
    ],
}


# -----------------------------
# API FUNCTION
# -----------------------------
@st.cache_data(ttl=86400)
def get_exchange_rates(base_currency):
    api_key = st.secrets["EXCHANGE_RATE_API_KEY"]

    url = (
        f"https://v6.exchangerate-api.com/"
        f"v6/{api_key}/latest/{base_currency}"
    )

    response = requests.get(url, timeout=10)

    if response.status_code != 200:
        raise Exception(
            f"API request failed with status code "
            f"{response.status_code}"
        )

    data = response.json()

    if data.get("result") != "success":
        raise Exception(
            data.get("error-type", "Unknown API error")
        )

    return data


# -----------------------------
# TITLE
# -----------------------------
st.title("💱 Currency Exchange Explorer")

st.write(
    """
    This app allows you to convert an amount from one currency to another
    and explore how the same amount compares across currencies from
    different continents.
    """
)


# -----------------------------
# SIDEBAR
# -----------------------------
st.sidebar.header("Currency converter")

currency_options = sorted(CURRENCY_NAMES.keys())

from_currency = st.sidebar.selectbox(
    "From currency",
    currency_options,
    index=currency_options.index("EUR")
)

to_currency = st.sidebar.selectbox(
    "To currency",
    currency_options,
    index=currency_options.index("DKK")
)

amount = st.sidebar.number_input(
    "Amount",
    min_value=0.01,
    value=100.00,
    step=10.00
)


# -----------------------------
# LOAD API DATA
# -----------------------------
try:
    data = get_exchange_rates(from_currency)
    rates = data["conversion_rates"]

except Exception as e:
    st.error(f"Could not load exchange rates: {e}")
    st.stop()


# -----------------------------
# MAIN CONVERSION
# -----------------------------
if to_currency not in rates:
    st.error(
        f"No exchange rate available for {to_currency}."
    )
    st.stop()

exchange_rate = rates[to_currency]
converted_amount = amount * exchange_rate


st.subheader("Your conversion")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "Amount",
        f"{amount:,.2f} {from_currency}"
    )

with col2:
    st.metric(
        "Exchange rate",
        f"1 {from_currency} = {exchange_rate:,.4f} {to_currency}"
    )

with col3:
    st.metric(
        "Converted amount",
        f"{converted_amount:,.2f} {to_currency}"
    )


# -----------------------------
# CONTINENT SELECTION
# -----------------------------
st.divider()

st.subheader("🌍 Compare currencies by continent")

st.write(
    "Choose a continent to see how your amount converts into "
    "currencies from that region."
)

selected_continent = st.selectbox(
    "Select continent",
    list(CONTINENTS.keys())
)


# -----------------------------
# CURRENCIES FOR SELECTED CONTINENT
# -----------------------------
continent_currencies = [
    currency
    for currency in CONTINENTS[selected_continent]
    if currency in rates and currency != from_currency
]


# Add selected "To currency" if it is not already in the continent
if (
    to_currency in rates
    and to_currency != from_currency
    and to_currency not in continent_currencies
):
    continent_currencies.insert(0, to_currency)


if len(continent_currencies) == 0:
    st.warning(
        "There are no available currencies for this continent."
    )
    st.stop()


# -----------------------------
# CREATE CHART DATA
# -----------------------------
chart_data = pd.DataFrame({
    "Currency": continent_currencies,
    "Amount": [
        amount * rates[currency]
        for currency in continent_currencies
    ]
})

chart_data["Currency name"] = chart_data["Currency"].map(
    lambda x: CURRENCY_NAMES.get(x, x)
)

chart_data["Label"] = (
    chart_data["Currency"]
    + " – "
    + chart_data["Currency name"]
)


# Sort for easier reading
chart_data = chart_data.sort_values(
    "Amount",
    ascending=True
)


# -----------------------------
# BAR CHART
# -----------------------------
st.subheader(
    f"{amount:,.2f} {from_currency} in {selected_continent} currencies"
)

fig = px.bar(
    chart_data,
    x="Amount",
    y="Label",
    orientation="h",
    text="Amount",
    labels={
        "Amount": f"Amount received ({selected_continent} currencies)",
        "Label": "Currency"
    }
)

fig.update_traces(
    texttemplate="%{text:,.2f}",
    textposition="outside"
)

fig.update_layout(
    height=max(450, len(chart_data) * 55),
    margin=dict(
        l=20,
        r=80,
        t=30,
        b=20
    ),
    showlegend=False
)

st.plotly_chart(
    fig,
    use_container_width=True
)


# -----------------------------
# DATA TABLE
# -----------------------------
st.subheader("Exchange details")

table_data = chart_data[
    ["Currency", "Currency name", "Amount"]
].copy()

table_data["Amount"] = table_data["Amount"].round(2)

st.dataframe(
    table_data,
    use_container_width=True,
    hide_index=True
)


# -----------------------------
# LAST UPDATE
# -----------------------------
if "time_last_update_utc" in data:
    st.caption(
        f"Exchange rates last updated: "
        f"{data['time_last_update_utc']}"
    )

st.caption(
    "Note: the chart shows how many units of each currency "
    "you receive for the same amount of the selected base currency. "
    "A longer bar does not necessarily mean that a currency is "
    "stronger or weaker, because currencies have different denominations."
)
