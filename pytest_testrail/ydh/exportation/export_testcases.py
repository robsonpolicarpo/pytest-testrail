import re
from pathlib import Path
from typing import List

from pytest_testrail.model.case import Case
from pytest_testrail.model.section import Section
from pytest_testrail.ydh.gherkin_util import get_feature_files_path, get_feature
from pytest_testrail.ydh.tr_base_api import BaseTestRail


def export_testcases(request,
                          project_name,
                          feature_path,
                          json_section_path):

    feature_path = get_feature_path(request, feature_path=feature_path)
    files_path = get_feature_files_path(feature_path)
    testrail = ExportTestCases(project_name)
    for file_path in files_path:
        feature = get_feature(file_path)
        testrail.export_tests(feature, json_section_path)
    testrail.close_connection()


def get_feature_path(request, feature_path=''):
    if feature_path == '':
        feature_path = request.config.option.feature_path
    if not Path(feature_path).exists():
        raise Exception(f"File path doesn't exist: {feature_path}, please inform correctly.")
    return feature_path


class ExportTestCases(BaseTestRail):

    def __init__(self, project_name):
        super().__init__(project_name)
        self.parents = []

    def export_tests(self, feature, json_section_path):
        tr_section = self.get_section_adding_if_not_exists(feature, json_section_path)
        tr_suite_cases = self.client.cases.get_cases(project_id=self.project.id)
        cases_in_suite = self.get_cases_by_section(tr_suite_cases, tr_section)
        raw_custom_preconds = []
        for scenario in feature['feature']['children']:
            if scenario['type'] == 'Background':
                raw_custom_preconds = list(
                    '**' + rs['keyword'].strip() + '** ' + rs['text'] for rs in scenario['steps'])
                continue
            raw_cases = self.mount_scenarios(feature, scenario, tr_section, raw_custom_preconds)
            for raw_case in raw_cases:
                print(feature['feature']['name'])
                self.export_case(tr_section.id, cases_in_suite, raw_case)

    def get_section_adding_if_not_exists(self, feature, json_section_path):
        name_section_wanted = self.get_section_on_json(feature, json_section_path)
        root_section = self.get_section_by_name(self.get_root_sections(), self.parents[-1])
        if root_section is None:
            root_section = self.create_section(self.parents[-1], None)
        sections_on_tree = self.get_sections_on_tree(root_section)
        tr_section = self.get_section_by_name(sections_on_tree, name_section_wanted)
        if tr_section is None:
            parent = self.add_parent_if_not_exists(sections_on_tree)
            tr_section = self.create_section(name_section_wanted, parent.id)
        self.parents.clear()
        return tr_section

    def get_section_on_json(self, feature, json_section_path):
        num_feature_wanted = re.search("[\d]{3}", feature['feature']['name'].strip()).group()
        data_dict = self.get_partial_dict(json_section_path, self.get_project_by_tag(feature))
        name_section_wanted = self.recursive_lookup(num_feature_wanted, data_dict)
        if name_section_wanted is None:
            raise Exception(f"Name/Number {num_feature_wanted} of section not found in json  >> {json_section_path}")
        return name_section_wanted

    def add_parent_if_not_exists(self, sections):
        """Return parent and create him if not exists"""
        section = None
        for parent_name in reversed(self.parents):
            section = self.get_section_by_name(sections, parent_name)
            if section is None:
                section = self.create_section(parent_name, parent_section.id)
            parent_section = section
        return section

    def recursive_lookup(self, value, dictionary: dict):
        if value in dictionary:
            return dictionary[value]
        for dict_onboard in dictionary.values():
            if isinstance(dict_onboard, dict):
                value_recursive = self.recursive_lookup(value, dict_onboard)
                if value_recursive is not None:
                    if dict_onboard['name'] != self.project.name:
                        self.parents.append(dict_onboard['name'])
                    return value_recursive
        self.parents.clear()
        return None

    def get_partial_dict(self, dictionary: dict, value):
        if value in dictionary:
            return dictionary
        for dict_onboard in dictionary.values():
            if isinstance(dict_onboard, dict):
                if value in dict_onboard:
                    return {'partial': dict_onboard[value]}

    def get_sections_on_tree(self, from_section: Section):
        if from_section is None:
            return []
        tree = [from_section]
        tree += self.get_sections_inside_parent(self.get_all_sections(), from_section)
        return tree

    def get_sections_inside_parent(self, sections, parent: Section):
        if not sections:
            return
        items_inside_parent = []
        for section in sections:
            if section.parent_id == parent.id:
                items_inside_parent.append(section)
                parents = self.get_sections_children(self.get_all_sections(), section)
                children = self.get_sections_inside_parent(parents, section)
                if children:
                    items_inside_parent += children
        return items_inside_parent

    def export_case(self, section_id: int, tr_suite_cases: List[Case], raw_case: Case):
        tr_suite_case = next((sc for sc in tr_suite_cases
                              if sc.title == raw_case.title
                              and sc._custom_methods['custom_data_set'] == raw_case._custom_methods['custom_data_set'])
                             , None)
        if tr_suite_case:
            print('Upgrading Case ', tr_suite_case.title)
            self.client.cases.update_case(case_id=tr_suite_case.id, case=raw_case)
        else:
            print('Creating Case ', raw_case.title)
            self.client.cases.add_case(section_id=section_id, case=raw_case)

    def mount_scenarios(self, feature, scenario, tr_section, raw_custom_preconds):
        if 'examples' in scenario:
            build_raw = []
            datasets = self.make_table_dataset(scenario['examples'][0])
            i = 1
            scenario_name = scenario['name']
            for dataset in datasets:
                scenario['name'] = scenario_name + f" [{i}]"
                i += 1
                build_raw.append(self.build_case(
                    suite_id=None,
                    section_id=tr_section.id,
                    feature=feature,
                    scenario=scenario,
                    raw_custom_preconds=raw_custom_preconds,
                    raw_custom_data_set=dataset))
            return build_raw
        return [self.build_case(
            suite_id=None,
            section_id=tr_section.id,
            feature=feature,
            scenario=scenario,
            raw_custom_preconds=raw_custom_preconds,
            raw_custom_data_set=None)]

    def make_table_dataset(self, examples):
        result = []
        headers = "||"
        for header in examples['tableHeader']['cells']:
            headers += '|:' + header['value']
        for example in examples['tableBody']:
            items = "|"
            for col in example['cells']:
                items += '|' + col['value']
            table_done = headers + '\r\n' + items
            result.append(table_done)
        return result

    def build_case(self, suite_id: None, section_id: int, feature,
                   scenario, raw_custom_preconds, raw_custom_data_set=None) -> Case:
        priority_name = 'Medium'
        raw_priority = next((pr.id for pr in self.client.priorities.get_priorities() if pr.name == priority_name), None)
        raw_type = next((ct.id for ct in self.client.case_types.get_case_types() if ct.name == 'Functional'), None)
        raw_template = next((ct.id for ct in self.get_templates() if ct.name == 'BDD Steps'), None)
        raw_automatizable = 1 if any('automated' in tag['name'] for tag in scenario['tags']) or \
                                 next((True for tag in scenario['tags'] if tag['name'] == '@automatizable'),
                                      None) else 0
        raw_automated = 1 if any('automated' in tag['name'] for tag in scenario['tags']) else 0
        raw_custom_automation_type = 1 if any('mobile' in tag['name'] for tag in feature['feature']['tags']) else 0
        raw_refs = ''
        for tag in scenario['tags']:
            if tag['name'].__contains__('ref'):
                if raw_refs == '':
                    raw_refs = tag['name'].strip('@ref-')
                else:
                    raw_refs += ',' + tag['name'].strip('@ref-')
        raw_steps = [{'content': preconds, 'expected': ''} for preconds in raw_custom_preconds]
        raw_steps.extend([
            {
                'content': '**' + rs['keyword'].strip() + '** ' + rs['text'].strip() + self.add_datatable(rs),
                'expected': ''
            }
            for rs in scenario['steps']])
        raw_case = Case({
            'priority_id': raw_priority,
            'refs': raw_refs,
            'custom_tags': None,
            'suite_id': suite_id,
            'section_id': section_id,
            'title': scenario['name'],
            'type_id': raw_type,
            'template_id': raw_template,
            'custom_automatedtheacceptedtest': raw_automatizable,
            'custom_automation_type': raw_custom_automation_type,
            'custom_automated_testing': raw_automated,
            'custom_data_set': raw_custom_data_set,
            'custom_preconds': '\n'.join(str(rp) for rp in raw_custom_preconds),
            'custom_steps_separated': raw_steps
        })
        return raw_case

    def add_datatable(self, scenario_step):
        if 'argument' not in scenario_step:
            return ''
        table_rows = scenario_step['argument']['rows']
        table_header = table_rows.pop(0)
        headers = "\r\n||"
        for header in table_header['cells']:
            headers += '|:' + header['value']
        all_items = ''
        for table_row in table_rows:
            items = "\r\n|"
            for col in table_row['cells']:
                items += '|' + col['value']
            all_items += items
        datatable = headers + all_items
        return datatable
