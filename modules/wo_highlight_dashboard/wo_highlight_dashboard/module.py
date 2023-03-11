import os.path

import dash_bootstrap_components as dbc

from learning_observer.dash_integration import thirdparty_url, static_url

import wo_highlight_dashboard.dashboard.layout

NAME = "Dash Writing Observer Dashboard"

DASH_PAGES = [
    {
        "MODULE": wo_highlight_dashboard.dashboard.layout,
        "LAYOUT": wo_highlight_dashboard.dashboard.layout.layout,
        "ASSETS": 'assets',
        "TITLE": "Writing Observer Dashboard",
        "DESCRIPTION": "Dashboard for the Writing Observer built with dash",
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
    "css/bootstrap.min.css": {
        "url": dbc.themes.MINTY,
        "hash": "c03f5bfd8deb11ad6cec84a6201f4327f28a640e693e56466fd80d983ed54"
        "16deff1548a0f6bbad013ec278b9750d1d253bd9c5bd1f53c85fcd62adba5eedc59"
    },
    "css/fontawesome_all.css": {
        "url": dbc.icons.FONT_AWESOME,
        "hash": "1496214e7421773324f4b332127ea77bec822fc6739292ebb19c6abcc22a5"
        "6248e0634b4e0ca0c2fcac14dc10b8d01fa17febaa35f46731201d1ffd0ab482dd7"
    },
    "webfonts/fa-solid-900.woff2": {
        "url": os.path.dirname(os.path.dirname(dbc.icons.FONT_AWESOME)) + "/webfonts/fa-solid-900.woff2",
        "hash": "d50c68cd4b3312f50deb66ac8ab5c37b2d4161f4e00ea077326ae76769dac"
        "650dd19e65dee8d698ba2f86a69537f38cf4010ff45227211cee8b382d9b567257a"
    },
    "webfonts/fa-solid-900.ttf": {
        "url": os.path.dirname(os.path.dirname(dbc.icons.FONT_AWESOME)) + "/webfonts/fa-solid-900.ttf",
        "hash": "5a2c2b010a2496e4ed832ede8620f3bbfa9374778f3d63e45a4aab041e174"
        "dafd9fffd3229b8b36f259cf2ef46ae7bf5cb041e280f2939884652788fc1e8ce58"
    }
}

COURSE_DASHBOARDS = [{
    'name': "Dash Writing Observer",
    'url': "/wo_highlight_dashboard/dash/dashboard/",
    "icon": {
        "type": "fas",
        "icon": "fa-pen-nib"
    }
}]
