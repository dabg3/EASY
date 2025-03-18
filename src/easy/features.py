import email.message
import email.utils
import re
import html.parser


def evaluate(msg: email.message.EmailMessage) -> dict | None:
    try:
        features = {}
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
        features['is_replyto_equal_from'] = 1 if _is_replyto_equal_from(msg) else 0
        features['recipients_count'] = _count_recipients(msg)
        # body value features
        features['text_html_ratio'] = _calculate_text_html_ratio(msg)
        features['self_ref_links_count'] = _count_self_ref_links(msg)
        features['has_attachment'] = 0 # TODO
        return features
    except Exception as e:
        # TODO log
        return None


def _is_replyto_equal_from(msg: email.message.EmailMessage) -> bool:
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
    tos = msg.get_all('to', [])
    ccs = msg.get_all('cc', [])
    resent_tos = msg.get_all('resent-to', [])
    resent_ccs = msg.get_all('resent-cc', [])
    return len(tos + ccs + resent_tos + resent_ccs)


def _calculate_text_html_ratio(msg: email.message.EmailMessage) -> float:
    # return a value between 0..1 (i.e html_only...plain_only)
    plain_bytes = 0
    html_bytes = 0
    # multipart can be laid out hierarchically
    for p in msg.walk():
        if p.get_content_type() == 'text/plain':
            plain_bytes += _size_bytes(p.get_content(), p.get_content_charset())
        elif p.get_content_type() == 'text/html':
            html_bytes += _size_bytes(p.get_content(), p.get_content_charset())
    sum_bytes = plain_bytes + html_bytes
    if sum_bytes == 0:
        raise ValueError("unexpected body content")
    return plain_bytes / (sum_bytes)


def _size_bytes(s: str, charset: str | None) -> int:
    if charset is None:
        charset = 'utf-8'
    return len(s.encode(charset))


class LinkParser(html.parser.HTMLParser):

    def __init__(self, domain):
        super().__init__()
        self.domain = domain
        self.self_ref_link_count = 0

    def handle_starttag(self, tag, attrs):
        if not tag == 'a':
            return
        for a, v in attrs:
            if not a == 'href':
                continue
            if self.domain in v:
                self.self_ref_link_count += 1


# TODO domain maybe not exactly the same i.e trenitalia.it trenitalia.com
def _count_self_ref_links(msg: email.message.EmailMessage) -> int:
    from_email = email.utils.getaddresses(msg.get_all('from', []))[0][1]
    domain = _extract_email_domain(from_email)
    parser = LinkParser(domain)
    for p in msg.walk():
        if not p.get_content_type() == 'text/html':
            continue
        parser.feed(p.get_content())
    return parser.self_ref_link_count


def _extract_email_domain(address: str) -> str:
    pattern = r'@([^@]+)$'
    match = re.search(pattern, address)
    if match:
        return match.group(1)
    raise ValueError(f"cannot parse email address: {address}")


def label_automatically(features: list[dict]) -> list[str]:
    """Analyze features to label an email as 'sent-by-human' or 'sent-by-service'
    according to a set of heuristics   

    :return: list of labels as int: 0 -> human, 1 -> service 
    """
    return 
