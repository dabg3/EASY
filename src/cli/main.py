import sys
import json
from requests_oauthlib import OAuth2Session
import cli.userdata
import easy.email
import easy.features

class OauthProviderConf(easy.email.OAuthConf, easy.email.ImapConf):
    pass

def load_conf_from_file(filename) -> OauthProviderConf:
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        # TODO exception
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
    
# TODO
# interface
#   `easycli <source> --user= <command>` 
# sources:
#   - provider matching conf.json
#   - mbox
#   - files for train/predict
# easycli commands:
#   - `mkdata --mbox | --features | --label | --visual <output>`
#   - `train <output>`
#   - `predict --weights=`
#
# `easycli local . predict`
# `easycli `
import pprint
def main():
    # TODO proper options
    provider_conf_path = sys.argv[1]
    email = sys.argv[2]
    provider_conf = load_conf_from_file(provider_conf_path)
    auth = OAuth2TokenStore.client(provider_conf)
    inbox = easy.email.ImapInbox(provider_conf)
    inbox.authenticate(email, auth)
    for msg_batch in inbox.fetch():
        for msg in msg_batch:
            f = easy.features.evaluate(msg)
            # TODO prediction
            pprint.pp(f)


if __name__ == "__main__":
    main()