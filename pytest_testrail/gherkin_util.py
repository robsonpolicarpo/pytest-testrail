from os import path, listdir

from gherkin.parser import Parser
from gherkin.token_matcher import TokenMatcher
from gherkin.token_scanner import TokenScanner


def get_feature(file_path: str):
    """ Read and parse given feature file"""
    try:
        with open(file_path, "r", encoding='utf8') as file_obj:
            steam = file_obj.read()
            parser = Parser()
            response = parser.parse(TokenScanner(steam), token_matcher=TokenMatcher('pt'))
    except Exception as ignored:
        raise Exception('Erro in read feature file, verify the file: ' + file_path)
    return response


def get_feature_files_path(export_tests_path: str):
    tests_abs_path = path.abspath(export_tests_path)
    if path.isfile(tests_abs_path):
        return [tests_abs_path]
    files_path = [path.join(tests_abs_path, f) for f in listdir(tests_abs_path) if
                  path.isfile(path.join(tests_abs_path, f))]
    dirs_name = [f for f in listdir(tests_abs_path) if not path.isfile(path.join(tests_abs_path, f))]
    for dir_name in dirs_name:
        curent_path = tests_abs_path + "/" + dir_name
        files_path = files_path + [path.join(curent_path, f) for f in listdir(curent_path) if
                                   path.isfile(path.join(curent_path, f))]
    return files_path
