## Overview

The `run_tests` shell script performs a sequence of operations to ensure that
the project components are running correctly. This script starts the Fusionizer
server, deploys the tasks, invokes them, and finally compares test logs against
reference logs.

## Prerequisites

Make sure you have the following installed on your system before using the script:
- Docker
- zip
- curl
- awk

Also, ensure Docker is running before executing the script.

## How to Use

```bash
./run_tests
```

## Testing Scenario

1. Build and deploy TaskA.
2. Build and deploy TaskB.
3. Invoke TaskA before fusion and check for expected output.
4. Wait for TaskA and TaskB to be fused together and verify the state of TaskA.
5. Invoke TaskA after the fusion and verify the resulting behavior.
6. Delete TaskA and check that it is removed correctly.
7. Verify TaskB's readiness and redeployment after TaskA's deletion.
8. Invoke TaskB with provided arguments and check for the expected result.
9. Delete TaskB and verify its removal.
10. Clean up Docker environment.
11. Compare test logs to reference logs to find any discrepancies.

## Notes

Log comparison is performed by ignoring dynamic content such as addresses and
dates to ensure that only the relevant differences are shown. You might still
experience differences, even if all went well. This is likely due different
server-internal ordering of the Tasks e.g. ['taska', 'taskb'] <-> ['taskb',
'taska']. Check against the reference logs if in doubt.