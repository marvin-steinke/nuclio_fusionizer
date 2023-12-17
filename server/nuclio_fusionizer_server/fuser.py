from loguru import logger
from copy import deepcopy
from importlib.resources import files
import os
import shutil
import yaml

from nuclio_fusionizer_server.mapper import FusionGroup, Task


class Fuser:
    """Handles the fusion of multiple tasks into a single deployment.

    This class is responsible for combining multiple tasks into a single
    deployment package. It creates a build directory, merges configuration files,
    and generates a dispatcher script.

    Methods:
        _merge_yaml_files: Merges YAML configurations of tasks into a single file.
        _create_dispatcher: Creates a dispatcher script for the fused tasks.
        fuse: Fuses a group of tasks into a single deployment package.
    """

    def __init__(self) -> None:
        self.build_dir = "build"
        if not os.path.exists(self.build_dir):
            os.makedirs(self.build_dir)

    def _merge_yaml_files(
        self,
        tasks: list[Task],
        output_file: str,
    ) -> None:
        """Merges multiple YAML configuration files into a single file.

        This method takes a list of tasks, each with its own YAML configuration,
        and merges them into a single YAML file. This is used to combine the
        configurations of multiple tasks into a single deployment.

        Args:
            tasks: A list of Task objects to be merged.
            output_file: The path to the output YAML file.
        """
        merged_data = {}

        # Loop through input YAML files
        for task in tasks:
            yaml_file = os.path.join(task.dir_path, "function.yaml")
            with open(yaml_file, "r") as file:
                data = yaml.safe_load(file)
                # Merge data from the current file into the merged_data dictionary
                merged_data.update(data)

        # Overwrite Fusion Group specific data
        merged_data["spec"]["handler"] = "dispatcher:handler"
        task_names = ", ".join({task.name for task in tasks})
        merged_data["spec"]["description"] = f"Fusion Group of tasks {task_names}"

        # Write the merged data to the output file
        with open(output_file, "w") as file:
            yaml.dump(merged_data, file)

    def _create_handler(self, group: FusionGroup, group_build_path: str) -> None:
        """Creates a handler script for the fused tasks.

        Generates a Python script that imports and dispatches requests to the
        appropriate task based on the configuration of the FusionGroup.

        Args:
            group: The group of tasks to create a handler for.
            group_build_path: The build path for the Fusion Group.
        """
        # Dictionary to hold import statements for each task
        import_dict = {}
        for task in group.tasks:
            # Construct path to function.yaml and read its contents
            function_config = os.path.join(task.dir_path, "function.yaml")
            with open(function_config, "r") as file:
                data = yaml.safe_load(file)
                handler = data["handler"].split(":")
                # Create and store the import statement for this task
                import_str = (
                    f"from .{task.name}.{handler[0]} import {handler[1]} as {task.name}"
                )
                import_dict[task] = import_str

        # Combine all import statements into a single string
        import_statements = "\n".join(import_dict.values())
        task_dict_str = ", ".join(
            [f"'{task.name}': {task.name}" for task in group.tasks]
        )
        # Create handler script with import statements and handler function
        handler_str = f"""
{import_statements}
from .dispatcher import Dispatcher

def handler(context, event):
    tasks = {{{task_dict_str}}}
    dispatcher = Dispatcher(tasks, context, event)
    dispatcher.run()
"""

        # Write handler script to a file
        with open(os.path.join(group_build_path, "handler.py"), "w") as file:
            file.write(handler_str)

    def fuse(self, group: FusionGroup) -> None:
        """Performs the fusion process for a given group of tasks.

        This method takes a FusionGroup, prepares a new build directory for it,
        copies task files, merges their configurations, and creates a handler
        script.

        Args:
            group: The group of tasks to be fused.
        """
        group = deepcopy(group)
        # New build dir for group
        group_name = "".join([task.name for task in group.tasks])
        group_build_path = os.path.join(self.build_dir, group_name)
        if os.path.exists(group_build_path):
            shutil.rmtree(group_build_path)
        os.makedirs(group_build_path)

        # Copy all tasks to build dir
        for task in group.tasks:
            new_dir_path = os.path.join(group_build_path, task.name)
            shutil.copytree(task.dir_path, new_dir_path)
            task.dir_path = new_dir_path

        # Merge all YAML files of tasks
        self._merge_yaml_files(
            group.tasks,
            os.path.join(group_build_path, "function.yaml"),
        )

        # Copy dispatcher.py lib to build dir
        shutil.copy(
            str(files("nuclio_fusionizer_server").joinpath("dispatcher.py")),
            group_build_path,
        )

        # Create __init__.py
        with open(os.path.join(group_build_path, "__init__.py"), "w"):
            pass

        self._create_handler(group, group_build_path)

        task_list_str = ", ".join([task.name for task in group.tasks])
        logger.info(f"Successfully fused Tasks: {task_list_str}")
