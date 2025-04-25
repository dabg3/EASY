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

Install venv `python -m venv venv` and activate `source venv/bin/activate`

Install dependencies `pip install -r requirements.txt`

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

Note: only authentication via oauth is supported right now, basic auth will be added in future.

A provider must be configured to authenticate. 
Configuration directory is:
* Linux: value of `XDG_CONFIG_HOME` env var if set, default to `~/.config/easy`
* Windows: value of `PROGRAMDATA` env var if set, default TODO

`gmail-conf.json`: client is confidential and requires a secret 
```json
{
    "client_id": "<assigned by the authorization server after registration>",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "redirect_uri": "https://localhost",
    "scopes": [
            "https://mail.google.com/"
    ],
    "client_secret": "<secret>",
    "imap_server": "imap.gmail.com",
    "imap_port": 993,
    "domains": ["gmail.com"]
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
    ],
    "imap_server": "outlook.office365.com",
    "imap_port": 993,
    "domains": ["outlook.com", "hotmail.com"]
}
```

`domains` field is used to match an email to its provider configuration


## Run

`easycli` has been tested on gmail and outlook, other imap providers supporting 
`SASL XOAUTH2` mechanism may work.

Application must be registered on whatever identity platform you're using e.g. Entra ID to access outlook.
See Register Application for references.

User must authenticate before executing commands

```sh
easycli login myemail@gmail.com
```

Example: fetching emails from gmail via IMAP (writes to STDOUT).

```sh
easycli download myemail@gmail.com
```

Example: store all emails in a mbox file

```sh
easycli download --mbox=myemail.mbox myemail@gmail.com
```


### Known Issues

Under certain conditions a provider may add more scopes in the access token, 
beside those specified as request parameter.

This behaviour makes `requests-oauthlib` throws a _scope has changed_ error and authentication won't succeed.

Fix it by just setting `OAUTHLIB_RELAX_TOKEN_SCOPE` env var

Example: avoid mismatching scopes error
```sh
OAUTHLIB_RELAX_TOKEN_SCOPE=1 easycli download myemail@hotmail.com
```


### Register Application

* [Google/Gmail](https://developers.google.com/identity/protocols/oauth2)
* [Microsoft/Outlook](https://learn.microsoft.com/en-us/exchange/client-developer/legacy-protocols/how-to-authenticate-an-imap-pop-smtp-application-by-using-oauth)


