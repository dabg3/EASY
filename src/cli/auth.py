import typing
import collections.abc
from requests_oauthlib import OAuth2Session

class OAuthConf(typing.TypedDict):
    auth_uri: str
    token_uri: str
    refresh_uri: str | None
    client_id: str
    scopes: list[str]
    client_secret: str | None
    redirect_uri: str

class OauthInteractiveAuthenticator:

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

    def authenticate(self, user: str) -> dict:
        print(self._conf)
        auth_res = self._askUserAuthorization()
        return self._fetchTokens(auth_res)

    def _askUserAuthorization(self) -> str:
        auth_url, state = self._oauth.authorization_url(
                self._conf.get('auth_uri') 
        )
        return self._user_prompt(auth_url)
    
    def _fetchTokens(self, auth_res: str):
        token_res = self._oauth.fetch_token(
            self._conf.get('token_uri'),
            client_secret=self._conf.get('client_secret', None),
            authorization_response=auth_res,
            include_client_id=True
        )
        return token_res
