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
from pyproj import Proj, transform
from bokeh.plotting import figure, output_notebook, show
from bokeh.models import ColumnDataSource, HoverTool
from bokeh.tile_providers import get_provider, CARTODBPOSITRON, Vendors
from bokeh.transform import factor_cmap
import pandas as pd
from pyproj import Proj, transform
import warnings
from bokeh.plotting import output_file, show
import searoute as sr


LOGGER = get_logger(__name__)


def run():
    st.set_page_config(
        page_title="LNG Terminals and Routes",
        page_icon="sailboat",
    )
   # Read the terminal data
    excel_file_path = 'LNG_Terminals.xlsx'
    terminal_df = pd.read_excel(excel_file_path)

    # Process the DataFrame
    for index, row in terminal_df.iterrows():
        if not pd.isna(row['UnitName']):
            terminal_df.at[index, 'TerminalName'] += ' ' + str(row['UnitName'])
    
    # Select required columns and drop NaN values
    terminal_df = terminal_df.loc[:, ["TerminalName", "FacilityType", "Status", "Parent", "CapacityInMtpa", "Latitude", "Longitude"]].replace("Unknown", float('nan')).dropna()
    
    # Convert latitude and longitude to numeric type
    terminal_df['Latitude'] = pd.to_numeric(terminal_df['Latitude'], errors='coerce')
    terminal_df['Longitude'] = pd.to_numeric(terminal_df['Longitude'], errors='coerce')
    lon_lat_proj = Proj(proj='latlong', datum='WGS84')
    mercator_proj = Proj(proj='merc', datum='WGS84')
    terminal_df['MercatorLon'], terminal_df['MercatorLat'] = zip(*[transform(lon_lat_proj, mercator_proj, lon, lat) for lon, lat in zip(terminal_df['Longitude'], terminal_df['Latitude'])])

    # Function to get route
    def get_route(start_terminal, end_terminal, speed_knot=15,restrictions=["northwest"]):
        origin = [terminal_df[terminal_df["TerminalName"] == start_terminal]["Longitude"].values[0],
                  terminal_df[terminal_df["TerminalName"] == start_terminal]["Latitude"].values[0]]
        destination = [terminal_df[terminal_df["TerminalName"] == end_terminal]["Longitude"].values[0],
                       terminal_df[terminal_df["TerminalName"] == end_terminal]["Latitude"].values[0]]
        route = sr.searoute(origin=origin, destination=destination,speed_knot=speed_knot,restrictions=restrictions)
        return route
    
    # Streamlit App
    # st.title("Terminal Route Visualization")
    st.markdown("<h1 style='text-align: center;'><i class='fas fa-ship'></i> Terminal Route Visualization <i class='fas fa-ship'></i></h1>", unsafe_allow_html=True)
    # User input for start and end terminals
    start_terminal = st.selectbox("Select Start Terminal:", options=terminal_df[terminal_df["FacilityType"] == "Export"]["TerminalName"].tolist(), index=9)
    end_terminal = st.selectbox("Select End Terminal:", options=terminal_df[terminal_df["FacilityType"] == "Import"]["TerminalName"].tolist(), index=terminal_df[terminal_df["FacilityType"] == "Import"]["TerminalName"].tolist().index("Le Havre FSRU"))
    
    passage=["babalmandab","bosporus","gibraltar","suez","panama","ormuz"]
    selected_values = st.multiselect('Select unaccessible routes:', passage)+["northwest"]
    speed_knot = st.slider('Vessel speed (knots):', min_value=0, max_value=30, value=15)
    # Get route
    route = get_route(start_terminal, end_terminal,speed_knot,selected_values)
    properties=route.properties
    properties["duration_hours"]=round(properties["duration_hours"]/24,2)
    properties["length"]=round(properties["length"])
    # Convert coordinates to Mercator projection
    lon_lat_proj = Proj(proj='latlong', datum='WGS84')
    mercator_proj = Proj(proj='merc', datum='WGS84')
    coordinates = route["geometry"]["coordinates"]
    mercator_coords = [transform(lon_lat_proj, mercator_proj, lon, lat) for lon, lat in coordinates]
    
    # Plot
    st.subheader("Map with Route")
    p = figure(title="World Map with Terminals", width=1000, height=600,
               x_range=(-20037508.342789244, 20037508.342789244),
               y_range=(-20037508.342789244, 20037508.342789244),
               tools="pan,wheel_zoom,reset,save",active_scroll="wheel_zoom")
    
    tile_provider = get_provider(Vendors.CARTODBPOSITRON)
    p.add_tile(tile_provider)
    
    # Plot terminals
    color_mapper = factor_cmap(field_name='FacilityType', palette=['blue', 'green'], factors=sorted(terminal_df['FacilityType'].unique()))
    operating_source = ColumnDataSource(terminal_df[terminal_df['Status'] == 'Operating'])
    construction_source = ColumnDataSource(terminal_df[terminal_df['Status'] == 'Construction'])
    proposed_source = ColumnDataSource(terminal_df[terminal_df['Status'] == 'Proposed'])

    circle=p.circle(x='MercatorLon', y='MercatorLat', size=10, color=color_mapper, source=operating_source, legend_field='FacilityType')
    triangle=p.triangle(x='MercatorLon', y='MercatorLat', size=10, color=color_mapper, source=construction_source, legend_field='FacilityType')
    cross=p.cross(x='MercatorLon', y='MercatorLat', size=10, color=color_mapper, source=proposed_source, legend_field='FacilityType')
    circle_hover = HoverTool(renderers=[circle],tooltips=[("Name", "@TerminalName"), ("Status", "@Status"), ("Parent", "@Parent"), ("Capacity (MTPA)", "@CapacityInMtpa")])
    p.add_tools(circle_hover)
    triangle_hover = HoverTool(renderers=[triangle],tooltips=[("Name", "@TerminalName"), ("Status", "@Status"), ("Parent", "@Parent"), ("Capacity (MTPA)", "@CapacityInMtpa")])
    p.add_tools(triangle_hover)
    cross_hover = HoverTool(renderers=[cross],tooltips=[("Name", "@TerminalName"), ("Status", "@Status"), ("Parent", "@Parent"), ("Capacity (MTPA)", "@CapacityInMtpa")])
    p.add_tools(cross_hover)
    
    # Plot route
    lon = [coord[0] for coord in mercator_coords]
    lat = [coord[1] for coord in mercator_coords]
    source = ColumnDataSource(data=dict(lon=lon, lat=lat, duration_hours=[properties["duration_hours"]]*len(lon), length=[properties["length"]]*len(lon)))
    # Add line glyphs to the figure
    line = p.line(x="lon", y="lat", source=source, line_color="red", line_width=2)
    
    # Define hover tool with renderers argument set to both line and dummy circle renderers
    line_hover = HoverTool(renderers=[line], tooltips=[("Duration (days)", "@duration_hours"), ("Length (km)", "@length")])
    p.add_tools(line_hover)
    st.bokeh_chart(p, use_container_width=True)
    st.subheader("Terminal Data")
    st.write(terminal_df[terminal_df["TerminalName"] == start_terminal])
    st.write(terminal_df[terminal_df["TerminalName"] == end_terminal])
    st.subheader("Road estimation")
    st.write(pd.DataFrame({"Length (km)":properties["length"],"Duration (days)":properties["duration_hours"]},index=["Road Estimation"]))
    st.markdown("Terminals data : Global Gas Infrastructure Tracker, Global Energy Monitor, october 2023.")
    st.markdown("Routes data : searoute")
if __name__ == "__main__":
    run()
