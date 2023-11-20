import numpy as np
import pandas as pd

import networkx as nx
from pyvis.network import Network

import holoviews as hv
from holoviews import opts

from bokeh.models import TapTool, OpenURL, HoverTool, Div, CustomJS, ColumnDataSource
from bokeh.events import MouseWheel, DoubleTap, Tap, DocumentReady
from bokeh.layouts import column, row
from bokeh.io import show, curdoc

hv.extension('bokeh')



schema = {
    "Name (English)": object,
    # "Name (Chinese)": object,
    "Region of Focus": "category",
    "Language": "category",
    "Entity owner (English)": "category",
    # "Entity owner (Chinese)": "category",
    "Parent entity (English)": "category",
    # "Parent entity (Chinese)": "category",
    "X (Twitter) handle": object,
    "X (Twitter) URL": object,
    "X (Twitter) Follower #": "Int64",
    "Facebook page": object,
    "Facebook URL": object,
    "Facebook Follower #": "Int64",
    "Instragram page": object,
    "Instagram URL": object,
    "Instagram Follower #": "Int64",
    "Threads account": object,
    "Threads URL": object,
    "Threads Follower #": "Int64",
    "YouTube account": object,
    "YouTube URL": object,
    "YouTube Subscriber #": "Int64",
    "TikTok account": object,
    "TikTok URL": object,
    "TikTok Subscriber #": "Int64",
}

canis_data = pd.read_excel(
    'CANIS_PRC_state_media_on_social_media_platforms-2023-11-03.xlsx',
    dtype=schema,
)[schema.keys()]

# Create a new column that stores the number of enities in the entity owner column owned by the same entity parent
canis_data["Parent entity (English) Children #"] = (
    canis_data
    .groupby("Parent entity (English)")
    ["Name (English)"]
    .transform("count")
    .astype(float)
)

# Create a graph
G = nx.Graph()

G.add_nodes_from(
    canis_data["Name (English)"],
)

G.add_nodes_from(
    canis_data["Entity owner (English)"],
)

G.add_nodes_from(
    canis_data["Parent entity (English)"],
)


edges_lvl_1 = [
    tuple(row) for row in 
    canis_data[["Parent entity (English)", "Entity owner (English)"]]
    .itertuples(index=False, name=None)
]

edges_lvl_2 = [
    tuple(row) for row in 
    canis_data[["Entity owner (English)", "Name (English)"]]
    .itertuples(index=False, name=None)
]

G.add_edges_from(
    edges_lvl_1
)
G.add_edges_from(
    edges_lvl_2
)

net_layout = nx.layout.spring_layout(G)

# Lables for the graph
label_data = [(net_layout[node][0], net_layout[node][1], str(node)) for node in G.nodes]

# Create labels with correct data format
labels = hv.Labels(label_data, ['x', 'y'], 'text')

for node in G.nodes:
    G.nodes[node]['name'] = node
    if node in canis_data["Name (English)"].unique():
        G.nodes[node]['url'] = (canis_data
                                [canis_data["Name (English)"] == node]
                                ["X (Twitter) URL"]
                                .iloc[0])
        G.nodes[node]['color'] = "#0000FF"
        G.nodes[node]['size'] = 10
    elif node in canis_data["Entity owner (English)"].unique(): 
        G.nodes[node]['url'] = ""
        G.nodes[node]['color'] = "#00FF00"
        G.nodes[node]['size'] = 10
        
    else:
        G.nodes[node]['url'] = ""
        G.nodes[node]['color'] = "#FF0000"
        G.nodes[node]['size'] = np.sqrt((canis_data
                                         [canis_data["Parent entity (English)"] == node]
                                         ["Parent entity (English) Children #"]
                                         .iloc[0])) + 10


canis_data_js = ColumnDataSource(canis_data)
div = Div(width=500)

# Create Holoviews graph and add URLs as hover information
hv_graph = hv.Graph.from_networkx(G, net_layout)

hovertool = HoverTool(tooltips=[('Name', '@name'), ('Twitter URL', '@url')])

# Customization to the graph
hv_graph.opts(
    directed=True, 
    bgcolor="#222222",
    xaxis=None, 
    yaxis=None,
    node_fill_color='color', 
    node_size='size',
    edge_line_color='#FFFFEE', 
    edge_line_width=1, 
    arrowhead_length=0.0001,
    width=1024, 
    height=900, 
    node_nonselection_fill_color='black',
    tools=[hovertool],
)

# Render the plot
labelled_graph = (hv_graph * labels).opts(opts.Labels(text_font_size='10pt', visible=False))

# Convert to Bokeh plot
plot = hv.render(labelled_graph)

# Label Callback
label_callback = CustomJS(args=dict(labels=plot.renderers[-1]), code=f"""
    // Determine the zoom level and adjust label visibility
    labels.visible = !labels.visible;
""")




plot.add_tools(TapTool(callback=OpenURL(url='@url'))) 
plot.js_on_event(DoubleTap, label_callback)
# plot.js_on_event(Tap, div_callback)


show_layout = row(plot, div)

# Display the plot
curdoc().add_root(show_layout)

