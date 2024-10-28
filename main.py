import streamlit as st
import pydeck as pdk
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import json


colour_scales = {"viridis": plt.cm.viridis}
cmap = plt.cm.viridis

st.set_page_config(layout="wide")

data = pd.read_excel(
    r"essex_data.xlsx",
    sheet_name = "Data")
data_info = pd.read_excel(
    r"essex_data.xlsx",
    sheet_name = "DataDictionary")

# mapping between column name and full name
field_lookup = {}
for i in data_info.index:
    field_lookup[
        f"{data_info["Description"][i]}, {data_info["Sex"][i]}, {data_info["Year"][i]}"
        ] = data_info["Field_Name"][i]

st.title("Essex MSOA Statistics")

col_name_selection = st.selectbox(
    label = "Select a criteria to set colour by",
    options = (f for f in field_lookup),
    key = 4564346573746576
)
height_name_selection = st.selectbox(
    label = "Select a criteria to set elevation by",
    options = (f for f in field_lookup),
    key = "height_name_selection"
)

col_selection = field_lookup[col_name_selection]
height_selecton = field_lookup[height_name_selection]

max_height = 5000

#get colour distribution for the stat selection
data['col_selection_norm'] = (data[col_selection] - data[col_selection].min()) / (data[col_selection].max() - data[col_selection].min())
data['height_selection_norm'] = (data[height_selecton] - data[height_selecton].min()) / (data[height_selecton].max() - data[height_selecton].min())

data['colour'] = data['col_selection_norm'].apply(lambda x: [int(255 * x), 0, int(255 * (1 - x))])
data['colour'] = data['col_selection_norm'].apply(lambda x: list(cmap(x)[:3]))  # Get RGB as a 3-tuple, ignore alpha

data['height'] = data["height_selection_norm"]*max_height

# Scale RGB values to 0-255 range
data['colour'] = data['colour'].apply(lambda rgb: [int(255 * v) for v in rgb])

def get_area_code_data(area_code, data, stat_cols):
    print(area_code)

    with open(rf'area_code_geojson/{area_code}.geojson') as f:
        geodata = json.load(f)

    # append statistics to geojson
    for s in stat_cols:
        stat = round(data.loc[
            data["Area Code"] == area_code, s].max(),
            2)
        geodata['features'][0][s] = stat
    return geodata


def get_geo_data(data, stat_cols):
    geo_data = data["Area Code"].apply(lambda x: get_area_code_data(
        x, data, stat_cols)
        )

    return geo_data

layers = []
geo_data = get_geo_data(data = data, stat_cols = [field_lookup[f] for f in field_lookup])
for i in data.index:
    #areacode = data["Area Code"][i]
   
    elevation = str(data["height"][i])
    fill_colour = str(data['colour'][i])

    layer_i = pdk.Layer(
        "GeoJsonLayer",
        geo_data[i], #f"https://findthatpostcode.uk/areas/{areacode}.geojson",
        stroked=False,
        filled=True,
        extruded=True,
        wireframe=True,
        get_elevation=elevation,
        get_fill_color=fill_colour,
        get_line_color=[255, 255, 255],
        pickable=True
    )
    layers.append(layer_i)

tooltip_label = "<b>{name}</b><br/><br/>"
for s in [field_lookup[col_name_selection], field_lookup[height_name_selection]]:
    tooltip_label = f"{tooltip_label}<b>{s}: </b>{{{s}}}<br/>"

map = st.pydeck_chart(
    pydeck_obj = pdk.Deck(
        map_style=None,
        initial_view_state=pdk.ViewState(
            latitude=51.81,
            longitude=0.54,
            zoom=9,
            pitch=50,
        ),
        layers=layers,
        tooltip = {"html": tooltip_label,
                        "style": {
                                "backgroundColor": "steelblue",
                                "color": "white"
                        }
                    }
    )
)

#Add a color scale legend
colours = ",".join([mcolors.to_hex(cmap(i / 10)) for i in range(11)])
min_val = round(min(data[col_selection]), 2)
mid_val = round((min(data[col_selection]) + max(data[col_selection])) / 2, 2)
max_val = round(max(data[col_selection]), 2)
color_scale_html = f"""
    <div style="text-align: center">{col_name_selection}</div>
    <div style="position: relative; top: 0px; height: 30px; width: 100%;">
        <div style="background: linear-gradient(to right, {colours}); width: 100%; height: 10px;"></div>
        <div style="display: flex; justify-content: space-between; font-size: small;">
            <span>{min_val}</span><span>{mid_val}</span><span>{max_val}</span>
        </div>
    </div>
"""

#st.text(str(col_name_selection))
st.markdown(color_scale_html, unsafe_allow_html=True)

st.write('')
st.write('')
st.write('MSOA polgons obtained from https://findthatpostcode.uk/')
st.write('Source data supplied by Essex County Council')