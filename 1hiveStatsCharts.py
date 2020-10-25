import requests
import json
import pandas as pd
import datetime
import math
import dash
import dash_core_components as dcc
import dash_html_components as html


external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server


def truncate(number, decimals=0):
    """
    Returns a value truncated to a specific number of decimal places.
    """
    if not isinstance(decimals, int):
        raise TypeError("decimal places must be an integer.")
    elif decimals < 0:
        raise ValueError("decimal places has to be 0 or more.")
    elif decimals == 0:
        return math.trunc(number)

    factor = 10.0 ** decimals
    return math.trunc(number * factor) / factor


# ----------------------------- Load output json --------------------------


url = 'https://raw.githubusercontent.com/1Hive/pollen/gh-pages/output/credResult.json'
r = requests.get(url)
cred = json.loads(r.text)

# with open('credResult.json', 'r') as f:
#  cred = json.load(f)

# -------------------------- Set dates time-filtering ------------------------

# start_date = '2018/11/10 18:56:36'
start_date = '2020/10/01 00:00:00'
end_date = '2020/10/18 00:00:00'

start_datetime = datetime.datetime.strptime(start_date, '%Y/%m/%d %H:%M:%S')
end_datetime = datetime.datetime.strptime(end_date, '%Y/%m/%d %H:%M:%S')

num_nodes = len(cred[1]['credData']['nodeSummaries'])
nodes = []

for i in range(num_nodes):

    # if (cred[1]['weightedGraph'][1]['graphJSON'][1]['sortedNodeAddresses'][i][1] == 'discourse'):
    node = {}
    node['address'] = cred[1]['weightedGraph'][1]['graphJSON'][1]['sortedNodeAddresses'][i]
    node['cred'] = cred[1]['credData']['nodeSummaries'][i]['cred']
    if cred[1]['credData']['nodeOverTime'][i] is None:
        node['credOverTime'] = []
    else:
        node['credOverTime'] = cred[1]['credData']['nodeOverTime'][i]['cred']

    node['description'] = cred[1]['weightedGraph'][1]['graphJSON'][1]['nodes'][i]['description']
    node['timestamp'] = cred[1]['weightedGraph'][1]['graphJSON'][1]['nodes'][i]['timestampMs']
    node['user'] = ''

    if (node['address'][2] == 'IDENTITY'):
        node['user'] = cred[1]['weightedGraph'][1]['graphJSON'][1]['nodes'][i]['description']

    nodes.append(node)

# --------- ----------------- filter nodes by type --------------------------


nodes_filt = [node for node in nodes if (node['address'][2] == 'post')]
# nodes_filt = [ node for node in cred[1]["orderedNodes"] if (node['address'][2] == 'topic' )] # Filter by topic
# nodes_filt = [ node for node in cred[1]["orderedNodes"] if (node['address'][2] == 'topic' or node['address'][2]== 'post') ] # Filter by topic AND post
# nodes_filt = cred[1]["orderedNodes"]  # No filter (pass through..)

# --------------------------- filter nodes by dateTime --------------------------

nodes_time_filt = [node for node in nodes_filt if (datetime.datetime.fromtimestamp(node['timestamp'] / 1000) >= \
                                                   start_datetime and datetime.datetime.fromtimestamp(
            node['timestamp'] / 1000) <= end_datetime)]

# ------------------------- Crop by top users Cred over time --------------------

# filter user nodes
nodes_filt = [node for node in nodes if (node['address'][2] == 'IDENTITY')]
span = 8
num_display = 100

nodes_sorted5 = sorted(nodes_filt, key=lambda e: sum(e['credOverTime'][-span:-1]), reverse=True)

top_nodes = nodes_sorted5[:num_display]

# ------------------------- Create pandas dataframes --------------------


df2 = pd.DataFrame(top_nodes, columns=['user', 'cred', 'credOverTime'])

df3 = pd.DataFrame(df2.credOverTime.tolist(), index=df2.index)
df4 = pd.concat([df2['user'], df2['cred'], df3], axis=1, sort=False)

# add extra colum with user name for sorting
df4['User.Upper'] = df4['user'].str.upper()
df4.sort_values(by='User.Upper', inplace=True)

df5 = df4.copy()
df5.sort_values(by='cred', inplace=True, ascending=False)


# ------------------------- Dash layout -----------------------

app.layout = html.Div(children=[
    html.H3(children='1hive Cred Stats'),

    html.Div(children='Data extracted from Github Pollen repo.'),

    dcc.Graph(id='graph1',
        figure={
            'data': [
            {'x': df4['user'], 'y': df4['cred'], 'type': 'bar', 'name': 'Cred'}
            ],
            'layout': {
                'title': '1hive Top 100 Accounts - Sorted Alphabetically',
                'font' : {
                    'size': '46px',
                }

            }
        }
    ),


    dcc.Graph(id='graph2',
        figure={
            'data': [
            {'x': df5['user'], 'y': df5['cred'], 'type': 'bar', 'name': 'Cred'}
            ],
            'layout': {
                'title': '1hive Top 100 Accounts - Sorted by Pollen',
                'font' : {
                    'size': '46px',
                }

            }
        }
    )


])

if __name__ == '__main__':
    app.run_server(host='127.0.0.1', port='8050', debug=True)
