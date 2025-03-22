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

## Run

Right now `easycli` is very bare-bones, it's relevant for testing instead of real usage. 
There's no input arguments parsing yet, at the same time a bunch of inputs are required
making the command cumbersome and quite long.

It's been only tested on gmail, while also implementing the oauth flow according 
to gmail documentation. It's likely gmail is the only provider authenticating, 
more providers are gonna be tested.

```
easycli <path to client_secret.json> \
        <oauth_scope> \
        <oauth_server_authorization_url> \
        <oauth_server_token_url> \
        <imap_host>
        <email>
```

An example: fetching emails from gmail via IMAP.

```
easycli ~/client_secret.json \
        https://mail.google.com/ \
        https://accounts.google.com/o/oauth2/v2/auth \
        https://accounts.google.com/o/oauth2/token \
        imap.gmail.com \
        myemail@gmail.com
```

Google cloud lets you download the `client_secret.json` after you register
the application via Google Cloud Console.

