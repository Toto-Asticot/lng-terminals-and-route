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
    
    # Function to get route
    def get_route(start_terminal, end_terminal):
        origin = [filtered_df[filtered_df["TerminalName"] == start_terminal]["Longitude"].values[0],
                  filtered_df[filtered_df["TerminalName"] == start_terminal]["Latitude"].values[0]]
        destination = [filtered_df[filtered_df["TerminalName"] == end_terminal]["Longitude"].values[0],
                       filtered_df[filtered_df["TerminalName"] == end_terminal]["Latitude"].values[0]]
        route = sr.searoute(origin, destination)
        return route
    
    # Streamlit App
    st.title("Terminal Route Visualization")
    
    # Display terminal data
    st.subheader("Terminal Data")
    st.write(filtered_df[["TerminalName", "FacilityType"]])
    
    # User input for start and end terminals
    start_terminal = st.selectbox("Select Start Terminal:", options=filtered_df["TerminalName"].tolist())
    end_terminal = st.selectbox("Select End Terminal:", options=filtered_df["TerminalName"].tolist())
    
    # Get route
    route = get_route(start_terminal, end_terminal)
    
    # Convert coordinates to Mercator projection
    lon_lat_proj = Proj(proj='latlong', datum='WGS84')
    mercator_proj = Proj(proj='merc', datum='WGS84')
    coordinates = route["geometry"]["coordinates"]
    mercator_coords = [transform(lon_lat_proj, mercator_proj, lon, lat) for lon, lat in coordinates]
    
    # Plot
    st.subheader("Map with Route")
    p = figure(title="World Map with Terminals", width=800, height=600,
               x_range=(-20037508.342789244, 20037508.342789244),
               y_range=(-20037508.342789244, 20037508.342789244),
               tools="pan,wheel_zoom,box_zoom,reset,save")
    
    p.add_tile(Vendors.CARTODBPOSITRON)
    
    # Plot terminals
    for status in filtered_df['Status'].unique():
        source = ColumnDataSource(filtered_df[filtered_df['Status'] == status])
        p.circle(x='MercatorLon', y='MercatorLat', size=10, color='blue' if status == 'Operating' else 'green', source=source)
    
    # Plot route
    lon = [coord[0] for coord in mercator_coords]
    lat = [coord[1] for coord in mercator_coords]
    source = ColumnDataSource(data=dict(lon=lon, lat=lat))
    p.line(x="lon", y="lat", source=source, line_color="red", line_width=2)
    
    # Hover tool
    hover = HoverTool(tooltips=[("Name", "@TerminalName"), ("Status", "@Status"), ("Parent", "@Parent"), ("Capacity (MTPA)", "@CapacityInMtpa")])
    p.add_tools(hover)
    
    st.bokeh_chart(p, use_container_width=True)

# Define function to get route
def get_route(start_terminal, end_terminal):
    origin = [filtered_df[filtered_df["TerminalName"]==start_terminal]["Longitude"].values[0], filtered_df[filtered_df["TerminalName"]==start_terminal]["Latitude"].values[0]]
    destination = [filtered_df[filtered_df["TerminalName"]==end_terminal]["Longitude"].values[0], filtered_df[filtered_df["TerminalName"]==end_terminal]["Latitude"].values[0]]
    route = sr.searoute(origin, destination)
    return route





if __name__ == "__main__":
    run()
