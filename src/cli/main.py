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


def main():
    # TODO proper options
    oauth_conf_filepath = sys.argv[1]
    imap_host = sys.argv[2]
    email = sys.argv[3]
    # oauth client config
    oauth_conf = load_json_from_file(oauth_conf_filepath)
    # userdata_store = cli.userdata.UnsafeJSONFileStore(
         #cli.userdata.get_system_userdata_path()
    # )
    # userdata_json = userdata_store.get(email)
    # userdata = json.loads(userdata_json) if userdata_json else None
    # if not userdata:
         #userdata = get_auth_tokens(oauth, oauth_conf)
         #print(userdata)
         #userdata_store.store(email, json.dumps(userdata))
    # # TODO check access_token expiration, refresh
    # # inspect_token(userdata['access_token'])
    # test_token_validity(userdata['access_token'])
    auth = easy.email.OAuth2.publicClient(oauth_conf) \
           if not 'client_secret' in oauth_conf \
           else easy.email.OAuth2.confidentialClient(oauth_conf)
    inbox = easy.email.ImapInbox(imap_host)
    inbox.authenticate(email, auth)
    for msg_batch in inbox.fetch():
        for msg in msg_batch:
            f = easy.features.evaluate(msg)
            # TODO prediction
            print(f)


if __name__ == "__main__":
    main()