# Copyright 2018 DataStax, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import re

from typing import Dict

from src.jira_connection import JiraConnection
from src.jira_issue import JiraIssue
from src.jira_project import JiraProject
from src.utils import argus_debug


class CSVCleaner:

    """
    Simple logic to take csv inputs, compare 2nd col against known projects, and not write out any lines that are resolved.
    Also fills out assignee, reviewer, and status for tickets based on current snapshot in JIRA
    """

    # The csv format should follow the below for 0-indexed column names.
    link = 0
    ticket = 1
    summary = 2
    bucket = 3  # dead item on improvements / new features
    assignees = 4
    reviewers = 5
    status = 6

    def __init__(self, jira_connections: Dict[str, JiraConnection], jira_projects: Dict[str, JiraProject]) -> None:
        self._jira_connections = jira_connections
        self._jira_projects = jira_projects

    def process(self, in_file_name: str) -> None:
        """
        Reads input csv file, checking known jira connections for all tickets listed in 2nd column. Skips writing back
        all rows for closed tickets.
        :param in_file_name: input file to process
        """
        argus_debug('Updating all cached jira projects before cleaning')
        # Update jira projects before querying
        for name, jp in self._jira_projects.items():
            jp.refresh()

        with open(in_file_name, 'r') as input_file:
            for line in input_file:
                cleanline = line.rstrip()
                sa = cleanline.split(',')

                # Pass through headers
                if len(sa) <= 2:
                    print(line)
                    continue

                ticket_name = sa[CSVCleaner.ticket]

                if '-' not in ticket_name:
                    print('Error on line. Expected hyphen in field 2, didn\'t get one. Line: [{}]'.format(cleanline))
                    continue

                project_name = JiraIssue.get_project_from_ticket(ticket_name)
                jira_project = self._jira_projects[project_name]
                jira_issue = jira_project.get_issue(ticket_name)

                # If we didn't find the issue, log and move on. We should know it exists at least.
                if jira_issue is None:
                    print('Error on line. Found project but could not find ticket. Project: {}. Ticket: {}'.format(project_name, ticket_name))

                # Scan and find jira_connection this is on
                jira_connection = None
                for name, conn in self._jira_connections.items():
                    if conn.contains_project(project_name):
                        jira_connection = conn
                        break

                if jira_connection is None:
                    # If we somehow have a JiraIssue and JiraProject but can't find the JiraConnection... something is wrong.
                    error_msg = 'No JiraConnection for key/project combo. This is a bug. Key: {}. Project: {}'.format(jira_issue.issue_key, jira_project.project_name)
                    print(error_msg)
                    raise Exception(error_msg)

                # Update assignee, reviewer, and status
                if jira_issue.issue_key == 'CASSANDRA-11479':
                    reviewers = jira_issue.reviewers(jira_connection)
                    if reviewers is not None:
                        for r in reviewers:
                            print('FOUND REVIEWER: {}'.format(r))
                        exit(0)
                    else:
                        print('Reviewers is none. Oops.')
                continue
                if jira_issue.is_open:
                    print('{},{},{},{},{},{},{}'.format(
                        sa[CSVCleaner.link],
                        sa[CSVCleaner.ticket],
                        sa[CSVCleaner.summary],
                        sa[CSVCleaner.bucket],
                        jira_issue.assignee,
                        jira_issue.reviewer(jira_connection),
                        jira_issue.status))
                # DEBUG: REMOVE PRE MERGE
                else:
                    print('FOUND CLOSED TICKET: {}. Status: {}'.format(jira_issue.issue_key, jira_issue.status))


