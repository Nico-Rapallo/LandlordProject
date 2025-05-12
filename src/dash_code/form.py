import dash
from dash import Dash, dcc, html, Input, Output, callback
dash.register_page(__name__)

def layout():
    # 5 dropdowns, 2 text boxes, 1 numeric input (total 8 inputs)
    return html.Div([
        html.H2('Leave Landlord Review'),
        html.Hr(),
        html.Div([
            html.Div([
                html.Label('Dropdown 1'),
                dcc.Dropdown(id='dd-1', options=[{'label': opt, 'value': opt} for opt in ['A','B','C']], value=None),
                html.Label('Dropdown 2'),
                dcc.Dropdown(id='dd-2', options=[{'label': opt, 'value': opt} for opt in ['X','Y','Z']], value=None),
                html.Label('Dropdown 3'),
                dcc.Dropdown(id='dd-3', options=[{'label': str(i), 'value': i} for i in range(1,6)], value=None),
                html.Label('Dropdown 4'),
                dcc.Dropdown(id='dd-4', options=[{'label': day, 'value': day} for day in ['Mon','Tue','Wed']], value=None),
                html.Label('Dropdown 5'),
                dcc.Dropdown(id='dd-5', options=[{'label': lvl, 'value': lvl} for lvl in ['Low','Medium','High']], value=None),
            ], style={'display': 'grid', 'gridTemplateColumns': '1fr 1fr', 'gap': '20px'}),
            html.Div([
                html.Label('Text Input 1'),
                dcc.Input(id='text-1', type='text', placeholder='Enter text...', style={'width': '100%'}),
                html.Label('Text Input 2'),
                dcc.Textarea(id='text-2', placeholder='Enter longer text...', style={'width': '100%'}),
                html.Label('Numeric Input'),
                dcc.Input(id='num-1', type='number', placeholder='Enter number', style={'width': '100%'}),
            ], style={'marginTop': '20px'})
        ], style={'padding': '20px'})
    ])