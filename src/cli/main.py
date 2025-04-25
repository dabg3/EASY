import sys
import json
import pathlib
from requests_oauthlib import OAuth2Session
import cli.userdata
import cli.auth
import easy.email
import easy.features
import click
import mailbox


class OauthProviderConf(cli.auth.OAuthConf, easy.email.ImapConf):
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
    credentials: dict = authenticator.authenticate(user)
    datastore.store_json(user, credentials)


@_cli.command()
@click.pass_context
@click.option('--mbox', type=click.Path(dir_okay=False))
@click.argument('user', type=str)
def download(ctx, mbox, user: str):
    domain = user.split('@')[1]
    conf = ctx.obj['providerconfigs'][domain]
    datastore = ctx.obj['userdatastore']
    credentials = datastore.get_json(user)
    if not credentials:
        return
    inbox = easy.email.Inbox(credentials, conf)
    if mbox:
        write_mbox(inbox, mbox)
    else:
        write_stdout(inbox)
   

def write_mbox(inbox: easy.email.Inbox, path):
    mbox = mailbox.mbox(path)
    for msg in inbox.fetch():
        mbox.add(msg)
    mbox.flush()
    mbox.unlock()


def write_stdout(inbox: easy.email.Inbox):
    for msg in inbox.fetch():
        sys.stdout.write(str(msg) + '\n')


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

    
if __name__ == '__main__':
    _cli()