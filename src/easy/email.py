import typing
import collections.abc
import imaplib
import email.message
import email.policy
import base64
import abc
from requests_oauthlib import OAuth2Session
import mailbox
import inspect


class Inbox(abc.ABC):

    @abc.abstractmethod
    def fetch(self, *, batch_size=100):
        pass


class ImapConf(typing.TypedDict):
    imap_server: str
    imap_port: int
    # ssl: bool
    
_imap_annotations = inspect.get_annotations(ImapConf)

class ImapInbox(Inbox):

    def __init__(self, conf: ImapConf, credentials: dict):
        self._client = imaplib.IMAP4_SSL(conf['imap_server'], conf['imap_port'])
        login_fn = _login_imap(credentials)
        login_fn(self._client)

    def fetch(
        self, *, batch_size=100
    ) -> typing.Generator[email.message.EmailMessage, None, None]:
        # TODO handle exceptions
        status, data = self._client.select('INBOX', readonly='True')
        if status != 'OK':
            #print('imap select error')
            return
        status, data = self._client.search(None, 'ALL')
        if status != 'OK':
            #print('imap search error')
            return
        ids = data[0].split()
        for i in range(0, len(ids), batch_size):
            batch_ids = b','.join(ids[i:i+batch_size]).decode('UTF-8')
            typ, data = self._client.fetch(batch_ids, '(RFC822)')
            msgs = map(
                lambda d: email.message_from_bytes(d[1], policy=email.policy.default), 
                filter(
                    lambda d: isinstance(d, tuple), 
                    data
                )
            )
            for m in msgs:
                yield m


def _login_imap(credentials: dict) -> collections.abc.Callable[[imaplib.IMAP4], None]:

    def _login_oauth(client: imaplib.IMAP4):
        auth_string = f"user={credentials['user']}\x01auth=Bearer {credentials['access_token']}\x01\x01"
        authobject = lambda b: auth_string.encode()
        client.authenticate('XOAUTH2', authobject)

    def _login_basic(client: imaplib.IMAP4):
        raise NotImplementedError("basic login not supported")

    if credentials['access_token'] is not None:
        return _login_oauth
    # fallback
    return _login_basic


class MboxConf(typing.TypedDict):
    path: str

_mbox_annotations = inspect.get_annotations(MboxConf)


class LocalMbox(Inbox):

    def __init__(self, conf: MboxConf):
        self._mailbox = mailbox.mbox(conf['path'])

    def fetch(
        self, *, batch_size=1
    ) -> typing.Generator[email.message.EmailMessage, None, None]:
        for msg in self._mailbox.itervalues():
            msgb = msg.as_bytes()
            yield email.message_from_bytes(msgb, policy=email.policy.default)



#def instance_inbox(conf: ImapConf | MboxConf, credentials: dict = None) -> Inbox:
#    global _imap_annotations
#    global _mbox_annotations
#    if inspect.get_annotations(conf) is _imap_annotations:
#        return ImapInbox(conf, credentials)
#    if inspect.get_annotations(conf) is _mbox_annotations:
#        return LocalMbox(conf)
#    raise ValueError("invalid inbox configuration")

