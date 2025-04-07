import typing
import email.message
import email.utils
import re
import html.parser

class Features(typing.TypedDict):
    has_list_unsubscribe: typing.Literal[0, 1]
    has_list_id: typing.Literal[0, 1]
    has_precedence: typing.Literal[0, 1]
    has_feedback_id: typing.Literal[0, 1]
    has_mailer: typing.Literal[0, 1]
    has_campaign: typing.Literal[0, 1]
    has_csa_complaints: typing.Literal[0, 1]
    is_replyto_equal_from: typing.Literal[0, 1]
    recipients_count: int
    media_html_ratio: float
    self_ref_links_count: int
    has_attachment: typing.Literal[0, 1]

# TODO all features that require 'walking' the body parts
#   can be written better to improve performance.
#   Right now every evaluation 'walks' making the process inefficient.


def evaluate(msg: email.message.EmailMessage) -> Features | None:
    if msg is None:
        return None
    try:
        features: Features = {}
        # headers presence features
        features['has_list_unsubscribe'] = 1 if msg.get('list-unsubscribe') else 0
        features['has_list_id'] = 1 if msg.get('list-id') else 0
        features['has_precedence'] = 1 if msg.get('precedence') else 0
        features['has_feedback_id'] = 1 if msg.get('feedback-id') \
                                        or msg.get('x-feedback-id') else 0
        features['has_mailer'] = 1 if msg.get('x-mailer') else 0
        features['has_campaign'] = 1 if msg.get('x-campaign') else 0
        features['has_csa_complaints'] = 1 if msg.get('x-csa-complaints') else 0
        # headers value features
        features['is_replyto_equal_from'] = 1 if _equals_replyto_from(msg) else 0
        features['recipients_count'] = _count_recipients(msg)
        # body value features
        features['media_html_ratio'] = _calculate_media_html_ratio(msg)
        features['html_style_ratio'] = _calculate_html_style_ratio(msg)
        features['self_ref_links_count'] = _count_self_ref_links(msg)
        features['has_attachment'] = 1 if _has_attachment(msg) else 0
        return features
    except Exception as e:
        print('error:', e)
        print('caused by msg:', msg.get('message-id'))
        # TODO log
        return None


def _equals_replyto_from(msg: email.message.EmailMessage) -> bool:
    # RFC6854 allows group syntax
    from_addresses = email.utils.getaddresses(msg.get_all('from', []))
    replyto_addresses = email.utils.getaddresses(msg.get_all('reply-to', []))
    return len(replyto_addresses) == 0 \
           or _equals(replyto_addresses, from_addresses)


def _equals(addresses1: list[tuple[str, str]],
            addresses2: list[tuple[str, str]]) -> bool:
    if len(addresses1) != len(addresses2):
        return False
    emails1 = map(lambda t: t[1], addresses1)
    emails2 = map(lambda t: t[1], addresses2)
    for a1 in emails1:
        if a1 not in emails2:
            return False
    return True


def _count_recipients(msg: email.message.EmailMessage) -> int:
    # 'to' addresses may be duplicate in 'resent-to', same for other 'resent-' fields. 
    # That's good because a service mail won't likely have any 'resent-' field,
    # so human emails would have an higher amount of recipients just because of 
    # that duplication.
    # update: actually resent headers are not used that much.
    tos = msg.get_all('to', [])
    ccs = msg.get_all('cc', [])
    resent_tos = msg.get_all('resent-to', [])
    resent_ccs = msg.get_all('resent-cc', [])
    return len(email.utils.getaddresses(tos + ccs + resent_tos + resent_ccs))


class HtmlValidator(html.parser.HTMLParser):

    _tags = ['html', 'head', 'body']

    def __init__(self):
        super().__init__()
        # valid html stack would be:
        # [ html, head, head, body, body, html ]
        self._stack: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag in self._tags:
            self._stack.append(tag)

    def handle_endtag(self, tag):
        if tag in self._tags:
            self._stack.append(tag)

    def is_valid(self) -> bool:
        return self._stack == ['html', 'head', 'head', 'body', 'body', 'html']


import math
def _calculate_media_html_ratio(
    msg: email.message.EmailMessage, 
    threshold: float = 0.2,
    steepness: float = 15
) -> float:
    # return a value between 0..1 (i.e html_only...media_only)
    media_bytes = 0
    html_bytes = 0
    # multipart can be laid out hierarchically
    for p in msg.walk():
        if p.is_multipart():
            continue
        elif p.get_content_maintype() == 'text' \
        and 'html' in p.get_content_subtype():
            html_bytes += _size_bytes(p.get_content(), p.get_content_charset())
        elif isinstance(p.get_content(), bytes):
            media_bytes += len(p.get_content())
        else:
            # prevent html declared as plain text
            html_validator = HtmlValidator()
            html_validator.feed(p.get_content())
            if html_validator.is_valid():
                html_bytes += _size_bytes(p.get_content(), p.get_content_charset())
            else:
                # any content-type that is text but not html 
                media_bytes += _size_bytes(
                    clean_text(p.get_content()), 
                    p.get_content_charset()
                )
    sum_bytes = media_bytes + html_bytes
    if sum_bytes == 0:
        raise ValueError("unexpected body content")
    ratio = media_bytes / sum_bytes
    if ratio == 0 or ratio == 1:
        return ratio
    # Apply sigmoid scaling to polarize middle values
    return 1 / (1 + math.exp(-steepness * (ratio - threshold)))


def _size_bytes(s: str, charset: str | None = None) -> int:
    if charset is None:
        charset = 'utf-8'
    return len(s.encode(charset))


def clean_text(text: str) -> str:
    # replace all whitespace (spaces, newlines, tabs) with a single space
    text = re.sub(r'\s+', ' ', text.strip())
    return text


class StyleContentFinder(html.parser.HTMLParser):
    
    def __init__(self):
        super().__init__()
        self._content: str = ''
        self._style_data_next: bool = False

    def handle_starttag(self, tag, attrs):
        a_content = self._extract_style_attribute_content(attrs)
        self._content += a_content
        if not tag == 'style':
            return
        self._style_data_next = True

    @staticmethod
    def _extract_style_attribute_content(attrs) -> str:
        for a,v in attrs:
            if not a == 'style':
                continue
            return v if v else ''
        return ''

    def handle_endtag(self, tag):
        if tag == 'style':
            self._style_data_next = False

    def handle_data(self, data) -> bool:
        if not self._style_data_next:
            return
        self._content += data

    def get_content(self) -> str:
        return self._content
        

# TODO avoid duplicating code, think about a valid abstraction.
#   right now performance can be improved a lot
def _calculate_html_style_ratio(
    msg: email.message.EmailMessage, 
    exponent: float = 0.3
) -> float:
    # return a value between 0..1 (i.e no-html/html_only...style_only)
    html_bytes = 0
    # multipart can be laid out hierarchically
    style_finder = StyleContentFinder()
    for p in msg.walk():
        if p.is_multipart():
            continue
        elif p.get_content_maintype() == 'text' \
        and 'html' in p.get_content_subtype():
            html_bytes += _size_bytes(p.get_content(), p.get_content_charset())
            style_finder.feed(p.get_content())
        elif isinstance(p.get_content(), bytes):
            continue
        else:
            # prevent html declared as plain text
            html_validator = HtmlValidator()
            html_validator.feed(p.get_content())
            if not html_validator.is_valid():
                continue
            html_bytes += _size_bytes(p.get_content(), p.get_content_charset())
            style_finder.feed(p.get_content())
    style_bytes = _size_bytes(style_finder.get_content())
    sum_bytes = style_bytes + html_bytes
    if sum_bytes == 0:
        # no html, content is only 'media'
        # html_media_ratio = 1 when style_ratio = 0
        return 0.0
    ratio = style_bytes / sum_bytes
    return ratio ** exponent


class SelfRefLinkCounter(html.parser.HTMLParser):

    def __init__(self, domain):
        super().__init__()
        self.domain = domain
        self.domain_links_count = 0

    def handle_starttag(self, tag, attrs):
        if not tag == 'a':
            return
        for a, v in attrs:
            if not a == 'href' or v.startswith('mailto:'):
                continue
            if self.domain in v:
                self.domain_links_count += 1


def _count_self_ref_links(msg: email.message.EmailMessage) -> int:
    from_email = email.utils.getaddresses(msg.get_all('from', []))[0][1]
    domain = _extract_email_second_lvl_domain(from_email)
    parser = SelfRefLinkCounter(domain)
    for p in msg.walk():
        # TODO html may be hidden as plain text,
        #   'walking' the body parts should be encapsulated somewhere.
        # 
        if not p.get_content_type() == 'text/html':
            continue
        parser.feed(p.get_content())
    return parser.domain_links_count


def _extract_email_second_lvl_domain(address: str) -> str:
    # input     user@sub.domain.com
    # output    domain.
    root_domain_pattern = r'@([^@]+)$'
    match = re.search(root_domain_pattern, address)
    if match:
        root_domain = match.group(1)
    second_lvl_domain_pattern = r'([^.]+\.)([^.]+)$'
    match = re.search(second_lvl_domain_pattern, root_domain)
    if match:
        return match.group(1)
    raise ValueError(f"cannot parse email address: {address}")


def _has_attachment(msg: email.message.EmailMessage) -> bool:
    for p in msg.walk():
        if not p.get_content_disposition():
            continue
        elif p.get_content_disposition().startswith('attachment'):
            return True
    return False