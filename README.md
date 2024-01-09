# Nuclio Fusionizer Server

## Overview

The Nuclio Fusionizer is a server for handling Task and Fusion Group operations
in a serverless computing environment using Nuclio. It exposes an API for
deploying, deleting, retrieving information, and invoking Nuclio functions that
represent both individual Tasks and groups of Tasks that are fused to optimize
resource usage and performance.

## Core Components

The server comprises several components working together to achieve its functionality:

- **Nuctl Interface (`nuclio_interface.py`)**: A Python abstraction layer for
Nuclio's CLI tool `nuctl`, handling deployment, deletion, invocation, and
information retrieval of Nuclio functions.

- **Fuser (`fuser.py`)**: Takes care of the fusion process, merging multiple
Tasks into a single Nuclio function deployment. It combines Tasks into a Fusion
Group, generates a unified configuration and creates a dispatch mechanism.

- **Mapper (`mapper.py`)**: Manages the representation and operations on Fusion
Groups, facilitating the mapping between Tasks and their corresponding fusion
groups.

- **ApiServer (`api_server.py`)**: FastAPI based server that provides an HTTP
interface for user interaction with the fusionizer system. It defines endpoints
for Task operations and utilizes the `Mapper` and `Nuctl` objects.

- **Optimizers (`optimizer.py`)**: Contains abstract and concrete classes for
optimization strategies that periodically update the fusion setup based on
various conditions or configurations. Implementation includes a static optimizer
that changes setup based on a predefined schedule.

- **Dispatcher (`dispatcher.py`)**: Intercepts HTTP requests and dispatches them
to the appropriate handlers within the fusion context.

## Usage

To deploy a Task, you need to zip your Task files and then upload them via the
API. Configure your Function [like instructed by
Nuclio](https://nuclio.io/docs/latest/reference/function-configuration/function-configuration-reference/).
Your Task files should be structured like this:

```
.
├── function.yaml
├── your_handler.py
└── your_local_dependencies
```

ZIP compress your Task files:
```
zip Task.zip -r .
```

### API
1. To deploy a new Task or redeploy an existing one:
```
curl -X PUT http://localhost:8000/{task_name} \
     -H "Content-Type: multipart/form-data" \
     -F "@task.zip"
```

2. To delete an existing Task:
```
curl -X DELETE http://localhost:8000/{task_name}
```

3. To get information about a Task:
```
curl -X GET http://localhost:8000/{task_name}
```

4. To invoke a Task:
```
curl -X POST http://localhost:8000/{task_name} \
     -H "Content-Type: application/json" \
     -d '{"arg1":"value1", "arg2":"value2"}'
```