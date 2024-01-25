from __future__ import annotations
from typing import Callable, Any
from urllib3.util.retry import Retry as Retry
from urllib.parse import urlparse
from requests.adapters import HTTPAdapter
from requests.models import Response, PreparedRequest
import requests
import json
import os


class FusionizerAdapter(HTTPAdapter):
    """Intercepts HTTP requests to the Fusionizer Server.

    Inherits the HTTPAdapter class and overrides the send method to allow
    for customized responses.

    Args:
        tasks: A dictionary of Tasks that the client can call.
        fusionizer_url: The base URL for the Fusionizer service.
        context: Nuclio context to be passed on to a locally invoked function.
        event: Nuclio event to be passed on to a locally invoked function.
        session: Custom requests session with this adapter mounted.

    Methods:
        send: Sends a prepared request and returns the response.
    """

    def __init__(
        self,
        tasks: dict[str, Callable],
        fusionizer_url: str,
        nuclio_context: Any,
        nuclio_event: Any,
        requests_session: requests.Session,
    ) -> None:
        super().__init__()
        self.tasks = tasks
        self.fusionizer_url = fusionizer_url
        self.nuclio_context = nuclio_context
        self.nuclio_event = nuclio_event
        self.requests_session = requests_session

    def send(self, request: PreparedRequest, **kwargs):
        """Sends a PreparedRequest.

        If the PreparedRequest object is for one of the Tasks handled by this
        adapter, the Task is invoked locally and the result is returned as a
        Response. Otherwise, the PreparedRequest is handled as a regular
        request.

        Args:
            request: The PreparedRequest object to be sent. If the object is for
                one of the Tasks handled by this adapter, the URL must point to the
                adapter's fusionizer server, and the body must be a JSON-compliant
                string that can be loaded as kwargs for the Task.
            **kwargs: (optional) Keyword arguments to be used in the regular
                *request (if the PreparedRequest is not for
                one of the Tasks handled by this adapter).

        Returns:
            The Response to the request. If the PreparedRequest was for one of
            the Tasks handled by this adapter, the content of the Response is
            the result of the Task invocation, and the status code is 200. If
            the body of the PreparedRequest was not JSON-compliant, the content
            is 'Invalid JSON format' and the status code is 400.  Otherwise, the
            Response is the result of handling the PreparedRequest as a regular
            request.

        Raises:
            ValueError: If the PreparedRequest object does not have an URL, or
                if it is for one of the Tasks handled by this adapter and does not
                have a body.
        """
        if not request.url:
            raise ValueError("PreparedRequest object is missing url.")
        subaddrs = urlparse(request.url).path.strip("/")
        base_url = request.url.replace("http://", "").replace("https://", "")
        if (
            request.method == "POST"
            # If the base url is our fusionizer server
            and base_url.startswith(self.fusionizer_url)
            # and is only called with one subaddr (=function)
            and subaddrs
            and "/" not in subaddrs
            # and the function is in this Fusion Group
            and subaddrs in self.tasks
        ):  # -> invoke locally
            if not request.body:
                raise ValueError("PreparedRequest object is missing a body.")
            response = Response()
            try:
                self.nuclio_event.body = json.loads(request.body)
                content = str(
                    self.tasks[subaddrs](
                        self.nuclio_context, self.nuclio_event, self.requests_session
                    )
                ).encode("utf-8")
                status_code = 200
            except ValueError as e:
                status_code = 400
                content = str(e).encode("utf-8")

            response.status_code = status_code
            response._content = content
            return response
        # If not, handle as a regular request
        return super().send(request, **kwargs)


class Dispatcher:
    def __init__(self, tasks: dict[str, Callable], context: Any, event: Any) -> None:
        self.tasks = tasks
        self.context = context
        self.event = event
        self.session = requests.Session()
        self._intercept_http()

    def _intercept_http(self) -> None:
        """Intercepts HTTP requests by setting the session for the Tasks.

        This method creates a new FusionizerAdapter with the Tasks and
        Fusionizer server address, and replaces the requests' default session
        with a custom session that utilizes this adapter. The adapter globaly
        mounts to all http and https addresses.

        Raises:
            ValueError: If no value for the 'Fusionizer-Server-Address' field
                was provided in the header.
        """
        fusionizer_server_addr = self.event.headers.get("Fusionizer-Server-Address")
        if not fusionizer_server_addr:
            raise ValueError(
                "No value for the 'Fusionizer-Server-Address' field was provided in "
                "the Header."
            )
        adapter = FusionizerAdapter(
            self.tasks, fusionizer_server_addr, self.context, self.event, self.session
        )
        # Mount the custom adapter globally
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def _choose_handler(self) -> Callable:
        """Selects the right Task handler based on the 'Task-Name' field.

        This method retrieves the Task name from the event header and checks if
        such a Task exists in the Tasks dictionary. If it does, it returns the
        corresponding Task handler function.

        Returns:
            The chosen Task handler function.

        Raises:
            ValueError: If no value for the 'Task-Name' field was provided in
                the header.
            ValueError: If the Task name is not handled by the given Fusion
                Group.
        """
        task_name = self.event.headers.get("Task-Name")
        if not task_name:
            raise ValueError(
                "No value for the 'Task-Name' field was provided in the Header."
            )
        if task_name not in self.tasks:
            fusion_group_name = os.getenv("NUCLIO_FUNCTION_NAME")
            raise ValueError(
                f"The Task '{task_name}' is not handled by the Fusion Group "
                f"'{fusion_group_name}'"
            )
        return self.tasks[task_name]

    def run(self) -> Any:
        """Runs the chosen handler and returns its result.

        This method first chooses the appropriate handler using
        _choose_handler(), then calls the chosen handler function and returns
        its result.

        Returns:
            The result returned by the chosen Task handler function.
        """
        handler = self._choose_handler()
        result = handler(self.context, self.event, self.session)
        return result
