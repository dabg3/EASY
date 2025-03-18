# EASY - Email Analysis SYstem

## Development 

Install venv `python -m venv venv`

This project uses the [src layout](https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/), 
it requires packages installed in development mode for tests to work
```
pip install -e .
```

Tests are based on the `unittest` module, autodiscovery works as long as test files and methods are prefixed with `test`.
Execute all tests 
```
python -m unittest
```

Build with
```
python -m build .
```

