"""
TestRail util integration
"""
import unicodedata

from pytest_testrail.model.section import Section
from pytest_testrail.testrail_api import TestRailAPI


class BaseTestRail:

    def __init__(self, project_name):
        self.client = self.get_tr_client()
        self.project = self.get_project_by_name(project_name)

    def get_tr_client(self):
        tr_client = TestRailAPI()
        if not self.is_connected(tr_client):
            raise Exception("TestRail User or Password incorrect! Please verify.")
        return tr_client

    @staticmethod
    def is_connected(client):
        return client.projects.get_projects()[0]._content != 'error'

    def close_connection(self):
        self.client._Session__session.close()

    def get_project_by_name(self, project_name):
        projects = self.client.projects.get_projects()
        for project in projects:
            if project.name == project_name:
                return project
        raise Exception('Project name not found: ' + project_name)

    def get_templates(self):
        return self.client.templates.get_templates(self.project.id)

    def get_all_sections(self):
        return self.client.sections.get_sections(self.project.id, suite_id=None)

    def get_project_by_tag(self, feature):
        subproj = 'appvendedor' if any('appvendedor' in tag['name'] for tag in feature['feature']['tags']) else None
        if not subproj:
            subproj = 'portalweb' if any('portalweb' in tag['name'] for tag in feature['feature']['tags']) else None
        if not subproj:
            subproj = 'b2badmin' if any('b2badmin' in tag['name'] for tag in feature['feature']['tags']) else None
        if not subproj:
            subproj = 'pwa' if any('pwa' in tag['name'] for tag in feature['feature']['tags']) else None

        if subproj:
            return subproj
        else:
            raise Exception('Please put @project tag on feature')

    def create_section(self, section_name, parent_id):
        section_model = Section({'description': '', 'name': section_name, 'parent_id': parent_id})
        return self.client.sections.add_section(self.project.id, section_model)

    def get_section_by_name(self, sections, section_name: str) -> Section:
        for section in sections:
            if section.name == section_name:
                return section

    def get_root_sections(self):
        root_sections = []
        for section in self.get_all_sections():
            if section.parent_id is None:
                root_sections.append(section)
        return root_sections

    def get_sections_children(self, sections, parent: Section):
        items_same_parent = []
        for section in sections:
            if section.parent_id == parent.id:
                items_same_parent.append(section)
        return items_same_parent

    def get_cases_by_section(self, cases, section: Section):
        cases_inside = []
        for case in cases:
            if case.section_id == section.id:
                cases_inside.append(case)
        return cases_inside

    def remove_accents(self, string: str):
        string = unicodedata.normalize('NFD', string).encode('ascii', 'ignore').decode("utf-8")
        return str(string)
