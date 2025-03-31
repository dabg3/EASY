import typing
import abc
import collections.abc
import imaplib
import email
import email.message
import email.policy
import base64
from requests_oauthlib import OAuth2Session


class Authentication(abc.ABC):

    def __init__(self):
        pass

    @property
    @abc.abstractmethod
    def imapMechanism(self) -> str:
        pass

    @abc.abstractmethod
    def authenticate(self, user: str) -> str:
        pass


class OAuthConf(typing.TypedDict):
    auth_uri: str
    token_uri: str
    client_id: str
    scopes: list[str]
    client_secret: str | None
    redirect_uri: str


class OAuth2(Authentication):

    def __init__(
        self,
        conf: OAuthConf, 
        user_prompt: collections.abc.Callable[[str], str],
    ):
        self._conf = conf
        self._user_prompt = user_prompt
        self._oauth = OAuth2Session(
            conf.get('client_id'),
            scope=conf.get('scopes'),
            redirect_uri=conf.get('redirect_uri')
        )

    @property
    def imapMechanism(self) -> str:
        return 'XOAUTH2'

    def _fetchToken(self, auth_res: str):
        token = self._oauth.fetch_token(
            self._conf.get('token_uri'),
            client_secret=self._conf.get('client_secret', None),
            authorization_response=auth_res,
            include_client_id=True
        )
        return token

    def _requestAuth(self) -> str:
        auth_url, state = self._oauth.authorization_url(
                self._conf.get('auth_uri') 
        )
        return self._user_prompt(auth_url)

    def authenticate(self, user: str) -> str:
        auth_res = self._requestAuth()
        response = self._fetchToken(auth_res)
        # TODO handle refresh token...
        return user, response['access_token']

    @classmethod
    def client(cls, conf: OAuthConf):
        return cls(conf, prompt_cli_handler_auth_url)


# interactive auth
def prompt_cli_handler_auth_url(auth_url: str) -> str:
    print(f'To authorize access go to \n\n{auth_url}\n')
    auth_res = input('Enter the full callback URL\n')
    return auth_res


class ImapInbox():

    def __init__(self, host: str = None):
        self._imap = imaplib.IMAP4_SSL(host, 993)

    def fetch(
        self, *, batch_size=100
    ) -> typing.Generator[list[email.message.Message]]:
        # TODO handle exceptions
        status, data = self._imap.select('INBOX', readonly='True')
        if status != 'OK':
            print('imap select error')
            return
        status, data = self._imap.search(None, 'ALL')
        if status != 'OK':
            print('imap search error')
            return
        ids = data[0].split()
        print(f"Fetching {len(ids)} emails...\n")
        for i in range(0, len(ids), batch_size):
            batch_ids = b','.join(ids[i:i+batch_size]).decode('UTF-8')
            typ, data = self._imap.fetch(batch_ids, '(RFC822)')
            msgs = map(
                lambda d: email.message_from_bytes(d[1], policy=email.policy.default), 
                filter(
                    lambda d: isinstance(d, tuple), 
                    data
                )
            )
            yield list(msgs)
    
    def authenticate(self, user: str, auth: Authentication):
        user, token = auth.authenticate(user)
        auth_string = f"user={user}\x01auth=Bearer {token}\x01\x01"
        #self._imap.debug=100
        try:
            self._imap.authenticate(auth.imapMechanism, lambda x: auth_string)
            print('IMAP Successfully authenticated!')
        except imaplib.IMAP4.error as e:
            print(f"IMAP authentication failed: {e}")
