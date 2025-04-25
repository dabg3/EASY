import sys
import json
import pathlib
from requests_oauthlib import OAuth2Session
import cli.userdata
import cli.auth
import easy.email
import easy.features
import click

class OauthProviderConf(easy.email.OAuthConf, easy.email.ImapConf):
    pass


class ProviderConf(OauthProviderConf):
    domains: list[str]


def load_json_from_file(filename) -> any:
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        # TODO exception
        return None


def load_provider_confs() -> list[ProviderConf]:
    provider_confs = []
    conf_dir = cli.userdata.get_system_appconfig_path()
    for conf_file in conf_dir.glob('*.json'):
            conf: ProviderConf = load_json_from_file(conf_file)
            # validation ?
            #provider_conf: ProviderConf = {
            #    # OAuth fields
            #    'auth_uri': conf['auth_uri'],
            #    'token_uri': conf['token_uri'],
            #    'refresh_uri': conf.get('refresh_uri'),  # Optional field
            #    'client_id': conf['client_id'],
            #    'scopes': conf['scopes'],
            #    'client_secret': conf.get('client_secret'),  # Optional field
            #    'redirect_uri': conf['redirect_uri'],
            #    # IMAP fields
            #    'imap_server': conf['imap_server'],
            #    'imap_port': conf['imap_port'],
            #    # Other fields
            #    'domains': conf['domains']
            #}
            provider_confs.append(conf)
    return provider_confs


def map_provider_conf_by_domain() -> dict[str, ProviderConf]:
    provider_confs = load_provider_confs()
    mapping = {}
    for provider_conf in provider_confs:
        for domain in provider_conf['domains']:
            mapping[domain] = provider_conf
    return mapping


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


def prompt_auth_url_cli(auth_url: str) -> str:
    print(f'To authorize access go to \n\n{auth_url}\n')
    auth_res = input('Enter the full callback URL\n')
    return auth_res


@click.group()
@click.pass_context
def _cli(ctx):
    ctx.ensure_object(dict)
    ctx.obj['userdatastore'] = cli.userdata.UnsafeFileStore()
    ctx.obj['providerconfigs'] = map_provider_conf_by_domain()


@_cli.command()
@click.pass_context
@click.argument('user', type=str)
def login(ctx, user: str):
    # if user is email use domain to retrieve conf.
    # if user is username a parameter to specify provider is required.
    # For now only oauth works so user is always an email
    domain = user.split('@')[1]
    conf = ctx.obj['providerconfigs'][domain]
    datastore = ctx.obj['userdatastore']
    # this method authenticates users and stores credentials (tokens or password for basic auth)
    # to be used for subsequent commands
    authenticator = cli.auth.OauthInteractiveAuthenticator(conf, prompt_auth_url_cli)
    auth_res: dict = authenticator.authenticate(user)
    datastore.store_json(user, auth_res)


@_cli.command()
@click.pass_context
@click.argument('user', type=str)
def download(ctx, user: str):
    domain = user.split('@')[1]
    conf = ctx.obj['providerconfigs'][domain]
    datastore = ctx.obj['userdatastore']
    # TODO fetch emails, credentials are stored
    # main_deprecated(user, conf)


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