import os.path
import sys

import dash_bootstrap_components as dbc

from learning_observer.dash_integration import thirdparty_url

import wo_dash.pages.assignment_page.layout

NAME = "Dash Writing Observer Prototype Dashboard"

DASH_PAGES = [
    {
        "MODULE": wo_dash.pages.assignment_page.layout,
        "LAYOUT": wo_dash.pages.assignment_page.layout.layout,
        "ASSETS": 'assets',
        "TITLE": "Writing Observer Dashboard",
        "DESCRIPTION": "Prototype Dashboard for the Writing Observer built with dash",
        "SUBPATH": "dashboard",
        "CSS": [
            thirdparty_url("css/bootstrap.min.css"),
            thirdparty_url("css/fontawesome_all.css")
        ]
    }
]

THIRD_PARTY = {
    "css/bootstrap.min.css": {
        "url": dbc.themes.MINTY,
        "hash": "b361dc857ee7c817afa9c3370f1d317db2c4be5572dd5ec3171caeb812281"
        "cf900a5a9141e5d6c7069408e2615df612fbcd31094223996154e16f2f80a348532"
    },
    "css/fontawesome_all.css": {
        "url": dbc.icons.FONT_AWESOME,
        "hash": "535a5f3e40bc8ddf475b56c1a39a5406052b524413dea331c4e683ca99e39"
        "6dbbc11fdce1f8355730a73c52ac6a1062de1938406c6af8e4361fd346106acb6b0"
    },
    "webfonts/fa-solid-900.woff2": {
        "url": os.path.dirname(os.path.dirname(dbc.icons.FONT_AWESOME))+"/webfonts/fa-solid-900.woff2",
        "hash": "6d3fe769cc40a5790ea2e09fb775f1bd3b130d2fdae1dd552f69559e7ca4c"
        "a047862f795da0024737e59e3bcc7446f6eec1bab173758aef0b97ba89d722ffbde"
    },
    "webfonts/fa-solid-900.ttf": {
        "url": os.path.dirname(os.path.dirname(dbc.icons.FONT_AWESOME))+"/webfonts/fa-solid-900.ttf",
        "hash": "0fdd341671021d04304186c197001cf2e888d3028baaf9a5dec0f0e496959"
        "666e8a2e34aae8e79904f8e9b4c0ccae40249897cce5f5ae58d12cc1b3985e588d6"
    }
}
