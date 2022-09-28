import sys

import wo_dash.pages.assignment_page.layout

NAME = "Dash Writing Observer Prototype Dashboard"

DASH_PAGES = [
    {
        "MODULE": wo_dash.pages.assignment_page.layout,
        "LAYOUT": wo_dash.pages.assignment_page.layout.layout,
        "TITLE": "Writing Observer Dashboard",
        "DESCRIPTION": "Prototype Dashboard for the Writing Observer built with dash",
        "SUBPATH": "dashboard"
    }
]
