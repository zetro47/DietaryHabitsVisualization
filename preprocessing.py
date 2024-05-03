import pandas as pd
import plotly.express as px

df = pd.read_csv('data.csv')

metrics = ['mean_bio', 'mean_land', 'mean_watuse', 'mean_eut', 'mean_ghgs']

for metric in metrics:
    grouped_data = df.groupby(['diet_group', 'age_group'])[metric].std().reset_index()

    grouped_data = grouped_data.pivot(index=['age_group'], columns='diet_group', values=metric)
    print(grouped_data)
    grouped_data.to_excel("Parth_{0}.xlsx".format(metric))


file_paths = ["parth_{0}.xlsx".format(m) for m in metrics] 
sheet_names = metrics  # Corresponding sheet names

output_file = 'Combined_Parth.xlsx'
with pd.ExcelWriter(output_file) as writer:
    for path, sheet_name in zip(file_paths, sheet_names):
        df = pd.read_excel(path)

        df.to_excel(writer, sheet_name=sheet_name, index=False)



import pandas as pd
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output

# Load the file and read all sheets
file_path = 'Combined_Parth.xlsx'
df_dict = pd.read_excel(file_path, sheet_name=None)

# Extract sheet names
sheet_names = list(df_dict.keys())

# Check the structure of each sheet
for name, df in df_dict.items():
    print(f"Sheet: {name}\nColumns: {df.columns}\n")

def create_spider_chart(selected_sheet):
    df = df_dict[selected_sheet]
    print(df)
    categories = df.columns[1:].tolist()  # Exclude 'sex' (index 0)
    categories_with_loop = categories + [categories[0]]  # Append the first element to close the loop

    fig = go.Figure()
    for i, row in df.iterrows():
        values = row[1:].tolist()  # Exclude 'sex'
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
            margin=dict(t=20, b=20, l=10, r=10)
    )

    return fig

def create_sunburst_chart(selected_sheet):
    df = df_dict[selected_sheet]  # Retrieve sheet directly

    df = df.melt(id_vars=['age_group'], var_name='diet_type', value_name='value')

    # Sunburst setup
    fig = px.sunburst(
        df, path=[ 'diet_type', 'age_group'], values='value',
        color='diet_type', color_discrete_sequence=px.colors.qualitative.Pastel
    )

    return fig

# Create the Dash app
app = Dash(__name__)

# Define layout
app.layout = html.Div([
    dcc.Dropdown(
        id='sheet-dropdown',
        options=[{'label': sheet, 'value': sheet} for sheet in sheet_names],
        value=sheet_names[0],
    ),
    dcc.Graph(id='spider-chart')
])

@app.callback(
    Output('spider-chart', 'figure'),
    [Input('sheet-dropdown', 'value')]
)
def update_spider_chart(selected_sheet):
    return create_spider_chart(selected_sheet)

# Run directly
if __name__ == '__main__':
    app.run_server(debug=True, port=8060)

