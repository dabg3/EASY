# EASY - Email Analysis SYstem

I'm doing this to put in order my email accounts. 
For instance, my primary (and only) use case is listing all the website I've registered to.
I'm sure more use cases will emerge once that is done.

How do I know which services I've registered to?<br>
By classifying emails as 'sent-by-human' or 'sent-by-service' first of all.
I've picked a bunch of features (`src/easy/features.py`) and I'm gonna train a binary classificator on those.
Then some kind of analysis is required to filter services emails further.

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


## Configuration

A provider must be configured to authenticate properly. 
Note: only authentication via oauth is supported right now, basic auth will be added in future.

`gmail-conf.json`, client is confidential and requires a secret 
```json
{
    "client_id": "<assigned by the authorization server after registration>",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "redirect_uri": "https://localhost",
    "scopes": [
            "https://mail.google.com/"
    ],
    "client_secret": "<secret>"
}
```

`outlook-conf.json`: public client no secret, `offline_access` for getting a refresh token
```json

{
    "client_id": "<assigned after registration>",
    "auth_uri": "https://login.microsoftonline.com/consumers/oauth2/v2.0/authorize",
    "token_uri": "https://login.microsoftonline.com/consumers/oauth2/v2.0/token",
    "redirect_uri": "https://localhost",
    "scopes": [
            "https://outlook.office.com/IMAP.AccessAsUser.All",
            "offline_access"
    ]
}
```


## Run

Right now `easycli` is very bare-bones, it's relevant for testing instead of real usage. 
There's no input arguments parsing yet, arguments follow a certain order.

It's been tested on gmail and outlook, other imap providers supporting 
`SASL XOAUTH2` mechanism may work.

Application must be registered on whatever identity platform you're using e.g. Entra ID to access outlook.
See Register Application for references.

```plain
easycli <path to provider-conf.json> <imap_host> <email>
```

Example: fetching emails from gmail via IMAP.

```sh
easycli gmail-conf.json imap.gmail.com myemail@gmail.com
```

### Known Issues

Under certain conditions a provider may add more scopes in the access token, 
beside those specified as request parameter.

This behaviour makes `requests-oauthlib` throws a _scope has changed_ error and authentication won't succeed.

Fix it by just setting `OAUTHLIB_RELAX_TOKEN_SCOPE` env var

Example: avoid mismatching scopes error
```sh
OAUTHLIB_RELAX_TOKEN_SCOPE=1 easycli outlook-conf.json outlook.office365.com myemail@hotmail.com
```

### Register Application

* [Google/Gmail](https://developers.google.com/identity/protocols/oauth2)
* [Microsoft/Outlook](https://learn.microsoft.com/en-us/exchange/client-developer/legacy-protocols/how-to-authenticate-an-imap-pop-smtp-application-by-using-oauth)


