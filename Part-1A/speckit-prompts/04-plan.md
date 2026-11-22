Technical plan: Python 3.11, standard library only at runtime. Layout: src/todo/{__init__,__main__,errors,service,cli}.py.
Keep validation in small pure helper functions (complexity <= 10). Storage: load the JSON file for each operation,
modify, then atomic save via tempfile.mkstemp in the same directory + os.replace (so the file is 0600).
CLI uses argparse only. Do not create or modify anything under tests/ or .harness/. Dev tooling (not runtime):
pytest, pytest-cov, ruff, bandit as in requirements-dev.txt.
