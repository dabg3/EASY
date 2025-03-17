import unittest
import easy.features 
import email.parser
import email.policy

mail = """Message-ID: <16159836.1075855377439.whatever>
Date: Fri, 7 Dec 2001 10:06:42 -0800 (PST)
From: from@from.xyz
To: to@to.xyz
Subject: subject
Mime-Version: 1.0
Content-Type: text/plain; charset=us-ascii

Hello
"""

class TestFeatures(unittest.TestCase):

    def setUp(self):
        self.features = initFeatures()

    def testEvaluation_None_emptyDict(self):
        self.assertEqual({}, easy.features.evaluate(None))

    def testEvaluation_noServiceHeaders_defaults(self):
        msg = email.parser.Parser(policy=email.policy.default) \
            .parsestr(mail)
        f = easy.features.evaluate(msg)
        print(f)


def initFeatures() -> dict:
    return {
        'has_list_unsubscribe': 0,
        'has_list_id': 0,
        'has_precedence': 0,
        'has_feedback_id': 0,
        'has_mailer': 0,
        'has_campaign': 0,
        'has_csa_complaints': 0,
        # 'replyTo' is optional, when missing 'from' is used
        'is_replyto_equal_from': 1,
        'recipients_count': 1,
        'text_html_ratio': 1, # only text
        'self_ref_links_count': 0,
        'has_attachment': 0
    } 


if __name__ == '__main__':
    unittest.main()