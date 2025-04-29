import sys
import json
import pathlib
from requests_oauthlib import OAuth2Session
import cli.userdata
import easy.auth
import easy.email
import email.message
import easy.features
import click
import mailbox


class OauthProviderConf(easy.auth.OAuthConf, easy.email.ImapConf):
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

           
def configure_inbox(ctx, *, provider=None, user=None, path=None):
    if path:
        conf = easy.email.MboxConf(path=path)
        return easy.email.LocalMbox(conf)
    if user:
        domain = user.split('@')[1]
        conf = ctx.obj['providerconfigs'][domain] if not provider \
                                                  else ctx.obj['providerconfigs'][provider]
        datastore = ctx.obj['userdatastore']
        credentials = datastore.get_json(user)
        return easy.email.ImapInbox(conf, credentials)


@click.group()
@click.pass_context
def _cli(ctx):
    ctx.ensure_object(dict)
    ctx.obj['userdatastore'] = cli.userdata.UnsafeFileStore()
    ctx.obj['providerconfigs'] = map_provider_conf_by_domain()


@_cli.command()
@click.pass_context
@click.option('--provider', type=str)
@click.argument('user', type=str)
def login(ctx, provider: str, user: str):
    # if user is email, use domain to retrieve conf.
    # if user is username, a parameter to specify provider is required.
    # For now only oauth works so user is always an email
    domain = user.split('@')[1]
    conf = ctx.obj['providerconfigs'][domain] if not provider \
                                              else ctx.obj['providerconfigs'][provider]
    datastore = ctx.obj['userdatastore']
    # this method authenticates users and stores credentials (tokens or password for basic auth)
    # to be used for subsequent commands
    authenticator = easy.auth.OauthInteractiveAuthenticator(conf, prompt_auth_url_cli)
    credentials: dict = authenticator.authenticate(user)
    datastore.store_json(user, credentials)


@_cli.command()
@click.pass_context
@click.option('--mbox', type=click.Path(dir_okay=False))
@click.option('--provider', type=str)
@click.argument('user', type=str)
def download(ctx, mbox, provider, user: str):
    inbox = configure_inbox(ctx, user=user, provider=provider)
    if mbox:
        write_mbox(inbox, mbox)
    else:
        write_stdout(inbox)


def write_mbox(inbox: easy.email.ImapInbox, path):
    mbox = mailbox.mbox(path)
    for msg in inbox.fetch():
        mbox.add(msg)
    mbox.flush()
    mbox.unlock()


def write_stdout(inbox: easy.email.ImapInbox):
    # experimental, how to separate messages ?
    for msg in inbox.fetch():
        sys.stdout.write(str(msg) + '\n')


@_cli.command()
@click.pass_context
@click.option('--mbox', type=click.Path(exists=True, dir_okay=False))
@click.option('--csv', 'output', flag_value='CSV', default=True)
@click.option('--json', 'output', flag_value='JSON')
@click.option('--no-headers', 'output_headers', flag_value=False, default=True, help='avoid inserting headers in the first line (csv)')
@click.option('--msgid', 'output_msgid', flag_value=True, default=False, help='avoid inserting headers in the first line (csv)')
@click.argument('user', required=False, type=str)
def mkfeatures(ctx, mbox, output, output_headers, output_msgid, user):
    inbox = configure_inbox(ctx, user=user, path=mbox)
    features = \
        filter(
            lambda f: f is not None, 
            map(
                lambda m: mkfeature(m, msgid=output_msgid), 
                inbox.fetch()
            )
        )
    # csv
    match output:
        case 'JSON':
            write_json(features) 
        case 'CSV':
            write_csv(features, write_headers=output_headers) 


def mkfeature(m: email.message.EmailMessage, msgid: bool = False):
    f = easy.features.evaluate(m)
    if f is not None and msgid:
        f['msgid'] = m['message-id']
    return f


def write_json(features):
    for f in features:
        sys.stdout.write(json.dumps(f) + '\n')


def write_csv(features, *, write_headers: bool = True):
    for i, f in enumerate(features):
        keys = f.keys()
        if i == 0 and write_headers:
            headers = ",".join(keys)
            sys.stdout.write(headers + '\n')
        row = [f[key] for key in keys]
        out = ','.join(map(str, row))
        sys.stdout.write(out + '\n')


@_cli.command()
@click.pass_context
@click.option('--mbox', type=click.Path(exists=True, dir_okay=False))
@click.option('--csv', 'output', flag_value='CSV', default=True)
@click.option('--json', 'output', flag_value='JSON')
@click.option('--no-headers', 'headers', flag_value=False, default=True, help='avoid inserting headers in the first line (csv)')
@click.argument('user', required=False, type=str)
def label(ctx, mbox, output, user):
    inbox = configure_inbox(ctx, user=user, path=mbox)
    for msg in inbox.fetch():
        label = label_msg(msg)


def label_msg(msg: email.message.EmailMessage) -> int:
    pass


def render_msg(msg: email.message.EmailMessage) -> int:
    pass


@_cli.command()
@click.pass_context
@click.option('--model', default=None, type=str)
@click.argument('labels', type=click.Path(dir_okay=False))
def train(ctx, model, labels):
    pass

    
if __name__ == '__main__':
    _cli()

# api
# input: provider_conf -> list[EmailMessage]
# mkfeature: EmailMessage -> dict
# label: dict -> dict
# train: list[dict] -> weights
# analyze: (model, weights) -> dict