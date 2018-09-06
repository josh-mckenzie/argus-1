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

from src.jira_manager import JiraManager
from src.team_manager import TeamManager
from src.utils import ConfigError


class StaticSystems:
    """
    Static container of the various objects with singleton use in the application.
    """
    jira_manager = None
    team_manager = None
    jenkins_manager = None

    @staticmethod
    def initialize()-> None:
        try:
            StaticSystems.team_manager = TeamManager.from_file()
        except ConfigError as ce:
            print('ConfigError: {}. Initializing empty JiraManager'.format(ce))
            StaticSystems.team_manager = TeamManager()
        StaticSystems.jira_manager = JiraManager(StaticSystems.team_manager)
