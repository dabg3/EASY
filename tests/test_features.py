import unittest
import pathlib
import json
import email
import email.parser
import email.policy
import tests.resources.features as testdata
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
            self.fail('test resources mismatch, every "input .txt" must have a matching "expected .json"')
        for i, path in enumerate(input_paths): 
            msg = read_email_from_file(path)
            expected = read_features_from_file(expected_paths[i])
            with self.subTest(msg=msg, expected=expected):
                features = easy.features.evaluate(msg)
                self.assertEqual(expected, features)


def read_email_from_file(path) -> email.message.EmailMessage:
    with open(path) as fp:
        msg = email.parser.Parser(policy=email.policy.default) \
                .parsestr(fp.read())
    return msg


def read_features_from_file(path) -> dict:
    with open(path) as json_file:
        data = json.load(json_file)
    return data


if __name__ == '__main__':
    unittest.main()