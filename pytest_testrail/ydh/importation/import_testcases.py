"""
TestRail util integration
"""
import os
from os import path
from pathlib import Path

from pytest_testrail.model.case import Case
from pytest_testrail.model.section import Section
from pytest_testrail.ydh.tr_base_api import BaseTestRail


def import_testcases():
    section_base_name = ''
    testrail = ImportTestCases("Project Name")
    testrail.import_testcases(section_base_name)
    testrail.close_connection()


class ImportTestCases(BaseTestRail):

    def import_testcases(self, section_name):
        if section_name == '':
            main_sections = self.get_root_sections()
        elif isinstance(section_name, str):
            main_sections = [self.get_section_by_name(self.get_all_sections(), section_name)]
        else:
            raise Exception('Informe a seção para procurar ou passe uma string vazia para começar das seções raízes')
        test_cases = self.client.cases.get_cases(project_id=self.project.id)
        for main_section in main_sections:
            sections = self.get_sections_children(self.get_all_sections(), main_section)
            for section in sections:
                cases_in_section = self.get_cases_by_section(test_cases, section)
                for case in cases_in_section:
                    parent_dir = self.strip_txt_for_dir(main_section.name)
                    file_path = './tests/b2b_plataforma/web/features/' + parent_dir + '/'
                    file_name = self.strip_txt_for_dir(section.name) + '.feature'
                    file_path = file_path + file_name
                    self.write_case(file_path, section, case)

    def write_case(self, file_path, section: Section, case: Case):
        id_bdd = next((ct.id for ct in self.get_templates() if ct.name == 'BDD - Behavior Driven Development'), None)
        id_bdd_steps = next((ct.id for ct in self.get_templates() if ct.name == 'BDD Steps'), None)
        if case.template_id == id_bdd:
            if not path.exists(file_path):
                Path(os.path.dirname(file_path)).mkdir(parents=True, exist_ok=True)
                with open(file_path, 'w') as file_feature:
                    file_feature.write('#language:pt\n\n')
                    file_feature.write(case._content['custom_descricao_funcionalidade'])
                    file_feature.write(case._content['custom_gherkin'])
            else:
                with open(file_path, 'a') as file_feature:
                    file_feature.write('\n' + case._content['custom_gherkin'])
        elif case.template_id == id_bdd_steps:
            if not path.exists(file_path):
                Path(os.path.dirname(file_path)).mkdir(parents=True, exist_ok=True)
                with open(file_path, 'w') as file_feature:
                    file_feature.write('#language:pt\n\n')
                    file_feature.write('Funcionalidade: ' + section.name + '\n\n\n')
            with open(file_path, 'a') as file_feature:
                if case._content['custom_data_set']:
                    string = 'Esquema do Cenario: ' + case.title + '\n'
                    string = string + self.steps_to_text(case._content.get('custom_steps_separated'))
                    string = string + 'Exemplos: \n'
                    string = string + case._content['custom_data_set'] + '\n'
                    file_feature.write(string)
                else:
                    string = 'Cenario: ' + case.title + '\n'
                    string = string + self.steps_to_text(case._content.get('custom_steps_separated')) + '\n'
                    file_feature.write(string)
        else:
            print(f"Template ID not implemented: | {str(case.id)} | {case.title} | {str(case.template_id)} |")

    def steps_to_text(self, steps):
        text = ''
        for step in steps:
            text = text + step['content'] + '\n'
        return text

    def strip_txt_for_dir(self, text: str):
        result = self.remove_accents(text)
        result = result.replace("-", " ").replace("  ", " ").replace(" ", "_").strip().lower()
        return result
