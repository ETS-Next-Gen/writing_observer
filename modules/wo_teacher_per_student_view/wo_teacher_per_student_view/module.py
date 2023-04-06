import os.path

import dash_bootstrap_components as dbc

from learning_observer.dash_integration import thirdparty_url, static_url

import wo_teacher_per_student_view.view.layout

NAME = "Dash Writing Observer Dashboard"

DASH_PAGES = [
    {
        "MODULE": wo_teacher_per_student_view.view.layout,
        "LAYOUT": wo_teacher_per_student_view.view.layout.layout,
        "ASSETS": 'assets',
        "TITLE": "Writing Observer",
        "DESCRIPTION": "Dashboard for teachers viewing per student data",
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

THIRD_PARTY = {
    "css/bootstrap.min.css": {
        "url": dbc.themes.MINTY,
        "hash": {
            "old": "b361dc857ee7c817afa9c3370f1d317db2c4be5572dd5ec3171caeb812281"
            "cf900a5a9141e5d6c7069408e2615df612fbcd31094223996154e16f2f80a348532",
            "5.1.3": "c03f5bfd8deb11ad6cec84a6201f4327f28a640e693e56466fd80d983ed54"
            "16deff1548a0f6bbad013ec278b9750d1d253bd9c5bd1f53c85fcd62adba5eedc59"
        }
    },
    "css/fontawesome_all.css": {
        "url": dbc.icons.FONT_AWESOME,
        "hash": {
            "6.1.1": "535a5f3e40bc8ddf475b56c1a39a5406052b524413dea331c4e683ca99e39"
            "6dbbc11fdce1f8355730a73c52ac6a1062de1938406c6af8e4361fd346106acb6b0",
            "6.3.0": "1496214e7421773324f4b332127ea77bec822fc6739292ebb19c6abcc22a5"
            "6248e0634b4e0ca0c2fcac14dc10b8d01fa17febaa35f46731201d1ffd0ab482dd7"
        }
    },
    "webfonts/fa-solid-900.woff2": {
        "url": os.path.dirname(os.path.dirname(dbc.icons.FONT_AWESOME)) + "/webfonts/fa-solid-900.woff2",
        "hash": {
            "6.1.1": "6d3fe769cc40a5790ea2e09fb775f1bd3b130d2fdae1dd552f69559e7ca4c"
            "a047862f795da0024737e59e3bcc7446f6eec1bab173758aef0b97ba89d722ffbde",
            "6.3.0": "d50c68cd4b3312f50deb66ac8ab5c37b2d4161f4e00ea077"
            "326ae76769dac650dd19e65dee8d698ba2f86a69537f38cf4010ff45227211cee8b382d9b567257a"
        }
    },
    "webfonts/fa-solid-900.ttf": {
        "url": os.path.dirname(os.path.dirname(dbc.icons.FONT_AWESOME)) + "/webfonts/fa-solid-900.ttf",
        "hash": {
            "6.1.1": "0fdd341671021d04304186c197001cf2e888d3028baaf9a5dec0f0e496959"
            "666e8a2e34aae8e79904f8e9b4c0ccae40249897cce5f5ae58d12cc1b3985e588d6",
            "6.3.0": "5a2c2b010a2496e4ed832ede8620f3bbfa9374778f3d63e4"
            "5a4aab041e174dafd9fffd3229b8b36f259cf2ef46ae7bf5cb041e280f2939884652788fc1e8ce58"
        }
    }
}

# As of today, our goal isn't to have consistent versions installed,
# so much as to verify hashes to block man-in-the-middle
# attacks. We're keeping versions which on different systems here.
#
# We may (and should) remove deprecated versions in the future, but we
# do expect to continue to work with more than one version.
#
# A better design would map version URLs to sha hashes, under
# DRY. That can be done once we either kill "old" above or figure out
# what URL that came from. At that point, we can replace Minty_URLs
# with THIRD_PARTY["css/bootstrap.min.css"]["hash"]

Minty_URLs = [
    'https://cdn.jsdelivr.net/npm/bootswatch@5.1.3/dist/minty/bootstrap.min.css',
]

if (dbc.themes.MINTY not in Minty_URLs):
    print("WARN:: Unrecognized Minty URL detected: {}".format(dbc.themes.MINTY))
    print("You will need to update dash bootstrap components hash value.\n")

FontAwesome_URLs = [
    "https://use.fontawesome.com/releases/v6.3.0/css/all.css",
    "https://use.fontawesome.com/releases/v6.1.1/css/all.css"
]

if (dbc.icons.FONT_AWESOME not in FontAwesome_URLs):
    print("WARN:: Unrecognized Fontawesome URL detected: {}".format(dbc.icons.FONT_AWESOME))
    print("You will need to update the FontAwesome bootstrap components hash value.\n")


COURSE_DASHBOARDS = [{
    'name': "Writing Observer per student view",
    'url': "/wo_teacher_per_student_view/dash/dashboard/",
    "icon": {
        "type": "fas",
        "icon": "fa-pen-nib"
    }
}]
