import sys
import json
import pathlib
from requests_oauthlib import OAuth2Session
import cli.userdata
import easy.email
import easy.features
import click

class OauthProviderConf(easy.email.OAuthConf, easy.email.ImapConf):
    pass


class ProviderConf(OauthProviderConf):
    domains: list[str]


def load_provider_confs() -> list[ProviderConf]:
    provider_confs = []
    conf_dir = pathlib.Path(cli.userdata.get_system_appconfig_path())
    if not conf_dir.exists():
        return provider_confs 
    for conf_file in conf_dir.glob('*.json'):
        try:
            with open(conf_file, 'r') as f:
                data = json.loads(f.read())

            if (isinstance(data, dict) and 
                'auth_uri' in data and 
                'token_uri' in data and 
                'client_id' in data and 
                'scopes' in data and 
                'domains' in data and
                'imap_server' in data and
                'imap_port' in data):

                provider_conf: ProviderConf = {
                    # OAuth fields
                    'auth_uri': data['auth_uri'],
                    'token_uri': data['token_uri'],
                    'refresh_uri': data.get('refresh_uri'),  # Optional field
                    'client_id': data['client_id'],
                    'scopes': data['scopes'],
                    'client_secret': data.get('client_secret'),  # Optional field
                    'redirect_uri': data['redirect_uri'],
                    # IMAP fields
                    'imap_server': data['imap_server'],
                    'imap_port': data['imap_port'],
                    # Other fields
                    'domains': data['domains']
                }
                
                provider_confs.append(provider_conf)
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            #print(f"Error parsing {conf_file}: {e}")
            continue
    
    return provider_confs


def map_provider_conf_by_domain() -> dict[str, ProviderConf]:
    provider_confs = load_provider_confs()
    mapping = {}
    for provider_conf in provider_confs:
        for domain in provider_conf['domains']:
            mapping[domain] = provider_conf
    return mapping


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


@click.group()
@click.pass_context
def _cli(ctx):
    pass


@_cli.command()
@click.argument('user', type=str)
def download(user: str):
    domain = user.split('@')[1]
    conf = map_provider_conf_by_domain()[domain]
    main_deprecated(user, conf)


@_cli.command()
@click.option('--local', 'is_local_input', flag_value=True, default=False, help='take local path as input')
#@click.option('--no-headers', 'is_local_input', flag_value=True, default=False, help='avoid inserting headers in the first line (csv)')
@click.option('--json', 'output', flag_value='JSON', default='CSV', help="output JSON")
def mkfeatures(is_local_input, output):
    pass


# Current task
# implement download command
#   It should output mbox messages, see how it goes.
#   Remember: the purpose is just obtaining a local database of email
#   Nice: pipelining       

    
# TODO
# interface
#   easycli login
#       store token for subsequent commands
#   easycli download [user]
#       output all messages to stdout,
#   easycli mkfeatures --csv --no-headers
# sources:
#   - provider matching conf.json
#   - mbox
#   - files for train/predict
# easycli commands:
#   - `mkdata --mbox | --features | --label | --visual <output>`
#   - `train <output>`
#   - `predict --weights=`
import mailbox
def main_deprecated(user, provider_conf: OauthProviderConf):
    # TODO proper options
    auth = OAuth2TokenStore.client(provider_conf)
    inbox = easy.email.ImapInbox(provider_conf)
    inbox.authenticate(user, auth)
    for msg_batch in inbox.fetch():
        for msg in msg_batch:
            msg = mailbox.mboxMessage(msg)
            sys.stdout.write(str(msg) + '\n')
            #f = easy.features.evaluate(msg)
            # TODO prediction            
            # pprint.pp(f)