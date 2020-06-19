import json

from pytest_testrail.helper import TestRailError
from pytest_testrail.model.result import Result
from pytest_testrail.tr_base_api import BaseTestRail


class ExportTestResults(BaseTestRail):

    def export_tests_results(self, project_variables: dict, scenarios_run: list, env_name: str):
        print('\nPublishing results')
        tr_active_plans = self.client.plans.get_plans(project_variables['id'], is_completed=0)
        tr_plan = next((plan for plan in tr_active_plans if plan.name == project_variables['test_plan']), None)
        if tr_plan is None:
            raise TestRailError('No Test Plan set with name %s for Automation Testing' % project_variables['test_plan'])
        tr_plan = self.client.plans.get_plan(tr_plan.id)
        tr_statuses = self.client.statuses.get_statuses()
        plan_entry_names = [plan_entry.name for plan_entry in tr_plan.entries]
        feature_names = scenarios_run.keys()
        if feature_names.__len__() > plan_entry_names.__len__() \
                or not set(feature_names).issubset(plan_entry_names):
            print('Not all test results will be published. Missing Test Suites: %s' % list(
                set(feature_names) - set(plan_entry_names)))
        for tr_plan_entry in tr_plan.entries:
            for tr_run in tr_plan_entry.runs:
                tr_results = []
                if tr_run.config == env_name and tr_run.name in scenarios_run:
                    for scenario_run in scenarios_run[tr_run.name]:
                        tr_tests = self.client.tests.get_tests(tr_run.id)
                        tr_test = next((test for test in tr_tests if test.title == scenario_run.name
                                        and (test.custom_methods['custom_data_set'] is None
                                             or ('custom_data_set' in test.custom_methods
                                                 and json.loads(
                                            test.custom_methods['custom_data_set']) == scenario_run.data_set))), None)

                        if tr_test is None:
                            print('Result for test %s not published to TestRail' % scenario_run.name)
                        else:
                            custom_step_results = []
                            custom_steps_separated = tr_test.custom_methods['custom_steps_separated']
                            passed = True
                            for scenario_step, tr_case_step in zip(scenario_run.steps, custom_steps_separated):
                                status_type = 'blocked' if not passed \
                                    else 'passed' if not scenario_step.failed \
                                    else 'failed' if scenario_step.failed \
                                    else 'untested'
                                if status_type == 'failed':
                                    passed = False
                                status_id = next((st.id for st in tr_statuses if st.name == status_type), None)
                                exception_message = scenario_run.exception_message \
                                    if status_type == 'failed' and hasattr(scenario_run, 'exception_message') \
                                    else ''
                                custom_step_results.append({
                                    'content': tr_case_step['content'],
                                    'expected': tr_case_step['expected'],
                                    'actual': exception_message,
                                    'status_id': status_id
                                })
                            status_type = 'failed' if scenario_run.failed else 'passed'
                            tr_result = Result({
                                'test_id': tr_test.id,
                                'status_id': next(st.id for st in tr_statuses if st.name == status_type),
                                'comment': '',
                                'custom_step_results': custom_step_results
                            })
                            tr_results.append(tr_result)
                if tr_results.__len__() != 0:
                    self.client.results.add_results(tr_run.id, tr_results)
        print('\nResults published')
