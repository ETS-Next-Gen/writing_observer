# Testing

Testing is an essential part of software development to ensure the reliability and stability of your code. In the Learning Observer project, we currently support Python testing, using the pytest framework. This document provides an overview of how the testing framework is used in the project.

## Python Testing

We use the [pytest framework](https://docs.pytest.org/) for Python testing. Pytest is a popular testing framework that simplifies writing and running test cases. It provides powerful features, such as fixtures, parametrized tests, and plugins, to help you test your code efficiently and effectively.

### Setting Up the Testing Environment

Before writing and running tests, it's essential to set up the testing environment correctly. Here is a step-by-step guide on how to set up the testing environment:

1. Install Python dependencies required for the project. You can find these dependencies in the `requirements.txt` file in the project's root directory.
2. Install the Python packages for the modules you will be testing. In the Learning Observer project, this includes the `writing_observer`, `lo_dash_react_components`^, and `wo_highlight_dashboard` modules.

^ This requires node v16 to installed as it needs to build the components during install

### Writing Test Cases

To write test cases for your Python code, follow these guidelines:

1. Create a `tests` directory in the module you want to test, if it doesn't already exist.
2. For each file or functionality you want to test, create a separate test file with a name in the format `test_<filename>.py` or `test_<functionality>.py`.
3. Inside each test file, write test functions that test specific aspects of your code. Start each test function's name with `test_` to ensure that pytest can discover and run the test.

### Running Tests

Once you have written your test cases, you can run them using the pytest command:

```bash
pytest <module_directory>
```

For example, to run tests for the `wo_highlight_dashboard` module, you would run:

```bash
pytest modules/wo_highlight_dashboard/
```

### GitHub Actions for Automated Testing

To automate testing in your project, you can use GitHub Actions. This allows you to run tests automatically when you push changes to your repository. The provided GitHub Action YAML file sets up a testing environment for the specified Python versions, installs the necessary dependencies, and runs the tests using pytest. You can customize this file to add or modify steps as needed for your project.

If your tests should be automated make sure to provide them as a parameter in the `.github/workflows/pytest.yml`. While we work on cleaning up the prior testing framework, we only run select tests.

```yml
    - name: Unit testing with pytest
      run: |
        pytest modules/wo_highlight_dashboard/
```

## Other testing

Not yet implemented.