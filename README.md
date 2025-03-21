# EASY - Email Analysis SYstem

I'm doing this to put in order my email accounts. 
For instance, my primary (and only) use case is listing all the website I've registered to.
I'm sure more use cases will emerge once that is done.

How do I know which services I've registered to?<br>
By classifying emails as 'sent-by-human' or 'sent-by-service' first of al.
I've picked a bunch of features (`src/easy/features.py`) and I'm gonna train a binary classificator on those.
Then some kind of analysis is required to filter services emails.

If you like the project and you would like to contribute somehow (thought about another use cases? great), contact me, I appreciate :) 

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

