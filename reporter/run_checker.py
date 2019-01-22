# -*- coding: utf-8 -*-
import os
import sys

import dash
import dash_auth
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import plotly.graph_objs as go
import plotly.figure_factory as ff
from dash.dependencies import Input, Output, State
import keys

import dash_scroll_up

import components.mongo_interface
import components.import_data as import_data


#Globals
COMPONENTS = ['whats_my_species', 'qcquickie',
              'analyzer', 'assemblatron', 'ssi_stamper', 'sp_cdiff_fbi', 'sp_ecoli_fbi', 'sp_salm_fbi']

app = dash.Dash()

app.config["suppress_callback_exceptions"] = True
app.title = "Serum QC Run Checker"

# Temp css to make it look nice
# Dash CSS
app.css.append_css(
    {"external_url": "https://codepen.io/chriddyp/pen/bWLwgP.css"})
# Lato font
app.css.append_css(
    {"external_url": "https://fonts.googleapis.com/css?family=Lato"})

run_list = import_data.get_run_list()
run_list_options = [
    {
        "label": "{} ({})".format(run["name"],
                                  len(run["samples"])),
        "value": run["name"]
    } for run in run_list]


app.layout = html.Div([
    html.Div(className="container", children=[
        dash_scroll_up.DashScrollUp(
            id="input",
            label="UP",
            className="button button-primary no-print"
        ),
        html.H1("SerumQC Run Checker"),
        dcc.Interval(
            id='table-interval',
            interval=30*1000,  # in milliseconds
            n_intervals=0),
        html.Div([
            html.Div(
                [
                    html.Div(
                        dcc.Dropdown(
                            id="run-list",
                            options=run_list_options,
                            placeholder="Sequencing run"
                        )
                    )
                ],
                className="nine columns"
            ),
            html.Div(
                [
                    dcc.Link(
                        "Load run",
                        id="run-link",
                        href="/",
                        className="button button-primary")
                ],
                className="three columns"
            )
        ], id="run-selector", className="row"),
        html.P("", id="run-name", style={"display": "none"}),
        html.H2("", id="run-name-title"),
        html.Div(id="report-link"),
        dcc.Location(id="url", refresh=False),
        html.P("The table will update every 30s automatically."),
        html.Div(id="run-report", className="run_checker_report")

    ]),
    html.Footer([
        "Created with 🔬 at SSI. Bacteria icons from ",
        html.A("Flaticon", href="https://www.flaticon.com/"),
        "."], className="footer container")
], className="appcontainer")


# Callbacks

# We could make this one much faster by hiding the unused species with CSS
# by adding a new hidden class.


@app.callback(
    Output("run-name", "children"),
    [Input("url", "pathname")]
)
def update_run_name(pathname):
    if pathname is None:
        pathname = "/"
    path = pathname.split("/")
    if len(path) > 2:
        print(path[2])
    if import_data.check_run_name(path[1]):
        name = path[1]
    elif path[1] == "":
        name = ""
    else:
        name = "Not found"
    if len(path) > 2:
        return name + "/" + path[2]
    else:
        return name + "/"


@app.callback(
    Output("run-name-title", "children"),
    [Input("run-name", "children")]
)
def update_run_title(run_name):
    return run_name.split("/")[0]


@app.callback(
    Output("report-link", "children"),
    [Input("run-name", "children")]
)
def update_run_name(run_name):
    run_name = run_name.split("/")[0]
    if run_name == "" or run_name == "Not found":
        return None
    else:
        return html.H3(html.A("Link to QC Report", href="{}/{}".format(keys.qc_report_url, run_name)))


@app.callback(
    Output("run-link", "href"),
    [Input("run-list", "value")]
)
def update_run_button(run):
    if run is not None:
        return "/" + run
    else:
        return "/"


@app.callback(
    Output("run-report", "children"),
    [Input("run-name", "children"),
     Input("table-interval", "n_intervals")]
)
def update_run_report(run, n_intervals):
    run = run.split("/")[0]
    report = "status"
    if run.split("/")[1] == "resequence":
        report = "resequence"
    data = []
    figure = {}
    if run != "" and report == "status":

        samples = import_data.get_sample_component_status(run)
        header = html.Tr([html.Th(html.Strong("Sample"))] +
                         list(map(lambda x: html.Th(html.Strong(x)), COMPONENTS)))
        rows = [header]

        for name, s_components in samples.items():
            row = []
            row.append(html.Td(name))
            for component in COMPONENTS:
                if component in s_components.keys():
                    s_c = s_components[component]
                    row.append(
                        html.Td(s_c[1], className="status-{}".format(s_c[0])))
                else:
                    row.append(html.Td("None", className="status-0"))
            rows.append(html.Tr(row))
        table = html.Table(rows)
        return [table]

    if run != "" and report == "resequence":

        samples = import_data.get_sample_QC_status(run)
        header = html.Tr([html.Th(html.Strong("Sample"))] +
                         list(map(lambda x: html.Th(html.Strong(x)), COMPONENTS)))
        rows = [header]

        for name, s_components in samples.items():
            row = []
            row.append(html.Td(name))
            for component in COMPONENTS:
                if component in s_components.keys():
                    s_c = s_components[component]
                    row.append(
                        html.Td(s_c[1], className="status-{}".format(s_c[0])))
                else:
                    row.append(html.Td("None", className="status-0"))
            rows.append(html.Tr(row))
        table = html.Table(rows)
        return [table]

    return []


server = app.server  # Required for gunicorn

#app.run_server(debug=True, host="0.0.0.0")
if __name__ == '__main__':
    # 0.0.0.0 exposes the app to the network.
    app.run_server(debug=True, host="0.0.0.0",
                   port=8051, dev_tools_hot_reload=True)
