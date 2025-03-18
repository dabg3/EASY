import email.message
import email.utils


def evaluate(msg: email.message.EmailMessage) -> dict:
    if msg is None:
        return {}
    features = {}
    features.update(_evaluate_headers_presence_features(msg))
    features.update(_evaluate_headers_value_features(msg))
    features.update(_evaluate_content_features(msg))
    return features


def _evaluate_headers_presence_features(msg: email.message.EmailMessage) -> dict:
    # check for the presence of some headers to evaluate features
    features = {}
    features['has_list_unsubscribe'] = 1 if msg.get('list-unsubscribe') else 0
    features['has_list_id'] = 1 if msg.get('list-id') else 0
    features['has_precedence'] = 1 if msg.get('precedence') else 0
    features['has_feedback_id'] = 1 if msg.get('feedback-id') \
                                    or msg.get('x-feedback-id') else 0
    features['has_mailer'] = 1 if msg.get('x-mailer') else 0
    features['has_campaign'] = 1 if msg.get('x-campaign') else 0
    features['has_csa_complaints'] = 1 if msg.get('x-csa-complaints') else 0
    return features


def _evaluate_headers_value_features(msg: email.message.EmailMessage) -> dict:
    # inspect the value of some headers to evaluate features
    features = {}
    # RFC6854 allows group syntax
    from_addresses = email.utils.getaddresses(msg.get_all('from', []))
    replyto_addresses = email.utils.getaddresses(msg.get_all('reply-to', []))
    features['is_replyto_equal_from'] = 1 if len(replyto_addresses) == 0 \
                                          or _equals(replyto_addresses,
                                                    from_addresses) \
                                          else 0
    # TODO number of recipients
    return features


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


def _evaluate_content_features(msg: email.message.EmailMessage) -> dict:
    # inspect the body to evaluate features    
    features = {}
    return features
 

def label_automatically(features: list[dict]) -> list[str]:
    """Analyze features to label an email as 'sent-by-human' or 'sent-by-service'
    according to a set of heuristics   

    :return: list of labels as int: 0 -> human, 1 -> service 
    """
    return 
