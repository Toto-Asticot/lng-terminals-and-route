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
        page_title="Hello",
        page_icon="👋",
    )
   @st.cache
    def get_route(start_terminal, end_terminal, filtered_df):
        origin = [filtered_df[filtered_df["TerminalName"]==start_terminal]["Longitude"].values[0], filtered_df[filtered_df["TerminalName"]==start_terminal]["Latitude"].values[0]]
        destination = [filtered_df[filtered_df["TerminalName"]==end_terminal]["Longitude"].values[0], filtered_df[filtered_df["TerminalName"]==end_terminal]["Latitude"].values[0]]
        route = sr.searoute(origin, destination)
        return route
    
    # Read the Excel file into a pandas DataFrame
    excel_file_path = 'LNG_Terminals.xlsx'
    terminal_df = pd.read_excel(excel_file_path)
    
    # Process DataFrame
    for index, row in terminal_df.iterrows():
        if not pd.isna(row['UnitName']):
            terminal_df.at[index, 'TerminalName'] += ' ' + str(row['UnitName'])
    
    # Select required columns and drop NaN values
    terminal_df = terminal_df.loc[:, ["TerminalName", "FacilityType", "Status", "Parent", "CapacityInMtpa", "Latitude", "Longitude"]].replace("Unknown",float('nan')).dropna()
    
    # Convert latitude and longitude to numeric type
    terminal_df['Latitude'] = pd.to_numeric(terminal_df['Latitude'], errors='coerce')
    terminal_df['Longitude'] = pd.to_numeric(terminal_df['Longitude'], errors='coerce')
    
    # Filter out rows with specific statuses
    filtered_df = terminal_df[~terminal_df['Status'].isin(['Shelved', 'Cancelled', 'Idle', 'Mothballed', 'Retired'])]
    
    # Streamlit UI
    st.title('LNG Terminal Route Mapper')
    
    # Display filtered terminal names and types
    st.write(filtered_df[["TerminalName", "FacilityType"]])
    
    # User input for start and end terminals
    start_terminal = st.selectbox("Select start terminal:", filtered_df["TerminalName"].tolist())
    end_terminal = st.selectbox("Select end terminal:", filtered_df["TerminalName"].tolist())
    
    # Get route
    route = get_route(start_terminal, end_terminal, filtered_df)
    
    # Plotting with Bokeh
    p = figure(title="World Map with Terminals", width=1100, height=650, 
               x_range=(-20037508.342789244, 20037508.342789244), y_range=(-20037508.342789244, 20037508.342789244),
               tools="pan,wheel_zoom,box_zoom,reset,save")
    p.add_tile(CARTODBPOSITRON)
    
    # Plot terminals
    color_mapper = factor_cmap(field_name='FacilityType', palette=['blue', 'green'], factors=sorted(filtered_df['FacilityType'].unique()))
    operating_source = ColumnDataSource(filtered_df[filtered_df['Status'] == 'Operating'])
    construction_source = ColumnDataSource(filtered_df[filtered_df['Status'] == 'Construction'])
    proposed_source = ColumnDataSource(filtered_df[filtered_df['Status'] == 'Proposed'])
    
    p.circle(x='Longitude', y='Latitude', size=10, color=color_mapper, source=operating_source, legend_field='FacilityType')
    p.triangle(x='Longitude', y='Latitude', size=10, color=color_mapper, source=construction_source, legend_field='FacilityType')
    p.cross(x='Longitude', y='Latitude', size=10, color=color_mapper, source=proposed_source, legend_field='FacilityType')
    
    # Plot route
    coordinates = route["geometry"]["coordinates"]
    lon_lat_proj = Proj(proj='latlong', datum='WGS84')
    mercator_proj = Proj(proj='merc', datum='WGS84')
    in_proj = Proj(init='epsg:4326')
    out_proj = Proj(init='epsg:3857')
    mercator_coords = [transform(in_proj, out_proj, lon, lat) for lon, lat in coordinates]
    lon = [coord[0] for coord in mercator_coords]
    lat = [coord[1] for coord in mercator_coords]
    source = ColumnDataSource(data=dict(lon=lon, lat=lat))
    line = p.line(x="lon", y="lat", source=source, line_color="red", line_width=2)
    
    # Hover tooltip
    hover = HoverTool(renderers=[line], tooltips=[("Duration (days)", f"{round(route['properties']['duration_hours'] / 24, 2)}"), ("Length (km)", f"{round(route['properties']['length'])}")])
    p.add_tools(hover)
    
    # Display the plot
    st.bokeh_chart(p, use_container_width=True)

if __name__ == "__main__":
    run()
