# Learning Observer Dash / React Components

Learning Observer Dash / React Components is a Dash component library of components we use in various dashboards for the Learning Observer and modules.

At some point, some of these should meander over to those specific modules, while others should be kept system-wide.

## Install

Get started with:

1. Install npm packages
    ```
    $ npm install
    ```
2. Create a virtual env and activate.
    ```
    $ virtualenv venv
    $ . venv/bin/activate
    ```
    _Note: venv\Scripts\activate for windows_

3. Install python packages required to build components.
    ```
    $ pip install -r requirements.txt
    ```
4. Install the python packages for testing (optional)
    ```
    $ pip install -r tests/requirements.txt
    ```

## Run

1. Run `python usage.py` for the official dash workflow.

2. Run `nodemon`, for the same, automatically restarting and rebuilding when files change

3. Run `webpack-start` to run in WebPack, which dash uses for React development

4. Run `react-start` to test in the main React scripts

Each of these will give slightly different behavior. Development in React tends to have the most rapid development cycle, but at some point, we switch to dash workflows in order to work end-to-end.

Read the `package.json` file to see other scripts available. There's a lot more, and you should be familiar with them.

## Develop

1. To develop a new component, simply toss in a `react.js` file in `src/lib/components`.
2. Remember to use class (not functional) syntax for compatibility with `dash`
3. If the component needs data, toss in a `.testdata.js` file in `src/lib/components`. Note that this file should not use modern JavaScript (we're limited to ES5.1, except for `export default`).
4. Add SCSS. As of this writing, we're still figuring out how to handle that. However:
5. Each component ought to be enclosed in a class of the name of that component (so that, e.g. your styles can be scoped to within there, or so we can introspect what's on a page).
6. Remember that by the time you move from pure React to `dash`, you should follow `dash` conventions. You'll need to support `setProps`, to be a class-based (not functional) component, and the `dash` system needs to be told about the new component [TODO: We need to document this step].

## Test

We're still figuring this out! Generic `dash` instructions are:

- Write tests for your component.
    - A sample test is available in `tests/test_usage.py`, it will load `usage.py` and you can then automate interactions with selenium.
    - Run the tests with `$ pytest tests`.
    - The Dash team uses these types of integration tests extensively. Browse the Dash component code on GitHub for more examples of testing (e.g. https://github.com/plotly/dash-core-components)
- Add custom styles to your component by putting your custom CSS files into your distribution folder (`lo_dash_react_components`).
    - Make sure that they are referenced in `MANIFEST.in` so that they get properly included when you're ready to publish your component.
    - Make sure the stylesheets are added to the `_css_dist` dict in `lo_dash_react_components/__init__.py` so dash will serve them automatically when the component suite is requested.
- [Review your code](./review_checklist.md)

Our plan, over time, is to diverge from `dash`. As a rule, with tests, we don't believe more is better. Tests can break abstractions, introduce unnecessary complexity, and make code less mutable. We would like to have tests for:

1. Test infrastructure for unit tests, ideally which also clearly document the code.
2. General system tests for high-level functionality (e.g. the components build and render without errors).

... and that's it!

## Create a production build

1. Build your code:
    ```
    $ npm run build
    $ npm run build-css
    ```
2. Create a Python distribution
    ```
    $ python setup.py sdist bdist_wheel
    ```
    This will create source and wheel distribution in the generated the `dist/` folder.
    See [PyPA](https://packaging.python.org/guides/distributing-packages-using-setuptools/#packaging-your-project)
    for more information.

3. Test your tarball by copying it into a new environment and installing it locally:
    ```
    $ pip install lo_dash_react_components-0.0.1.tar.gz
    ```

## Share

We encourage you to share your components back with us. That way:
- We're more likely to understand your use-case
- We're less likely to break them as we evolve the system.

## Issues

If ESLint errors block your app, edit `node_modules/react-dev-utils/webpackHotDevClient.js` to disable `handleWarnings`. See:

https://stackoverflow.com/questions/48714225/how-to-not-show-warnings-in-create-react-app