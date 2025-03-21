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
        self.assertEqual(easy.features.evaluate(None), None)

    def testEvaluation_parameterized(self):
        # test resources are stored in tests/resources/features.
        # input emails file format:         {id}.txt 
        # expected features file format:    {id}.json 
        testdata_path = pathlib.Path(testdata.__path__[0])
        input_paths = list(testdata_path.glob('*.txt'))
        for input_path in input_paths: 
            expected_path = find_matching_expected(input_path.stem, testdata_path)
            if expected_path is None:
                self.fail('test resources mismatch, every "input .txt" must have a matching "expected .json"')
            try:
                email = read_email_from_file(input_path)
            except Exception:
                self.fail(f"cannot parse input file: {input_path}")
            try:
                expected = read_features_from_file(expected_path)
            except Exception:
                self.fail(f"cannot parse expected file: {expected_path}")
            with self.subTest(f"resource {input_path.name}"):
                #if not input_path.stem == '4':
                #    continue
                features = easy.features.evaluate(email)
                self.assertEqual(features, expected)


def find_matching_expected(res_id, testdata_path) -> pathlib.Path | None:
    expected_paths = list(testdata_path.glob('*.json'))
    for p in expected_paths:
        if res_id == p.stem:
            return p
    return None 


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