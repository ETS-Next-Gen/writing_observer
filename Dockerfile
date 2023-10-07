FROM python:3.9-slim

WORKDIR /usr/src/app

RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates git gcc g++ python3-dev && \
    curl -sL https://deb.nodesource.com/setup_16.x | bash - && \
    apt-get install -y nodejs=16.* && \
    apt-get remove --purge -y curl && \
    apt-get -y autoremove && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* 

COPY . .

RUN pip install -U pip setuptools
RUN pip install --no-cache-dir learning_observer/[wo,awe]
# HACK we need to run the install a second time to properly install lo_dash_react_components
RUN pip install learning_observer/

# TODO we may want this to be a generic image that we can do a variety of things with
# For example, we may want to just run tests or deploy via this dockerfile.
# We should support both
CMD ["pytest", "modules/wo_highlight_dashboard"]
