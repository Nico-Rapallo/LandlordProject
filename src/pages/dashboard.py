import dash
from dash import Dash, dcc, html, Input, Output, callback, State, callback_context
import os
from src.Landlord import Landlord_DB 
db = Landlord_DB()


def run_app() -> None:
    assets_path = os.path.join(os.getcwd(), 'src')
    app = Dash(__name__,
                assets_folder=assets_path,
                assets_url_path='')
    
    app.title = 'Williamsburg Landlord Dashboard'
    create_layout(app)
    app.run(debug=True)
    return None

def create_layout(app: Dash) -> None:
    app.layout = html.Div([
            html.H1('Williamsburg Landlord Dashboard Address Lookup'),
            html.Hr(),

            html.Div([
                html.Label("Enter Address"),
                dcc.Dropdown(
                    id='address-dd',
                    options=[''] + db.get_address_list(),
                    value='',
                    placeholder='Enter Address…',
                    style={'flex': '1'}               
                ),
                html.Button(
                    'I live here!',
                    id='form-button',
                    style={'flex': '0 0 auto'}    
                ),
            ], style={'width': '100%', 'display': 'flex', 'gap': '10px'}),

        html.Div(
            children=[
                html.Div(
                    html.Img(
                        id='property-image',
                        src='',
                        style={'width':'100%','maxWidth':'100%','height':'auto'}
                    ),
                    style={'flex':'0 0 50%','paddingRight':'10px'}
                ),
                html.Div(
                    id='property-info',
                    children=[],
                    style={
                        'flex':'1',
                        'paddingLeft':'10px',
                        'borderLeft':'1px solid #ccc'
                    }
                ),
            ],
            id='property-display-container',
            style={'display':'flex','alignItems':'flex-start','marginTop':'20px'}
        ),

        html.Div(
            children=[
                html.H2('Leave Landlord Review'),
                html.Hr(),
                html.Div([
                    html.Label("What is your landlord's name? (Who do you pay rent to?)"),
                    dcc.Input(id='landlord-name', type='text', placeholder='Enter text...', style={'width': '100%'}),
                    html.Label('Landlord Star Rating'),
                    dcc.Dropdown(id='landlord-stars', options=[{'label': opt, 'value': opt} for opt in ['1','2','3', '4', '5']], value=None),
                    html.Label('Landlord Review'),
                    dcc.Input(id='landlord-review', type='text', placeholder='Enter text...', style={'width': '100%'}),
                    html.Label('Property Star Rating'),
                    dcc.Dropdown(id='property-stars', options=[{'label': opt, 'value': opt} for opt in ['1','2','3', '4', '5']], value=None),
                    html.Label('Property Review'),
                    dcc.Input(id='property-review', type='text', placeholder='Enter text...', style={'width': '100%'}),
                    html.Label('Individual Rent Range'),
                    dcc.Dropdown(id='ind-rent', options=[{'label': opt, 'value': opt} for opt in ['<500',
                                                                                                   '500-1,000',
                                                                                                   '1,000-1,500', 
                                                                                                   '1,500-2,000', 
                                                                                                   '2,000-2,500',
                                                                                                   '>2,500']], value=None),
                    html.Label('Total Rent Range (including roommates)'),
                    dcc.Dropdown(id='total-rent', options=[{'label': opt, 'value': opt} for opt in ['<500',
                                                                                                   '500-1,500',
                                                                                                   '1,500-2,500', 
                                                                                                   '2,500-3,500', 
                                                                                                   '3,500-4,500',
                                                                                                    '4,500-5,500',
                                                                                                  '>5,500'
                                                                                                   ]], value=None),
                    html.Label('Are Utilies included in rent?'),
                    dcc.Dropdown(id='utilies', options=[{'label': opt, 'value': opt} for opt in ['None',
                                                                                                   'Some',
                                                                                                   'All'
                                                                                                   ]], value=None),
                    html.Label('Do you have free parking?'),
                    dcc.Dropdown(id='parking', options=[{'label': opt, 'value': opt} for opt in ['No',
                                                                                                 'Yes'
                                                                                                 ]], value=None)
                ], style={'display':'grid','gridTemplateColumns':'1fr 1fr','gap':'20px'}),

            html.Div([
                html.Button('Back', id='back-button', n_clicks=0, style={'marginRight':'10px'}),
                html.Button('Submit Review', id='submit-button', n_clicks=0, disabled=True)
            ], style={'marginTop':'20px'}),

            html.Div(
                "Thank you! Your review has been submitted.",
                id='submit-confirmation',
                style={'display':'none','marginTop':'10px','color':'green'}
            )
        ], id='user-input-container', style={'display':'none','marginTop':'20px'}),

    ], style={'padding':'20px'})


@callback(
    Output('property-image', 'src'),
    Output('property-info', 'children'),
    Input('address-dd', 'value')
)
def update_property_display(address: str):
    if not address:
        return '', []
    pid = db.get_pid_from_address_display(address)
    img_path = db.get_property_image(pid)

    (owner, beds, half_baths, full_baths, units) = db.get_property_details(pid)
    landlord_rating = db.get_avg_landlord_rating(pid)
    property_rating = db.get_avg_property_rating(pid)

    info_children = [
        html.H4("Property Details", style={'marginBottom': '10px'}),
        html.P(f"Owner: {owner}"),
        html.P(f"Owner Rating: {landlord_rating}/5"),
        html.P(f"Property Rating: {property_rating}/5"),
        html.P(f"Bedrooms: {beds}"),
        html.P(f"Half Baths: {half_baths}"),
        html.P(f"Full Baths: {full_baths}"),
        html.P(f"Rental Units: {units}")
    ]
    return img_path, info_children

@callback(
    Output('property-display-container', 'style'),
    Output('user-input-container', 'style'),
    Input('form-button', 'n_clicks'),
    Input('back-button', 'n_clicks'),
    State('address-dd', 'value'),
    prevent_initial_call=True
)
def swap_views(live_clicks, back_clicks, address):
    triggered_id = callback_context.triggered[0]['prop_id'].split('.')[0]
    
    if triggered_id == 'form-button' and address:
        return {'display':'none'}, {'display':'block','marginTop':'20px'}

    if triggered_id == 'back-button':
        return {'display':'flex','alignItems':'flex-start','marginTop':'20px'}, {'display':'none'}
    
    return dash.no_update, dash.no_update

@callback(
    Output('submit-button', 'disabled'),
    Input('landlord-name', 'value'),
    Input('landlord-stars', 'value'),
    Input('landlord-review', 'value'),
    Input('property-stars', 'value'),
    Input('property-review', 'value'),
    Input('ind-rent', 'value'),
    Input('total-rent', 'value'),
    Input('utilies', 'value'),
    Input('parking', 'value'),
)
def toggle_submit_button(ln, ls, lr, ps, pr, ir, tr, ut, pa):
    all_filled = all([ln, ls, lr, ps, pr, ir, tr, ut, pa])
    return not all_filled


@callback(
    Output('submit-button', 'style'),
    Output('submit-confirmation', 'style'),
    Input('submit-button', 'n_clicks'),
    State('address-dd', 'value'),
    State('landlord-name', 'value'),
    State('landlord-stars', 'value'),
    State('landlord-review', 'value'),
    State('property-stars', 'value'),
    State('property-review', 'value'),
    State('ind-rent', 'value'),
    State('total-rent', 'value'),
    State('utilies', 'value'),
    State('parking', 'value'),
    prevent_initial_call=True
)
def submit_review(n_clicks, 
                  address, property_stars, property_review,
                  landlord_name, landlord_stars, landlord_review,
                  total_rent, ind_rent, 
                  utilities, parking):
    if not n_clicks:
        return dash.no_update, dash.no_update

    db.insert_response(
        address,
        property_stars,
        property_review,
        landlord_name, 
        landlord_stars,
        landlord_review,
        total_rent,
        ind_rent,
        utilities,
        parking
    )

    hide_btn = {'display': 'none'}
    show_conf = {'display': 'block', 'marginTop': '10px', 'color': 'green'}
    return hide_btn, show_conf