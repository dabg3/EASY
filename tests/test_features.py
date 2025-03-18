import unittest
import pathlib
import json
import email
import tests.resources.features as testdata;
import easy.features 


class TestFeatures(unittest.TestCase):

    def testEvaluation_None_emptyDict(self):
        self.assertEqual({}, easy.features.evaluate(None))

    def testEvaluation_parameterized(self):
        # test resources are stored in tests/resources/features.
        # input emails file format:         {id}.txt 
        # expected features file format:    {id}.json 
        testdata_path = pathlib.Path(testdata.__path__[0])
        input_paths = list(testdata_path.glob('*.txt'))
        expected_paths = list(testdata_path.glob('*.json'))
        if len(input_paths) != len(expected_paths):
            self.fail("test resources mismatch, every input .txt must have a matching expected .json")
        for i, path in enumerate(input_paths): 
            msg = read_email_from_file(path)
            expected = read_features_dict_from_file(expected_paths[i])
            with self.subTest(msg=msg, expected=expected):
                features = easy.features.evaluate(msg)
                self.assertDictEqual(expected, features)


def read_email_from_file(path):
    with open(path) as fp:
        msg = email.message.EmailMessage()
        msg.set_content(fp.read())
    return msg


def read_features_dict_from_file(path):
    with open(path) as json_file:
        data = json.load(json_file)
    return data


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