"""Ask an attester for its verdict in a process of its own, and write the verdict to a file.

The bundle check runs this file and never loads an attester into its own process. An attester is
the project's own code, and it can end a process in a way that no code around it in that process
can catch: `os._exit` skips every `except` and `finally`. So the verdict is written to a file as
the very last step, and a process that ends before that step has given no verdict, whatever its
exit code. Standard library only, as an attester is.

    python -I -B attester_child.py <attester file> <verdict file>   (the request on stdin, as JSON)
"""

import importlib.util
import json
import sys
from pathlib import Path
from typing import Final

ATTESTER_MODULE_NAME: Final = "okf_attester"
ATTEST_FUNCTION_NAME: Final = "attest"


def main(arguments: list[str]) -> int:
    """Load the attester, ask it for its verdict on the request, and write what it returned."""
    attester_file = Path(arguments[0])
    verdict_file = Path(arguments[1])
    request = json.load(sys.stdin)
    module_spec = importlib.util.spec_from_file_location(ATTESTER_MODULE_NAME, attester_file)
    if module_spec is None or module_spec.loader is None:
        sys.stderr.write(f"the attester {attester_file} could not be loaded\n")
        return 1
    attester_module = importlib.util.module_from_spec(module_spec)
    # A dataclass looks its own module up by name, so the module is registered before it runs.
    sys.modules[ATTESTER_MODULE_NAME] = attester_module
    module_spec.loader.exec_module(attester_module)
    attest_function = getattr(attester_module, ATTEST_FUNCTION_NAME)
    raw_verdict: object = attest_function(
        computation=request["computation"],
        parameters=request["parameters"],
        receipt=request["receipt"],
        claimed_value=request["claimed_value"],
    )
    # Written last: a process that ends before this line has given no verdict.
    verdict_file.write_text(json.dumps(raw_verdict, default=str), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
