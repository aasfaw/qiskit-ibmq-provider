# -*- coding: utf-8 -*-

# This code is part of Qiskit.
#
# (C) Copyright IBM 2017, 2018.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

"""Model for representing IBM Q credentials."""

import re

from typing import Dict, Tuple, Optional, Any
from requests_ntlm import HttpNtlmAuth

from .hubgroupproject import HubGroupProject


# Regex that matches a IBMQ URL with hub information
REGEX_IBMQ_HUBS = (
    '(?P<prefix>http[s]://.+/api)'
    '/Hubs/(?P<hub>[^/]+)/Groups/(?P<group>[^/]+)/Projects/(?P<project>[^/]+)'
)

# Template for creating an IBMQ URL with hub information
TEMPLATE_IBMQ_HUBS = '{prefix}/Network/{hub}/Groups/{group}/Projects/{project}'


class Credentials:
    """IBM Q account credentials.

    Note that, by convention, two credentials that have the same hub, group
    and project (regardless of other attributes) are considered equivalent.
    The `unique_id()` returns the unique identifier.
    """

    def __init__(
            self,
            token: str,
            url: str,
            websockets_url: Optional[str] = None,
            hub: Optional[str] = None,
            group: Optional[str] = None,
            project: Optional[str] = None,
            proxies: Optional[Dict] = None,
            verify: bool = True
    ) -> None:
        """Return new set of credentials.

        Args:
            token (str): Quantum Experience or IBMQ API token.
            url (str): URL for Quantum Experience or IBMQ.
            websockets_url (str): URL for websocket server.
            hub (str): the hub used for IBMQ.
            group (str): the group used for IBMQ.
            project (str): the project used for IBMQ.
            proxies (dict): proxy configuration for the API.
            verify (bool): if False, ignores SSL certificates errors

        Note:
            `hub`, `group` and `project` are stored as attributes for
            convenience, but their usage in the API is deprecated. The new-style
            URLs (that includes these parameters as part of the url string, and
            is automatically set during instantiation) should be used when
            communicating with the API.
        """
        self.token = token
        (self.url, self.base_url,
         self.hub, self.group, self.project) = _unify_ibmq_url(
             url, hub, group, project)
        self.websockets_url = websockets_url
        self.proxies = proxies or {}
        self.verify = verify

    def is_ibmq(self) -> bool:
        """Return whether the credentials represent a IBMQ account."""
        return all([self.hub, self.group, self.project])

    def __eq__(self, other: object) -> bool:
        return self.__dict__ == other.__dict__

    def unique_id(self) -> HubGroupProject:
        """Return a value that uniquely identifies these credentials.

        By convention, we assume (hub, group, project) is always unique.

        Returns:
            HubGroupProject: the (hub, group, project) tuple.
        """
        return HubGroupProject(self.hub, self.group, self.project)

    def connection_parameters(self) -> Dict[str, Any]:
        """Return a dict of kwargs in the format expected by `requests`.

        Returns:
            dict: a dict with connection-related arguments in the format
                expected by `requests`. The following keys can be present:
                `proxies`, `verify`, `auth`.
        """
        request_kwargs = {
            'verify': self.verify
        }

        if self.proxies:
            if 'urls' in self.proxies:
                request_kwargs['proxies'] = self.proxies['urls']

            if 'username_ntlm' in self.proxies and 'password_ntlm' in self.proxies:
                request_kwargs['auth'] = HttpNtlmAuth(
                    self.proxies['username_ntlm'],
                    self.proxies['password_ntlm']
                )

        return request_kwargs


def _unify_ibmq_url(
        url: str,
        hub: Optional[str] = None,
        group: Optional[str] = None,
        project: Optional[str] = None
) -> Tuple[str, str, Optional[str], Optional[str], Optional[str]]:
    """Return a new-style set of credential values (url and hub parameters).

    Args:
        url (str): URL for Quantum Experience or IBM Q.
        hub (str): the hub used for IBM Q.
        group (str): the group used for IBM Q.
        project (str): the project used for IBM Q.

    Returns:
        tuple[url, base_url, hub, group, token]:
            * url (str): new-style Quantum Experience or IBM Q URL (the hub,
                group and project included in the URL).
            * base_url (str): base URL for the API, without hub/group/project.
            * hub (str): the hub used for IBM Q.
            * group (str): the group used for IBM Q.
            * project (str): the project used for IBM Q.
    """
    # Check if the URL is "new style", and retrieve embedded parameters from it.
    regex_match = re.match(REGEX_IBMQ_HUBS, url, re.IGNORECASE)
    base_url = url
    if regex_match:
        base_url, hub, group, project = regex_match.groups()
    else:
        if hub and group and project:
            # Assume it is an IBMQ URL, and update the url.
            url = TEMPLATE_IBMQ_HUBS.format(prefix=url, hub=hub, group=group,
                                            project=project)
        else:
            # Cleanup the hub, group and project, without modifying the url.
            hub = group = project = None

    return url, base_url, hub, group, project
