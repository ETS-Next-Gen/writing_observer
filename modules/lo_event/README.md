# lo_event

The Learning Observer event module is used to handle the logging of event data.

## Installation

This package supports both Node and Python.
However, before installing in either environment, we need to download the [xAPI](https://xapi.com/overview/) components. These components are used to determine the type of events being used.

```bash
cd xapi
./download_xapi_json.sh
```

### As a Node package

To use in a separate node project, such as the `/extension/writing_process`, you need to make the project available on your system.

```bash
npm install
npm link
```

Then from the other node project, run

```bash
npm link lo_event
```

### As a Python package

Simply install the package as a normal python module.

```bash
pip install .
```
