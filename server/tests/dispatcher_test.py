import unittest
import json
from unittest.mock import Mock
from requests import PreparedRequest, Response

from nuclio_fusionizer_server.dispatcher import FusionizerAdapter, Dispatcher


class FusionizerAdapterTest(unittest.TestCase):
    def setUp(self):
        self.tasks = {"test_task": Mock(return_value="task was run")}
        self.fusionizer_url = "http://test.url"
        self.adapter = FusionizerAdapter(self.tasks, self.fusionizer_url)

    def test_send_no_url(self):
        request = PreparedRequest()
        self.assertRaises(ValueError, self.adapter.send, request)

    def test_send_fusionizer_task_no_body(self):
        request = PreparedRequest()
        request.url = f"{self.fusionizer_url}/test_task"
        self.assertRaises(ValueError, self.adapter.send, request)

    def test_send_fusionizer_task_valid_body(self):
        request = PreparedRequest()
        request.url = f"{self.fusionizer_url}/test_task"
        request.body = json.dumps({"key": "value"})
        response = self.adapter.send(request)
        self.assertEqual(response.status_code, 200)

    def test_send_fusionizer_task_invalid_body(self):
        request = PreparedRequest()
        request.url = f"{self.fusionizer_url}/test_task"
        request.body = "invalid JSON"
        response = self.adapter.send(request)
        self.assertEqual(response.status_code, 400)

    def test_send_regular_request(self):
        request = PreparedRequest()
        request.url = "http://other.url"
        request.body = json.dumps({"key": "value"})
        mock_response = Response()
        mock_response.status_code = 200
        self.adapter.send = Mock(return_value=mock_response)
        response = self.adapter.send(request)
        self.assertEqual(response.status_code, 200)


class TestDispatcher(unittest.TestCase):
    def setUp(self):
        self.tasks = {"task1": lambda: "result1", "task2": lambda: "result2"}
        self.context = Mock()
        self.event = Mock()
        self.dispatcher = Dispatcher(self.tasks, self.context, self.event)

    def test_intercept_http(self):
        self.event.trigger.header.get.return_value = "http://localhost"
        try:
            self.dispatcher._intercept_http()
        except Exception as e:
            self.fail(f"Unexpected exception raised: {e}")

    def test_intercept_http_no_addr(self):
        self.event.trigger.header.get.return_value = None
        with self.assertRaises(ValueError):
            self.dispatcher._intercept_http()

    def test_choose_handler(self):
        self.event.trigger.headers.get.return_value = "task1"
        try:
            result = self.dispatcher._choose_handler()
            self.assertEqual(result(), "result1")
        except Exception as e:
            self.fail(f"Unexpected exception raised: {e}")

    def test_choose_handler_invalid_task(self):
        self.event.trigger.headers.get.return_value = "invalid_task"
        with self.assertRaises(ValueError):
            self.dispatcher._choose_handler()

    def test_run(self):
        self.event.trigger.headers.get.return_value = "task1"
        try:
            result = self.dispatcher.run()
            self.assertEqual(result, "result1")
        except Exception as e:
            self.fail(f"Unexpected exception raised: {e}")


if __name__ == "__main__":
    unittest.main()
