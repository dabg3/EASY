import typing
import abc
import collections.abc
import imaplib
import email
import email.message
import email.policy
import base64
from requests_oauthlib import OAuth2Session
import time

# ideas for the future

class BaseStorage(abc.ABC):

    @abc.abstractmethod
    def load(self, user: str) -> dict | None:
        pass

    @abc.abstractmethod
    def store(self, user: str, data: dict):
        pass


class MemoryStorage(BaseStorage):
    """Default in-memory storage"""

    def __init__(self):
        self._data = {}

    def load(self, user: str) -> dict | None:
        return self._data.get(user)

    def store(self, user: str, data: dict):
        self._data[user] = data

##


class Authentication(abc.ABC):

    def __init__(self):
        pass

    @property
    @abc.abstractmethod
    def imapMechanism(self) -> str:
        pass

    @abc.abstractmethod
    def authenticate(self, user: str) -> collections.abc.Callable[[bytes], bytes]:
        pass

    # pass error as argument ?
    @abc.abstractmethod
    def handle_auth_attempt_failure(self, user: str) -> bool:
        """Return True if retry should be attempted. (may change)"""
        pass

    @abc.abstractmethod
    def handle_auth_failure(self, user: str):
        pass


class OAuthConf(typing.TypedDict):
    auth_uri: str
    token_uri: str
    refresh_uri: str | None
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
        # TODO here I can pass token state (token=load_...)
        self._oauth = OAuth2Session(
            conf.get('client_id'),
            scope=conf.get('scopes'),
            redirect_uri=conf.get('redirect_uri')
        )

    @property
    def imapMechanism(self) -> str:
        return 'XOAUTH2'

    def _fetchTokens(self, auth_res: str):
        response = self._oauth.fetch_token(
            self._conf.get('token_uri'),
            client_secret=self._conf.get('client_secret', None),
            authorization_response=auth_res,
            include_client_id=True
        )
        return response 

    def _requestAuth(self) -> str:
        auth_url, state = self._oauth.authorization_url(
                self._conf.get('auth_uri') 
        )
        return self._user_prompt(auth_url)

    def authenticate(self, user: str) -> collections.abc.Callable[[bytes], bytes]:
        response = self._load_auth_res(user)
        if not response:
            auth_res = self._requestAuth()
            response = self._fetchTokens(auth_res)
            self._store_auth_res(user, response)
        if 'expires_at' in response and time.time() > response['expires_at']:
            self.refresh(user)
        auth_string = f"user={user}\x01auth=Bearer {response['access_token']}\x01\x01"
        authobject = lambda b: auth_string.encode()
        return authobject

    def _load_auth_res(self, user: str) -> dict:
        pass

    def _store_auth_res(self, user: str, data: dict):
        pass

    def refresh(self, user: str):
        auth_res = self._load_auth_res(user)
        refresh_uri = self._conf['refresh_uri'] if self._conf.get('refresh_uri') \
                                                else self._conf['token_uri']
        response = self._oauth.refresh_token(
            refresh_uri, 
            refresh_token=auth_res['refresh_token'],
            include_client_id=True,
            client_id=self._conf.get('client_id'),
            client_secret=self._conf.get('client_secret', None),
        )
        self._store_auth_res(user, response)

    def handle_auth_attempt_failure(self, user: str) -> bool:
        self.refresh(user)
        return True

    def handle_auth_failure(self, user: str):
        # passing None equals delete 
        # TODO better api
        # think about a succeed handler that would store working credentials, 
        # instead of delete after failure
        self._store_auth_res(user, None)

    @classmethod
    def client(cls, conf: OAuthConf):
        return cls(conf, prompt_cli_handler_auth_url)


# interactive auth
def prompt_cli_handler_auth_url(auth_url: str) -> str:
    print(f'To authorize access go to \n\n{auth_url}\n')
    auth_res = input('Enter the full callback URL\n')
    return auth_res


class ImapConf(typing.TypedDict):
    imap_server: str
    imap_port: int
    # ssl: bool


class ImapInbox():

    def __init__(self, conf: ImapConf):
        self._imap = imaplib.IMAP4_SSL(conf['imap_server'], conf['imap_port'])

    def fetch(
        self, *, batch_size=100
    ) -> typing.Generator[list[email.message.EmailMessage], None, None]:
        # TODO handle exceptions
        status, data = self._imap.select('INBOX', readonly='True')
        if status != 'OK':
            #print('imap select error')
            return
        status, data = self._imap.search(None, 'ALL')
        if status != 'OK':
            #print('imap search error')
            return
        ids = data[0].split()
        #print(f"\nFetching {len(ids)} emails...\n")
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
    
    def authenticate(self, user: str, auth: Authentication, max_retries: int = 1):
        for attempt in range(1, max_retries + 2):
            try:
                authobject = auth.authenticate(user)
                self._imap.authenticate(auth.imapMechanism, authobject)
                return
            except imaplib.IMAP4.error as e:
                auth.handle_auth_attempt_failure(user)
        auth.handle_auth_failure(user)
        # TODO better exception
        raise Exception(
            f"Failed to authenticate after {attempt} attempts"
        )