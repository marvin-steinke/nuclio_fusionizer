# Nuclio Fusionizer Server

The Nuclio Fusionizer Server is a project that enables the fusion of specific
tasks into a single Nuclio Function. This function can then be deployed to the
open-source serverless computing platform, Nuclio. 

The project is informed by the principles outlined in the Fusionize++ paper,
which discusses the benefits and disadvantages of the Function-as-a-Service
(FaaS) model in serverless computing. One key take away from the paper, and the
guiding principle of this project, is the optimization of operational
flexibility and cost-effectiveness by fusing application code into an optimized
multi-function composition.

## Key Features

- **Fusion of Tasks**: Through Nuclio Fusionizer, different tasks can be fused
into a singular Nuclio function, thereby streamlining function calls and
execution flow within an application.

- **Elimination of Invocation Overhead, Cold starts, and Double Billing**:
Because tasks operate within the same memory, invocation overheads, cold starts
and double billing associated with individual function calls are eliminated.

- **Customized Optimization**: An additional feature of the Nuclio Fusionizer is
the capability to customize the optimization process for the fusion tasks with
custom Optimizers, providing developers with the flexibility they require to set
up their systems as needed.

## Architecture

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
![fusionizer](https://github.com/marvin-steinke/nuclio_fusionizer/assets/48684343/72ad1f9d-9ea2-4fce-a620-4d245649ef98)
