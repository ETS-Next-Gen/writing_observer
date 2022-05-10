'''
Integration with Jupyter notebooks.

We're still figuring this out.

By the current design:

1. The user can run the notebook 
2. The user can create an iframe in the notebook
3. We have a server which serves the repos to iframes in 
   the notebook to render data.
4. We have tools to inject data into the iframes.

This allows us to have a notebook where we can prototype
dashboards, and analyze data.

The notebook architecture will allow us to capture the
analyses run in the notebook, for open science.

Much of this code is untested and still in flux.
'''

import argparse
import json
import uuid
import base64

import aiohttp.web

import learning_observer.routes

import gitserve.aio_gitserve


from IPython.core.display import display, HTML


def make_iframe(url, width, height):
    '''
    Make an iframe for a given URL.

    Args:
        url (str): The URL to load in the iframe.
        width (int): The width of the iframe.
        height (int): The height of the iframe.

    Returns:
        str: The iframe ID.
    '''
    frameid = str(uuid.uuid1())

    display(HTML(f"""
    <iframe src="{url}" width="{width}" height="{height}"
    allowfullscreen></iframe>
    """))
    return frameid


def inject_script(frameid, script):
    '''
    Inject a script into an iframe.

    Args:
        frameid (str): The ID of the iframe to inject into.
        script (str): The script to inject.

    Returns:
        None
    '''
    b64_script = base64.b64encode(script.encode('utf-8')).decode('utf-8')
    display(HTML(f"""
    <script>
    var frame = document.getElementById("{frameid}");
    var doc = frame.contentDocument || frame.contentWindow.document;
    var script = doc.createElement("script");
    script.innerHTML = atob("{b64_script}");
    doc.body.appendChild(script);
    </script>
    """))


def inject_data(frameid, data):
    '''
    Inject data into an iframe.

    Args:
        frameid (str): The ID of the iframe to inject into.
        data (dict): The data to inject.

    Returns:
        None
    '''
    data_loader = "lo_data="+json.dumps(data);
    display(HTML(f"""
    <script>
    var frame = document.getElementById("{frameid}");
    var doc = frame.contentDocument || frame.contentWindow.document;
    var script = doc.createElement("script");
    script.innerHTML = atob("{data_loader}");
    doc.body.appendChild(script);
    </script>
    """))


def run_server(repos, port=8008):
    '''
    Run a server to serve the given repos.

    Args:
        repos (list): A list of repos to serve.
        port (int): The port to serve on.

    Returns:
        Never :)
'''
    app = aiohttp.web.Application()
    learning_observer.routes.register_static_routes(app)
    learning_observer.routes.register_repo_routes(app, repos)
    aiohttp.web.run_app(app, port=port)


if __name__ == "__main__":
    def to_bool(s):
        '''
        Convert a string to a boolean.
        
        Args:
            s (str): The string to convert.

        Returns:
            bool: The converted string.
        '''
        if s.lower().strip() in ['true', 't', 'yes', 'y', '1']:
            return True
        elif s.lower().strip() in ['false', 'f', 'no', 'n', '0']:
            return False
        else:
            raise ValueError("Boolean value expected. Got {}".format(s))


    parser = argparse.ArgumentParser(description="Run a server to serve the given repos.")
    parser.add_argument("repos", type=str, nargs="+", help="The repos to serve.")
    parser.add_argument("--port", type=int, default=8008, help="The port to serve on.")
    args = parser.parse_args()
    repos = {}
    for repo in args.repos:
        repo_split_partial = repo.split(";")
        repo_split_default = ["", "", "", False, True]
        repo_split = repo_split_partial + repo_split_default[len(repo_split_partial):]
        repos[repo_split[0]] = {
            "module": repo_split[0],
            "url": repo_split[1],
            "prefix": repo_split[2],
            "bare": to_bool(repo_split[3]),   # This doesn't quite work yet
            "working_tree": to_bool(repo_split[4])
        }
    run_server(repos, args.port)
