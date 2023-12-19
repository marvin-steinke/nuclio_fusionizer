from unittest.mock import patch, mock_open, call
import os
import tempfile
import shutil
import yaml
from collections import OrderedDict
import unittest

from nuclio_fusionizer_server.fuser import Fuser
from nuclio_fusionizer_server.mapper import FusionGroup, Task


class TestFuser(unittest.TestCase):
    def setUp(self):
        self.fuser = Fuser()
        self.task1 = Task("task1", "/task1/dir/path")
        self.task2 = Task("task2", "/task2/dir/path")
        self.group = FusionGroup([self.task1, self.task2])

        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_merge_yaml_files(self):
        output_file = os.path.join(self.temp_dir, "output.yaml")

        yaml_file1 = os.path.join(self.temp_dir, "file1.yaml")
        yaml_file2 = os.path.join(self.temp_dir, "file2.yaml")

        data1 = OrderedDict([("file1Key", "file1Value")])
        data2 = OrderedDict([("file2Key", "file2Value")])

        with open(yaml_file1, "w") as outfile:
            yaml.dump(data1, outfile)
        with open(yaml_file2, "w") as outfile:
            yaml.dump(data2, outfile)

        task1 = Task("task1", self.temp_dir)
        task2 = Task("task2", self.temp_dir)

        self.fuser._merge_yaml_files([task1, task2], output_file)

        with open(output_file, "r") as file:
            merged_data = yaml.safe_load(file)

        self.assertEqual(
            merged_data,
            {
                **data1,
                **data2,
                "spec": {
                    "description": "Fusion Group of tasks task2, task1",
                    "handler": "dispatcher:handler",
                },
            },
        )

    def test_create_handler(self):
        group_build_path = os.path.join(self.temp_dir, "build")
        os.makedirs(group_build_path)

        with patch("builtins.open", new=mock_open()) as mock_file:
            self.fuser._create_handler(self.group, group_build_path)

        calls = [
            call(os.path.join(task.dir_path, "function.yaml"), "r")
            for task in self.group.tasks
        ]
        mock_file.assert_has_calls(calls, any_order=True)

        handler_file_path = os.path.join(group_build_path, "handler.py")
        mock_file.assert_any_call(handler_file_path, "w")

        assert mock_file().write.call_count == 1
        handler_content = mock_file().write.call_args[0][0]
        for task in self.group.tasks:
            assert f"from .{task.name}" in handler_content

    def test_fuse(self):
        self.fuser.build_dir = self.temp_dir
        self.fuser.fuse(self.group)

        group_build_path = os.path.join(self.temp_dir, "task1task2")

        # Assert build directory was created
        self.assertTrue(os.path.exists(group_build_path))

        # Assert handler script was created
        self.assertTrue(os.path.exists(os.path.join(group_build_path, "handler.py")))


if __name__ == "__main__":
    unittest.main()
