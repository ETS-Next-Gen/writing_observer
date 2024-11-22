# NGINX Setup and Config

This document contains basic info related to using nginx in the context of writing observer.

## Static Routing Use Case Config

In order to improve event processing efficiency, we will use nginx to route requests to different processes based on whether they are incoming data events (from the extension), or requests for data (from the dashboard). The associated config can be found at `/devops/nginx-static-loadbalance.conf` in this repository.

At the top of that file, the `upstream`s indicate the servers that should be used for each type of request, `dashboard` or `extension`.

The next section, which includes the `map` directive, tells nginx to look for a url query parameter called source (`$arg_source`: `$arg` indicates that it is a url query param, and `source` gives the name). If `source=dashboard`, then it routes to the dashboard server, if `source=extension`, it routes to the extension server, and if no `source` is provided, then it defaults to the dashboard server.

Below, in the `server` block, are general instructions for handling proxying.

## Usage

To deploy nginx, take the appropriate `.conf` file and put it in `/etc/nginx/sites-enabled`. Then, you can use `sudo nginx -t` to validate the config and ensure it is correct--this will print any detected syntax errors in the config files. Finally, restart nginx to apply the new config (for example, with `sudo systemctl restart nginx`)
