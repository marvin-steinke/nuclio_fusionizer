# Nuclio Fusionizer Server

The Nuclio Fusionizer Server is a project that enables the fusion of specific
Tasks into a single Nuclio Function. This function can then be deployed to the
open-source serverless computing platform, Nuclio. 

The project is informed by the principles outlined in the [Fusionize++ paper by
Schirmer et al.](https://arxiv.org/abs/2311.04875), which discusses the benefits
and disadvantages of the Function-as-a-Service (FaaS) model in serverless
computing. One key take away from the paper, and the guiding principle of this
project, is the optimization of operational flexibility and cost-effectiveness
by fusing application code into an optimized multi-function composition.

## Key Features

- **Fusion of Tasks**: Through Nuclio Fusionizer, different Tasks can be fused
into a singular Nuclio function, thereby streamlining function calls and
execution flow within an application.

- **Elimination of Invocation Overhead, Cold starts, and Double Billing**:
Because Tasks operate within the same memory, invocation overheads, cold starts
and double billing associated with individual function calls are eliminated.

- **Customized Optimization**: An additional feature of the Nuclio Fusionizer is
the capability to customize the optimization process for the fusion Tasks with
custom Optimizers, providing developers with the flexibility they require to set
up their systems as needed.

## Architecture

![fusionizer](https://github.com/marvin-steinke/nuclio_fusionizer/assets/48684343/72ad1f9d-9ea2-4fce-a620-4d245649ef98)

- **nuctl Interface (`nuclio_interface.py`)**: A Python abstraction layer for
Nuclio's CLI tool `nuctl`, handling deployment, deletion, invocation, and
information retrieval of Nuclio functions.

- **Task Fuser (`fuser.py`)**: Takes care of the fusion process, merging
multiple Tasks into a single Nuclio function deployment. It combines Tasks into
a Fusion Group, generates a unified configuration and creates a dispatch
mechanism.

- **Task Manager/Mapper (`mapper.py`)**: Manages the representation and
operations on Fusion Groups, facilitating the mapping between Tasks and their
corresponding fusion groups.

- **FastApi Server (`api_server.py`)**: FastAPI based server that provides an HTTP
interface for user interaction with the fusionizer system. It defines endpoints
for Task operations and utilizes the `Mapper` and `Nuctl` objects.

- **Optimizers (`optimizer.py`)**: Contains abstract and concrete classes for
optimization strategies that periodically update the fusion setup based on
various conditions or configurations. Implementation includes a static optimizer
that changes setup based on a predefined schedule.

- **Dispatcher (`dispatcher.py`)**: In the Nuclio Function, HTTP requests are
intercepted and dispatched to the appropriate handlers within the fusion
context.

## Installation

```bash
pip install nuclio-fusionizer
```

## Usage

### Server

TODO

### Deploying and Invoking Tasks

Set up your Tasks [as instructed by
nuclio](https://docs.nuclio.io/en/stable/tasks/deploying-functions.html) with
the addition of the `requests_session` parameter in your handler function. This
custom session will intercept any invcocation requests to other Tasks if they
reside within the same nuclio function and invoke them locally. The address of
the Fusionizer server is supplied in the event headers:

```python
def handler(context, event, requests_session):
    fusionizer_address = event.headers["Fusionizer-Server-Address"]
    # invoke other Task
    url = f"http://{fusionizer_address}:8000/<other Task>"
    headers = {"Content-Type": "application/json"}
    data = {"value1": 5, "value2": 3}
    response = requests_session.post(url, headers=headers, json=data))
    return response.text
```
Other Task:
```python
def handler(context, event, requests_session):
    return event.body["value1"] + event.body["value2"]
```

 To deploy a Task, you need to zip your Task files and then upload them via the
 API.  Your Task files should be structured like this:

```bash
.
├── function.yaml 
├── your_handler.py
└── your_local_dependencies
```

ZIP compress your Task files from within the Tasks dir:
```bash
zip task.zip -r .
```

### API
1. To deploy a new Task or redeploy an existing one:
```bash
curl -X PUT http://localhost:8000/<task_name> \
     -H "Content-Type: multipart/form-data" \
     -F "zip_file=@<task>.zip"
```

2. To delete an existing Task:
```bash
curl -X DELETE http://localhost:8000/<task_name>
```

3. To get information about a Task:
```bash
curl -X GET http://localhost:8000/<task_name>
```

4. To invoke a Task:
```bash
curl -X POST http://localhost:8000/<task_name> \
     -H "Content-Type: application/json" \
     -d '{"arg1": "value1", "arg2": 42}'
```
