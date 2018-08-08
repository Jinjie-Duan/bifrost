import dash_html_components as html
import dash_core_components as dcc
from components.images import list_of_images, get_species_color
from components.table import html_table, html_td_percentage
import plotly.graph_objs as go
import pandas as pd
import math

def check_test(test_name, sample):
    test_path = "testomatic." + test_name
    if test_path not in sample:
        return "" # show nothing
        #return "test-missing"
    if sample["testomatic." + test_name].startswith("pass"):
        return "test-pass"
    elif sample["testomatic." + test_name].startswith("fail"):
        return "test-fail"
    else:
        return "test-warning"

def generate_sample_report(dataframe, sample, data_content, plot_data):
    return (
        html.Div(
            [
                html.A(id="sample-" + sample["name"]),
                html.H5(
                    sample["name"],
                    className="box-title"
                ),
                html_sample_tables(sample, data_content, className="row"),

                graph_sample_depth_plot(
                    sample,
                    dataframe[dataframe["species"]
                              == sample["species"]],
                    plot_data
                ),
                html_test_table(sample, className="row")
            ],
            className="border-box"
        )
    )


def html_species_report(dataframe, species, data_content, species_plot_data, **kwargs):
    report = []
    for index, sample in \
      dataframe.loc[dataframe["species"] == species].iterrows():
        report.append(generate_sample_report(dataframe,
                                             sample,
                                             data_content,
                                             species_plot_data))
    return html.Div(report, **kwargs)


def html_organisms_table(sample_data, **kwargs):
    percentages = [
        sample_data.get("qcquickie.percent_classified_species_1", math.nan),
        sample_data.get("qcquickie.percent_classified_species_2", math.nan),
        sample_data.get("qcquickie.percent_unclassified", math.nan)
    ]

    color_1 = get_species_color(
        sample_data.get("qcquickie.name_classified_species_1"))  # Default
#    color_2 = COLOR_DICT.get(
#        sample_data["name_classified_species_2"], "#f3bbd3")  # Default
    color_2 = "#f3bbd3"  # Default

#   color_u = COLOR_DICT.get("", "#fee1cd")  # Default
    color_u = "#fee1cd"  # Default

    return html.Div([
        html.H6("Detected Organisms", className="table-header"),
        html.Table([
            html.Tr([
                html.Td(
                    html.I(sample_data.get("qcquickie.name_classified_species_1", "No data"))),
                html_td_percentage(percentages[0], color_1)
            ], className=check_test("qcquickie.minspecies", sample_data)),
            html.Tr([
                html.Td(
                    html.I(sample_data.get("qcquickie.name_classified_species_2", "No data"))),
                html_td_percentage(percentages[1], color_2)
            ]),
            html.Tr([
                html.Td("Unclassified"),
                html_td_percentage(percentages[2], color_u)
            ])
        ])
    ], **kwargs)

def html_test_table(sample_data, **kwargs):
    rows = []
    for key, value in sample_data.items():
        if key.startswith("testomatic"):
            rows.append([key.split(".")[-1], value])
    return html.Div(html_table(rows, className="six columns"), **kwargs)

def html_sample_tables(sample_data, data_content, **kwargs):
    """Generate the tables for each sample containing submitter information,
       detected organisms etc. """
    genus = str(sample_data.get(["qcquickie.name_classified_species_1"])).split()[
        0].lower()
    if "{}.svg".format(genus) in list_of_images:
        img = html.Img(
            src="/static/" + genus + ".svg",
            className="svg_bact"
        )
    else:
        img = []
    if "sample_sheet.sample_name" in sample_data:
        if "sample_sheet.emails" in sample_data and type(sample_data["sample_sheet.emails"]) is str:
            n_emails = len(sample_data["sample_sheet.emails"].split(";"))
            if (n_emails > 1):
                emails = ", ".join(
                    sample_data["sample_sheet.emails"].split(";")[:2])
                if (n_emails > 2):
                    emails += ", ..."
            else:
                emails = sample_data["sample_sheet.emails"]
        else:
            emails = ""
        sample_sheet_div = [
            html.H5("Sample Sheet", className="table-header"),
            html.Div([
                html.Div([
                    html_table([
                        ["Supplied name", sample_data["sample_sheet.sample_name"]],
                        ["Supplying lab", sample_data["sample_sheet.group"]],
                        ["Submitter emails", emails],
                        {
                            "list": ["Provided species", html.I(
                                sample_data["sample_sheet.provided_species"])],
                            "className": check_test("qcquickie.submitted==detected", sample_data)
                        }
                    ])
                ], className="six columns"),
                html.Div([
                    html.H6("User Comments", className="table-header"),
                    sample_data["sample_sheet.Comments"]
                ], className="six columns"),
            ], className="row"),
        ]
    else:
        sample_sheet_div = []

    if data_content == "qcquickie":
        title = "QCQuickie Results"
        report = [
            html.Div([
                html_table([
                    [
                        "Number of contigs",
                        "{:,}".format(
                            sample_data.get("qcquickie.bin_contigs_at_1x", math.nan))
                    ],
                    [
                        "N50",
                        "{:,}".format(
                            sample_data.get("qcquickie.N50", math.nan))
                    ],
                    {
                        "list": [
                            "bin length at 1x depth",
                            "{:,}".format(
                                sample_data.get("qcquickie.bin_length_at_1x", math.nan))
                        ],
                        "className": check_test("qcquickie.1xgenomesize", sample_data)
                    },
                    [
                        "bin length at 25x depth",
                        "{:,}".format(
                            sample_data.get("qcquickie.bin_length_at_25x", math.nan))
                    ],
                    {
                        "list": [
                            "bin length 1x - 25x diff",
                            "{:,}".format(
                                sample_data.get("qcquickie.bin_length_at_1x", math.nan) \
                                - sample_data.get("qcquickie.bin_length_at_25x", math.nan)
                                )
                        ],
                        "className": check_test("qcquickie.1x25xsizediff", sample_data)
                    }
                ])
            ], className="six columns"),
            html_organisms_table(sample_data, className="six columns")
        ]
    elif data_content == "assemblatron":
        title = "Assemblatron Results"
        report = [
            html.Div([
                html_table([
                    [
                        "Number of contigs",
                        "{:,}".format(
                            sample_data.get("assemblatron.bin_contigs_at_1x", math.nan))
                    ],
                    [
                        "N50",
                        "{:,}".format(sample_data.get("assemblatron.N50", math.nan))
                    ],
                    [
                        "bin length at 1x depth",
                        "{:,}".format(
                            sample_data.get("assemblatron.bin_length_at_1x", math.nan))
                    ],
                    [
                        "bin length at 10x depth",
                        "{:,}".format(
                            sample_data.get("assemblatron.bin_length_at_10x", math.nan))
                    ],
                    [
                        "bin length at 25x depth",
                        "{:,}".format(
                            sample_data.get("assemblatron.bin_length_at_25x", math.nan))
                    ]
                ])
            ], className="six columns"),
            html_organisms_table(sample_data, className="six columns")
        ]
    else:
        title = "No report selected"
        report = []

    return html.Div([
        html.Div(img, className="bact_div"),
        html.Div(sample_sheet_div),
        html.H5(title, className="table-header"),
        html.Div(report, className="row")
    ], **kwargs)


def graph_sample_depth_plot(sample, run_species, background):
    # With real data, we should be getting sample data (where to put 1, 10
    # and 25x annotation) and the info for the rest of that species box.
    return dcc.Graph(
        id="coverage-1-" + sample["name"],
        figure={
            "data": [
                go.Box(
                    x=run_species["qcquickie.bin_length_at_1x"],
                    text=run_species["name"],
                    name="Current run",
                    showlegend=False,
                    boxpoints="all",
                    pointpos=-1.8,
                    jitter=0.3,
                    marker=dict(
                        size=4,
                        color=get_species_color(
                            sample["qcquickie.name_classified_species_1"])
                    )
                ),
                go.Box(
                    x=background,
                    # boxpoints="all",
                    showlegend=False,
                    name="Prev. runs",
                    jitter=0.3,
                    pointpos=-1.8,
                    marker=dict(
                        color="black",
                        size=4
                    )
                )
            ],
            "layout": go.Layout(
                title="{}: Binned Depth 1x size".format(sample["name"]),
                hovermode="closest",
                margin=go.Margin(
                    l=75,
                    r=50,
                    b=25,
                    t=50
                ),
                annotations=go.Annotations([
                    go.Annotation(
                        x=sample["qcquickie.bin_length_at_1x"],
                        y=0,
                        text="1x",
                        showarrow=True,
                        ax=35,
                        ay=0
                    ),
                    go.Annotation(
                        x=sample["qcquickie.bin_length_at_10x"],
                        y=0.0,
                        text="10x",
                        showarrow=True,
                        ax=0,
                        ay=35
                    ),
                    go.Annotation(
                        x=sample["qcquickie.bin_length_at_25x"],
                        y=0,
                        text="25x",
                        showarrow=True,
                        ax=-35,
                        ay=0
                    ),
                ])
            )
        },
        style={"height": "200px"}
    )

def graph_sample_cov_plot(sample, sample_coverage):
    df = pd.DataFrame.from_dict(sample_coverage, orient="index")
    return dcc.Graph(
        id="something" + sample["name"],
        figure={
            "data": [
                go.Scatter(
                    x= df.total_length,
                    y= df.coverage,
                    text= df.index,
                    mode= "markers"
                )
            ],
            "layout": go.Layout(
                title="{}: Binned Depth 1x size".format("something"),
                xaxis=dict(
                    type="log",
                    autorange=True
                ),
                yaxis=dict(
                    type="log",
                    autorange=True
                )
            )
        },
    )


def children_sample_list_report(filtered_df, data_content, plot_data):
    report = []
    for species in filtered_df["species"].unique():
        report.append(html.Div([
            html.A(id="species-cat-" + str(species).replace(" ", "-")),
            html.H4(html.I(str(species))),
            
            html_species_report(filtered_df, species, data_content, plot_data.get(species,[]))
        ]))
    return report


