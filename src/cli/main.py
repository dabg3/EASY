import sys
import json
from requests_oauthlib import OAuth2Session
import cli.userdata
import easy.email
import easy.features


def load_json_from_file(filename):
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return None


# TODO oauth stuff should be encapsulated somewhere,
#   try adding another provider to see how things change

def configure_oauth(conf: dict, scope):
    return OAuth2Session(
            conf.get('client_id'),
            redirect_uri=conf.get('redirect_uris')[0],
            scope=scope
    )


def get_auth_tokens(
    oauth: OAuth2Session, 
    conf: dict,
    oauth_server_authorization_url: str,
    oauth_server_token_url: str
) -> dict:
    authorization_url, state = oauth.authorization_url(
            oauth_server_authorization_url, 
            access_type="offline"
    )
    print(f'To authorize access go to \n\n{authorization_url}\n')
    auth_res = input('Enter the full callback URL\n')
    token = oauth.fetch_token(
            'https://accounts.google.com/o/oauth2/token',
            authorization_response=auth_res,
            client_secret=conf.get('client_secret')
    )
    return token


def main():
    # TODO proper options
    oauth_conf_filepath = sys.argv[1]
    oauth_scope = sys.argv[2]
    oauth_server_authorization_url = sys.argv[3]
    oauth_server_token_url = sys.argv[4]
    imap_host = sys.argv[5]
    email = sys.argv[6]
    # oauth client config
    oauth_conf = load_json_from_file(oauth_conf_filepath).get('installed')
    oauth = configure_oauth(oauth_conf, oauth_scope)

    userdata_store = cli.userdata.UnsafeJSONFileStore(
        cli.userdata.get_system_userdata_path()
    )
    userdata_json = userdata_store.get(email)
    userdata = json.loads(userdata_json) if userdata_json else None
    if not userdata:
        userdata = get_auth_tokens(
            oauth, 
            oauth_conf, 
            oauth_server_authorization_url, 
            oauth_server_token_url
        )
        userdata_store.store(email, json.dumps(userdata))
    # TODO check access_token expiration, refresh
    inbox = easy.email.ImapInbox(imap_host)
    inbox.authenticate(email, userdata['access_token'])
    for msg_batch in inbox.fetch():
        for msg in msg_batch:
            f = easy.features.evaluate(msg)
            # TODO prediction
            print(f)

if __name__ == "__main__":
    print(sys.argv)
    exit
    main()