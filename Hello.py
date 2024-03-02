# Copyright (c) Streamlit Inc. (2018-2022) Snowflake Inc. (2022)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import streamlit as st
from streamlit.logger import get_logger
import streamlit as st
from pyproj import Proj, transform
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource, HoverTool
from bokeh.tile_providers import CARTODBPOSITRON
from bokeh.transform import factor_cmap
import pandas as pd
import searoute as sr

LOGGER = get_logger(__name__)


def run():
    st.set_page_config(
        page_title="Hello",
        page_icon="👋",
    )


# Define function to get route
def get_route(start_terminal, end_terminal):
    origin = [filtered_df[filtered_df["TerminalName"]==start_terminal]["Longitude"].values[0], filtered_df[filtered_df["TerminalName"]==start_terminal]["Latitude"].values[0]]
    destination = [filtered_df[filtered_df["TerminalName"]==end_terminal]["Longitude"].values[0], filtered_df[filtered_df["TerminalName"]==end_terminal]["Latitude"].values[0]]
    route = sr.searoute(origin, destination)
    return route

# Read terminal data
excel_file_path = 'LNG_Terminals.xlsx'
terminal_df = pd.read_excel(excel_file_path)

# Process DataFrame
for index, row in terminal_df.iterrows():
    if not pd.isna(row['UnitName']):
        terminal_df.at[index, 'TerminalName'] += ' ' + str(row['UnitName'])

# Select required columns and drop NaN values
terminal_df = terminal_df.loc[:, ["TerminalName", "FacilityType", "Status", "Parent", "CapacityInMtpa", "Latitude", "Longitude"]].replace("Unknown",float('nan')).dropna()

# Filter out rows with specific statuses
filtered_df = terminal_df[~terminal_df['Status'].isin(['Shelved', 'Cancelled', 'Idle', 'Mothballed', 'Retired'])]

# Streamlit app begins
st.title("Terminal Route Explorer")

# Display terminal data
st.write("### Filtered Terminals:")
st.write(filtered_df[["TerminalName", "FacilityType"]])

# Get start and end terminal from user
start_terminal = st.text_input("Enter the start terminal:", "West Papua FLNG Terminal")
end_terminal = st.text_input("Enter the end terminal:", "Lubmin FSRU Phase 1")

# Plot terminals on map
st.write("### Terminals Map:")
p = figure(title="World Map with Terminals", width=1100, height=650,
           x_range=(-20037508.342789244, 20037508.342789244), y_range=(-20037508.342789244, 20037508.342789244),
           tools="pan,wheel_zoom,box_zoom,reset,save")

p.add_tile(CARTODBPOSITRON)

color_mapper = factor_cmap(field_name='FacilityType', palette=['blue', 'green'], factors=sorted(filtered_df['FacilityType'].unique()))

operating_source = ColumnDataSource(filtered_df[filtered_df['Status'] == 'Operating'])
construction_source = ColumnDataSource(filtered_df[filtered_df['Status'] == 'Construction'])
proposed_source = ColumnDataSource(filtered_df[filtered_df['Status'] == 'Proposed'])

p.circle(x='Longitude', y='Latitude', size=10, color=color_mapper, source=operating_source, legend_field='FacilityType')
p.triangle(x='Longitude', y='Latitude', size=10, color=color_mapper, source=construction_source, legend_field='FacilityType')
p.cross(x='Longitude', y='Latitude', size=10, color=color_mapper, source=proposed_source, legend_field='FacilityType')

hover = HoverTool(tooltips=[("Name", "@TerminalName"), ("Status", "@Status"), ("Parent", "@Parent"),("Capacity (MTPA)", "@CapacityInMtpa")])
p.add_tools(hover)

st.bokeh_chart(p, use_container_width=True)

# Get route
route = get_route(start_terminal, end_terminal)
coordinates = route["geometry"]["coordinates"]
properties = route.properties

st.write("### Route Details:")
st.write(f"Duration (days): {round(properties['duration_hours']/24, 2)}")
st.write(f"Length (km): {round(properties['length'])}")

# Plot route
route_p = figure(title="Route", width=800, height=400)
route_p.line(x=[coord[0] for coord in coordinates], y=[coord[1] for coord in coordinates], line_color="red", line_width=2)
route_p.add_tools(HoverTool(tooltips=[("Duration (days)", round(properties["duration_hours"]/24, 2)), ("Length (km)", round(properties["length"]))]))

st.bokeh_chart(route_p, use_container_width=True)



if __name__ == "__main__":
    run()
