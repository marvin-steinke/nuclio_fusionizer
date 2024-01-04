from __future__ import annotations
from typing import TYPE_CHECKING
from loguru import logger
from copy import deepcopy
from importlib.resources import files
import os
import shutil
import yaml

if TYPE_CHECKING:
    from nuclio_fusionizer_server.mapper import FusionGroup


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

    def _merge_files(self, group: FusionGroup) -> None:
        """Merges multiple YAML configuration files.

        This method takes a Fusion Group and for each Task merges their YAML
        configuration file. This is used to combine the configurations of
        multiple Tasks into a single deployment.

        Args:
            group: The Fusion Group to merge files for.
        """
        merged_yaml = {}
        build_commands = ["pip install requests"]

        # Loop through input YAML and requirements.txt files
        for task in group.tasks:
            yaml_file = os.path.join(task.dir_path, "function.yaml")
            with open(yaml_file, "r") as file:
                data = yaml.safe_load(file)
                # Merge data from the current file into the merged_data dictionary
                if (
                    "spec" in data
                    and "build" in data["spec"]
                    and "commands" in data["spec"]["build"]
                ):
                    build_command = data["spec"]["build"]["commands"]
                    if build_command:
                        build_commands.extend(build_command)
                merged_yaml.update(data)

        # Add build commands
        if build_commands:
            merged_yaml["spec"]["build"]["commands"] = build_commands
        # Overwrite Fusion Group specific data
        merged_yaml["spec"]["handler"] = "dispatcher:handler"
        merged_yaml["spec"]["description"] = f"Fusion Group of Tasks {str(group)}"

        # Write the merged data to the output files
        with open(os.path.join(group.build_dir, "function.yaml"), "w") as file:
            yaml.dump(merged_yaml, file)

    def _create_handler(self, group: FusionGroup) -> None:
        """Creates a handler script for the fused tasks.

        Generates a Python script that imports and dispatches requests to the
        appropriate task based on the configuration of the FusionGroup.

        Args:
            group: The group of tasks to create a handler for.
        """
        # Dictionary to hold import statements for each task
        import_dict = {}
        for task in group.tasks:
            # Construct path to function.yaml and read its contents
            function_config = os.path.join(task.dir_path, "function.yaml")
            with open(function_config, "r") as file:
                data = yaml.safe_load(file)
                handler = data["spec"]["handler"].split(":")
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
    return dispatcher.run()
"""

        # Write handler script to a file
        with open(os.path.join(group.build_dir, "handler.py"), "w") as file:
            file.write(handler_str)

    def fuse(self, group: FusionGroup) -> None:
        """Performs the fusion process for a given group of tasks.

        This method takes a FusionGroup, prepares a new build directory for it,
        copies task files, merges their configurations, and creates a handler
        script.

        Args:
            group: The group of tasks to be fused.
        """
        # New build dir for group
        group_build_path = os.path.join(self.build_dir, group.name)
        if os.path.exists(group_build_path):
            shutil.rmtree(group_build_path)
        os.makedirs(group_build_path)
        group.build_dir = group_build_path
        logger.debug(
            f"Starting build process for Tasks {str(group)} in directory "
            f"{group_build_path}"
        )

        copy_group = deepcopy(group)
        # Copy all tasks to build dir
        for task in copy_group.tasks:
            new_dir_path = os.path.join(group_build_path, task.name)
            shutil.copytree(task.dir_path, new_dir_path)
            task.dir_path = new_dir_path

        # Merge all YAML files of tasks
        self._merge_files(copy_group)

        # Copy dispatcher.py lib to build dir
        shutil.copy(
            str(files("nuclio_fusionizer_server").joinpath("dispatcher.py")),
            group_build_path,
        )

        # Create __init__.py
        # with open(os.path.join(group_build_path, "__init__.py"), "w"):
        #    pass

        self._create_handler(copy_group)

        logger.debug(f"Contents of {group_build_path}: {os.listdir(group_build_path)}")
        logger.info(f"Successfully fused Tasks: {str(copy_group)}")
