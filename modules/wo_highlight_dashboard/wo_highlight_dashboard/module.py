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
        "hash": "535a5f3e40bc8ddf475b56c1a39a5406052b524413dea331c4e683ca99e39"
        "6dbbc11fdce1f8355730a73c52ac6a1062de1938406c6af8e4361fd346106acb6b0"
    },
    "webfonts/fa-solid-900.woff2": {
        "url": os.path.dirname(os.path.dirname(dbc.icons.FONT_AWESOME)) + "/webfonts/fa-solid-900.woff2",
        "hash": "6d3fe769cc40a5790ea2e09fb775f1bd3b130d2fdae1dd552f69559e7ca4c"
        "a047862f795da0024737e59e3bcc7446f6eec1bab173758aef0b97ba89d722ffbde"
    },
    "webfonts/fa-solid-900.ttf": {
        "url": os.path.dirname(os.path.dirname(dbc.icons.FONT_AWESOME)) + "/webfonts/fa-solid-900.ttf",
        "hash": "0fdd341671021d04304186c197001cf2e888d3028baaf9a5dec0f0e496959"
        "666e8a2e34aae8e79904f8e9b4c0ccae40249897cce5f5ae58d12cc1b3985e588d6"
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
