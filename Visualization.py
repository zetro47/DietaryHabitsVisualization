import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output
import geopandas as gpd
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import make_axes_locatable



grouped_df = pd.read_excel("main_data_counts.xlsx")
pivoted_data = grouped_df.pivot(index='age_group', columns='diet_group', values='n_participants_proportioned').reset_index()
stacked_bar_fig = px.bar(
    pivoted_data,
    x='age_group',
    y=[col for col in pivoted_data.columns if col != 'age_group'],
    labels={'value': 'Proportion of Participants', 'age_group': 'Age Group'},
    barmode='stack'
)
stacked_bar_fig.update_layout(
    plot_bgcolor='rgba(0, 0, 0, 0)',
    paper_bgcolor='rgba(0, 0, 0, 0)', margin=dict(t=25, b=0, l=10, r=10)
)


supple_agg_df = pd.read_excel('supple_agg_df_water.xlsx')
dietary_data_df = pd.read_excel('dietary_data_proportioned.xlsx')
supple_agg_df.dropna(inplace=True)

def calculate_water_use(selected_age_category):
    mapping = {
    'Grains': ['Barley (Beer)', 'Beet Sugar', 'Maize (Meal)', 'Oatmeal', 'Rice', 'Wheat & Rye (Bread)'],
    'Potatoes': ['Potatoes'],
    'Beans': ['Groundnuts', 'Other Pulses', 'Peas', 'Soybean Oil'],
    'Fruit': ['Apples', 'Bananas', 'Berries & Grapes', 'Citrus Fruit', 'Other Fruit', 'Tomatoes'],
    'Meat': ['Bovine Meat (beef herd)', 'Bovine Meat (dairy herd)', 'Lamb & Mutton', 'Pig Meat', 'Poultry Meat'],
    'Fish': ['Crustaceans (farmed)', 'Fish (farmed)'],
    'Cheese': ['Cheese'],
    'Milk': ['Milk'],
    'Yogurt': ['Soymilk', 'Tofu']
    }

    main_data_counts_df = pd.read_excel('main_data_counts.xlsx')

    diet_group_name_mappings = {'fish': 'Fish-eaters', 'veggie': 'Vegetarians', 'vegan': 'Vegans', 'meat': 'Low meat-eaters', 'meat50': 'Medium meat-eaters', 'meat100': 'High meat-eaters'}
    main_data_counts_df = main_data_counts_df[main_data_counts_df['age_group'] == selected_age_category]

    proportions_by_age = []

    for index, row in main_data_counts_df.iterrows():
        proportions = dietary_data_df[dietary_data_df['Diet'] == diet_group_name_mappings[row['diet_group']]]
        proportions_by_age.append(proportions[mapping.keys()] * row['n_participants_proportioned'])

    proportions_by_age = pd.concat(proportions_by_age, ignore_index=True).sum()
        
    supple_agg_df['ProportionatedLandUseByDietType'] = supple_agg_df.apply(
        lambda row: row['Water Use (L)'] * (proportions_by_age[row['Category']]), axis=1
    )
    land_use_summed = supple_agg_df.groupby('Country')['ProportionatedLandUseByDietType'].sum().reset_index()
    return land_use_summed

world = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres'))

def create_choropleth(selected_age_category):
    land_use_summed = calculate_water_use(selected_age_category)
    merged_data = world.merge(land_use_summed, left_on='name', right_on='Country', how='left')
    merged_data['ProportionatedLandUseByDietType'].fillna(0, inplace=True)
    merged_data['BubbleSize'] = merged_data['ProportionatedLandUseByDietType'] * 100
    choropleth_fig = px.choropleth(
        merged_data,
        locations='iso_a3',
        color='ProportionatedLandUseByDietType',
        hover_name='name',
        color_continuous_scale='Brwnyl',
        range_color=(0, 10000),
        labels={'ProportionatedLandUseByDietType': ''}
    )
    choropleth_fig.update_layout(
    plot_bgcolor='rgba(0, 0, 0, 0)',
    paper_bgcolor='rgba(0, 0, 0, 0)', margin=dict(t=10, b=10, l=10, r=10)
    )
    return choropleth_fig


file_path = 'Combined_Parth.xlsx'
df_dict = pd.read_excel(file_path, sheet_name=None)

sheet_names = list(df_dict.keys())

for name, df in df_dict.items():
    print(f"Sheet: {name}\nColumns: {df.columns}\n")

def create_spider_chart(selected_sheet):
    df = df_dict[selected_sheet]
    print(df)
    categories = df.columns[1:].tolist() 
    categories_with_loop = categories + [categories[0]]  # Append the first element to close the loop

    fig = go.Figure()
    for i, row in df.iterrows():
        values = row[1:].tolist()  
        values_with_loop = values + [values[0]]  # Append the first element to close the loop

        fig.add_trace(go.Scatterpolar(
            r=values_with_loop,
            theta=categories_with_loop,
            name=row['age_group'],
            line=dict(width=2),
        ))
    fig.update_layout(
            polar=dict(
                radialaxis=dict(visible=True, range=[0, df.iloc[:, 1:].max().max()])
            ),
            showlegend=True, plot_bgcolor='rgba(0, 0, 0, 0)',
            paper_bgcolor='rgba(0, 0, 0, 0)',
            margin=dict(t=20, b=20, l=10, r=10),
            
    )

    return fig


app = Dash(__name__)

app.layout = html.Div(style={'backgroundColor': '#faeceb'}, children=[
html.Div([
    html.H4("Standard Deviation of environmental metrics w.r.t. diet type and age category (select mertric from dropdown)", style={'text-align': 'left', 'padding-left': '10px', 'padding-right': '10px'}),
    dcc.Dropdown(
        id='sheet-dropdown',
        options=[{'label': sheet, 'value': sheet} for sheet in sheet_names],
        value=sheet_names[0], style={'width': '55%', 'padding-left': '10px',}
    ),
    dcc.Graph(id='spider-chart', config={'displayModeBar': False})
], style={'width': '50%', 'height': '100%', 'float': 'left', 'background-color': '#e3fdff'}),
    html.Div([
        html.H4("Proportion of diet groups for each age group", style={'text-align': 'left', 'padding-left': '10px', 'padding-right': '10px'}),
        dcc.Graph(id='stacked-bar-chart', figure=stacked_bar_fig, style={'padding-left': '10px',}, config={'displayModeBar': False})
    ], style={'width': '50%', 'height': '100%', 'float': 'right', 'background-color': '#faeceb', }),

    html.Div([
        html.H4("Mean water use for production of food items in various countries, based on age groups of British consumers", style={'text-align': 'left', 'padding-left': '10px', 'padding-right': '10px'}),
        dcc.Dropdown(
            id='diet-category-dropdown',
            options=['20-29', '30-39', '40-49', '50-59', '60-69', '70-79'],
            value="20-29", style={'width': '35%', 'padding-left': '10px',}
        ),
        dcc.Graph(id='choropleth-chart', config={'displayModeBar': False})
    ], style={'width': '100%', 'display': 'inline-block', 'background-color': '#fffae3'})
])



@app.callback(
    Output('choropleth-chart', 'figure'),
    [Input('diet-category-dropdown', 'value')]
)
def update_choropleth(selected_diet_category):
    return create_choropleth(selected_diet_category)

@app.callback(
    Output('spider-chart', 'figure'),
    [Input('sheet-dropdown', 'value')]
)
def update_spider_chart(selected_sheet):
    return create_spider_chart(selected_sheet)


if __name__ == '__main__':
    app.run_server(debug=False, port = 9899)
