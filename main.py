import streamlit as st
import pandas as pd
import numpy as np
import pydeck as pdk
import plotly.express as px

data_path = (
    "C:/Users/User/PycharmProjects/StreamlitApp/Motor_Vehicle_Collisions_-_Crashes.csv"
)


st.title("Motor Vehicle Collisions in New York City")
st.markdown("This is a streamlit dashboard application that can be used to analyze motor vehicle collisions in NYC")


@st.cache(persist=True)
def load_data(nrows):
    data = pd.read_csv(data_path, nrows=nrows, parse_dates=[["CRASH_DATE", "CRASH_TIME"]])
    data.dropna(subset=['LATITUDE', 'LONGITUDE'], inplace=True)
    data.rename(lambda x: str(x).lower(), axis='columns', inplace=True)
    data.rename(columns={"crash_date_crash_time": "date/time"}, inplace=True)
    data = data.drop(data[(data.latitude < 40) | (data.latitude > 50)].index)
    data = data.drop(data[(data.longitude > -65) | (data.longitude < -80)].index)
    return data


data = load_data(100000)
original_data = data

st.header("Where are most people injured in NYC?")
injured_people = st.slider("Number of injured people", 0, 19, 2)
st.map(data.query("injured_persons >= @injured_people")[['latitude', 'longitude']].dropna(how='any'))

if st.sidebar.checkbox('Filer by hour of day', False):
    st.header("How many collisions occur during a given time of day?")
    hour = st.slider("Hour to look at", 0, 23)
    data = data[data["date/time"].dt.hour == hour]

    st.markdown("Vehicle collisions between %i:00 and %i:59" % (hour % 24, hour % 24))
    midpoint = (np.average(data['latitude']), np.average(data['longitude']))

    st.write(pdk.Deck(
        map_style="mapbox://styles/mapbox/light-v9",
        initial_view_state={
            "latitude": midpoint[0],
            "longitude": midpoint[1],
            "zoom": 9,
            "pitch": 50,
        },
        layers=[
            pdk.Layer(
                "HexagonLayer",
                data=data[['date/time', 'latitude', 'longitude']],
                get_position=['longitude', 'latitude'],
                radius=100,
                extruded=True,
                pickable=True,
                elevation_scale=4,
                elevation_range=[0, 1000],
            )
        ]
    ))

    st.subheader("Breakdown by minute between %i:00 and %i:59" % (hour % 24, hour % 24))
    filtered = data[
        (data['date/time'].dt.hour >= hour) & (data['date/time'].dt.hour < (hour+1))
    ]
    hist = np.histogram(filtered['date/time'].dt.minute, bins=60, range=(0, 60))[0]
    chart_data = pd.DataFrame({'minute': range(60), 'crashes': hist})
    fig = px.bar(chart_data, x='minute', y='crashes', hover_data=['minute', 'crashes'], height=400)
    st.write(fig)

st.header("Top 5 most dangerous streets by affected type")
select = st.selectbox('Affected type of people', ["Pedestrians", "Cyclists", "Motorists"])

if select == "Pedestrians":
    st.write(original_data.query("injured_pedestrians >= 1")[["on_street_name", "injured_pedestrians"]].sort_values(
        by=['injured_pedestrians'], ascending=False).dropna(how='any')[:5])
elif select == "Cyclists":
    st.write(original_data.query("injured_cyclists >= 1")[["on_street_name", "injured_cyclists"]].sort_values(
        by=['injured_cyclists'], ascending=False).dropna(how='any')[:5])
else:
    st.write(original_data.query("injured_motorists >= 1")[["on_street_name", "injured_motorists"]].sort_values(
        by=['injured_motorists'], ascending=False).dropna(how='any')[:5])

if st.checkbox('Show raw data', False):
    st.subheader('Raw data')
    st.write(data)
