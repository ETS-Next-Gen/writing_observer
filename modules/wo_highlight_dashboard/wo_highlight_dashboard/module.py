import learning_observer.downloads as d
from learning_observer.dash_integration import thirdparty_url, static_url

import wo_highlight_dashboard.dashboard.layout

NAME = "Writing Observer - Text Metric & Highlight Dashboard"

DASH_PAGES = [
    {
        "MODULE": wo_highlight_dashboard.dashboard.layout,
        "LAYOUT": wo_highlight_dashboard.dashboard.layout.layout,
        "ASSETS": 'assets',
        "TITLE": "Metric & Highlight Dashboard",
        "DESCRIPTION": "The Metric and Highlight dashboard provides in-depth natural language processing on student essays.",
        "SUBPATH": "dashboard",
        "CSS": [
            thirdparty_url("css/bootstrap.min.css"),
            thirdparty_url("css/fontawesome_all.css")
        ],
        "SCRIPTS": [
            static_url("liblo.js")
        ]
    }
]

# Third party module tests with helpful messages.
Minty_URL = 'https://cdn.jsdelivr.net/npm/bootswatch@5.1.3/dist/minty/bootstrap.min.css'
if (dbc.themes.MINTY != Minty_URL):
    print("WARN:: Unrecognized Minty URL detected: {}".format(dbc.themes.MINTY))
    print("You will need to update dash bootstrap components hash value.\n")
    
FontAwesome_URL = "https://use.fontawesome.com/releases/v6.3.0/css/all.css"
if (dbc.icons.FONT_AWESOME != FontAwesome_URL):
    print("WARN:: Unrecognized Fontawesome URL detected: {}".format(dbc.icons.FONT_AWESOME))
    print("You will need to update the FontAwesome bootstrap components hash value.\n")


THIRD_PARTY = {
    "css/bootstrap.min.css": d.BOOTSTRAP_MIN_CSS,
    "css/fontawesome_all.css": d.FONTAWESOME_CSS,
    "webfonts/fa-solid-900.woff2": d.FONTAWESOME_WOFF2,
    "webfonts/fa-solid-900.ttf": d.FONTAWESOME_TTF
}

COURSE_DASHBOARDS = [{
    'name': NAME,
    'url': "/wo_highlight_dashboard/dash/dashboard/",
    "icon": {
        "type": "fas",
        "icon": "fa-pen-nib"
    }
}]
