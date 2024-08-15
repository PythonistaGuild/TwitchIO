# Installing TwitchIO

**TwitchIO 3 currently supports the following [Python](https://www.python.org/downloads/) versions:**


| Python Version           | Status                                                                                       | Notes                                                          |
| -----------              | -------------------------------------------------------------------------------------------- | -------------------------------------------------------------- |
| **`<= 3.10`**            | :fontawesome-solid-triangle-exclamation:{ .icon-warning .pythonista-tag title="Unsupported"} | Unsupported                                                    |
| **`3.11, 3.12`**         | :fontawesome-solid-check:{ .icon-check .pythonista-tag title="Supported" }                   | Supported                                                      |
| **`3.13`**               | :fontawesome-solid-question:{ .icon-unknown .pythonista-tag title="Unknown" }                | Unknown                                                        |


## Virtual Environments

TwitchIO recommends the use of Virtual Environments (venvs).

You can read more about [Virtual Environments here.](https://realpython.com/python-virtual-environments-a-primer/)
Below are some simple commands to help you get started with a **venv** and TwitchIO.

=== "Windows"

    ``` shell
    # Change into your projects root directory or open a terminal there...
    cd path/to/project

    # Create the virtual environment...
    # Replace 3.11 with the Python version you want to use...
    # You can check what Python versions you have installed with:
    # py -0
    py -3.11 -m venv venv

    # Activate your venv...
    # Everytime you want to use your venv in a new terminal you should run this command...
    # You will know your venv is activated if you see the (venv) prefix in your terminal...
    venv/Scripts/Activate

    # Install your packages...
    pip install -U twitchio

    # You can use your venv python while it's activated simply by running py
    # E.g. py main.py
    # E.g. py --version
    py main.py

    # You can deactivate your venv in this terminal with
    deactivate

    # REMEMBER!
    # You have to re-activate your venv whenever it is deactivated to use for it for you project...
    # You will know your venv is activated by looking for the (venv) prefix in your terminal
    ```


=== "Linux & MacOS"

    ``` shell
    # Change into your projects root directory or open a terminal there...
    cd path/to/project

    # Create the virtual environment...
    # Replace 3.11 with the Python version you want to use...
    python3.11 -m venv venv

    # Activate your venv...
    # Everytime you want to use your venv in a new terminal you should run this command...
    # You will know your venv is activated if you see the (venv) prefix in your terminal...
    source venv/bin/activate

    # Install your packages...
    pip install -U twitchio

    # You can use your venv python while it's activated simply by running python
    # E.g. python main.py
    # E.g. python --version
    python main.py

    # You can deactivate your venv in this terminal with
    deactivate

    # REMEMBER!
    # You have to re-activate your venv whenever it is deactivated to use for it for you project...
    # You will know your venv is activated by looking for the (venv) prefix in your terminal
    ```


## Extra and Optional Dependencies

To use certain optional features of TwitchIO you will have to install the required packages needed to run them.

The following commands can be used to install TwitchIO with optional features:

**To use the StarletteAdapter**:
```shell
pip install -U twitchio[starlette]
```

**For development purposes**:
```shell
pip install -U twitchio[dev]
```

**For documentation purposes**:
```shell
pip install -U twitchio[docs]
```


## Custom Index

Using TwitchIO with `Python >= 3.12` may require the use of a custom pip index.

The index allows pip to fetch pre-built wheels for some dependencies that may require build-tools for C/C++ due to not having released their own wheels for recent versions of Python.

Usually with time, dependencies will eventually release wheels for new Python releases.

For convenience we provide an index thanks to [Abstract Umbra](https://github.com/AbstractUmbra)

**To install with prebuilt wheels:**
``` shell
pip install -U twitchio --extra-index-url https://pip.pythonista.gg

```

## Installation Issues
Make sure you have the latest version of Python installed, or if you prefer, a Python version of 3.11 or greater.

If you have any other issues feel free to search for duplicates and then create a new issue on [GitHub](https://github.com/PythonistaGuild/twitchio) with as much detail as possible. Including providing the output of pip, your OS details and Python version.

