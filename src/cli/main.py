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


# poc
class OAuth2TokenStore(easy.email.OAuth2):

    def __init__(
        self,
        conf: easy.email.OAuthConf, 
        user_prompt,
    ):
        super().__init__(conf, user_prompt)
        self._store = cli.userdata.UnsafeFileStore()

    def _load_auth_res(self, user: str) -> dict:
        json_res = self._store.get(user)
        return json.loads(json_res.decode()) if json_res else None

    def _store_auth_res(self, user: str, data: dict | None):
        # temporary delete 
        if not data:
            self._store.delete(user)
        self._store.store(user, json.dumps(data).encode())
    

import pprint
def main():
    # TODO proper options
    oauth_conf_filepath = sys.argv[1]
    imap_host = sys.argv[2]
    email = sys.argv[3]

    oauth_conf = load_json_from_file(oauth_conf_filepath)
    auth = OAuth2TokenStore.client(oauth_conf)
    inbox = easy.email.ImapInbox(imap_host)
    inbox.authenticate(email, auth)
    for msg_batch in inbox.fetch():
        for msg in msg_batch:
            f = easy.features.evaluate(msg)
            # TODO prediction
            pprint.pp(f)


if __name__ == "__main__":
    main()