from typing import Callable, Any
from urllib3.util.retry import Retry as Retry
from urllib.parse import urljoin
from requests.adapters import HTTPAdapter
from requests.models import Response
import requests
import os


class FusionizerAdapter(HTTPAdapter):
    """Intercepts HTTP requests to the Fusionizer Server.

    Inherits the HTTPAdapter class and overrides the send method to allow
    for customized responses.

    Args:
        tasks: A dictionary of tasks that the client can call.
        fusionizer_url: The base URL for the Fusionizer service.
        pool_connections: The number of connections to cache. Defaults to 10.
        pool_maxsize: The maximum number of connections to save in the pool.
            Defaults to 10.
        max_retries: The number of maximum retries for the requests. Can either
            be an integer, Retry object, or None. Defaults to 0.
        pool_block: Whether the connection pool should block when no free
            connections are available. Defaults to False.
    
    Methods:
        send: Sends a prepared request and returns the response.
    """
    def __init__(
        self,
        tasks: dict[str, Callable],
        fusionizer_url: str,
        pool_connections: int = 10,
        pool_maxsize: int = 10,
        max_retries: Retry | int | None = 0,
        pool_block: bool = False,
    ) -> None:
        super().__init__(pool_connections, pool_maxsize, max_retries, pool_block)
        self.tasks = tasks
        self.fusionizer_url = fusionizer_url

    def send(self, request, **kwargs):
        """Sends a prepared request and returns the response.

        Check if the request URL starts with the fusionizer invocation url, if
        it does, then it returns the call to the specified local handler,
        otherwise, it sends the request through the parent class's send method.

        Args:
            request: The Request object to send.
            **kwargs: Optional arguments that request takes.
        
        Returns:
            Response object.
        """
        invoke_url = urljoin(self.fusionizer_url, "/invoke/")
        if request.url.startswith(invoke_url):
            response = Response()
            response.status_code = 200
            # TODO return local function
            # maybe this is more complicated as we call the function via the
            # invoke fastpi access point
            response._content = b"Static response for specific URL"
            return response
        return super(FusionizerAdapter, self).send(request, **kwargs)


class Dispatcher:
    def __init__(self, tasks: dict[str, Callable], context: Any, event: Any) -> None:
        self.tasks = tasks
        self.context = context
        self.event = event
        self._intercept_http()

    def _intercept_http(self) -> None:
        """Intercepts HTTP requests by replacing the default session.

        This method creates a new FusionizerAdapter with the tasks and
        Fusionizer server address, and replaces the requests' default session
        with a custom session that utilizes this adapter. The adapter globaly
        mounts to all http and https addresses.
        
        Raises:
            ValueError: If no value for the 'Fusionizer-Server-Address' field
                was provided in the header.
        """
        fusionizer_server_addr = self.event.trigger.header.get(
            "Fusionizer-Server-Address"
        )
        if not fusionizer_server_addr:
            raise ValueError(
                "No value for the 'Fusionizer-Server-Address' field was provided in "
                "the Header."
            )
        adapter = FusionizerAdapter(self.tasks, fusionizer_server_addr)
        # Mount the custom adapter globally
        session = requests.Session()
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        # Replace the requests' default session with our custom session
        requests.Session = lambda: session

    def _choose_handler(self) -> Callable:
        """Selects the right task handler based on the 'Task-Name' field.
        
        This method retrieves the task name from the event header and checks if
        such a task exists in the tasks dictionary. If it does, it returns the
        corresponding task handler function.

        Returns:
            The chosen task handler function.
            
        Raises:
            ValueError: If no value for the 'Task-Name' field was provided in
                the header.
            ValueError: If the task name is not handled by the given Fusion
                Group.
        """
        task_name = self.event.trigger.headers.get("Function-Name")
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
            The result returned by the chosen task handler function.
        """
        handler = self._choose_handler()
        result = handler()
        return result
