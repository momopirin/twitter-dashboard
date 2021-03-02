import dash

# import utils

from layout import layout
from callbacks import register_callbacks

app = dash.Dash(__name__)

app.layout = layout
register_callbacks(app)

if __name__ == "__main__":
    app.run_server(debug=True)