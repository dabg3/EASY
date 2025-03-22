import typing
import abc
import imaplib
import email
import email.message
import email.policy


# class Inbox(abc.ABC):
# 
#     @abc.abstractmethod
#     def fetch(self, *, batch_size=100) -> typing.Generator[email.message.Message]:
#         pass
# 
#     # just an idea
#     @abc.abstractmethod
#     def authenticate(self, user: str, password: str) -> None:
#         pass


class ImapInbox():

    def __init__(self, host: str = None):
        self._imap = imaplib.IMAP4_SSL(host)

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
    
    def authenticate(self, user: str, password: str):
        auth_string = f"user={user}\x01auth=Bearer {password}\x01\x01"
        try:
            self._imap.authenticate('XOAUTH2', lambda x: auth_string)
            print('IMAP Successfully authenticated!')
        except imaplib.IMAP4.error as e:
            print(f"IMAP authentication failed: {e}")