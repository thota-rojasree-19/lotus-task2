import subprocess
import time
import os
import sys

print("Starting Product 005 Acceptance Flow...")

def run_cmd(cmd, env=None):
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, env=env)
    if result.returncode != 0:
        print(f"Command failed with code {result.returncode}")
        sys.exit(result.returncode)

print("1. Baseline verification...")
run_cmd([sys.executable, "harness/validate_openapi.py"])
run_cmd([sys.executable, "harness/contract.py"])
run_cmd([sys.executable, "-m", "pytest", "tests/"])

print("2. Starting Product 004 Backend...")
run_cmd([sys.executable, "harness/reset_db.py"])

env = os.environ.copy()
env["FLASK_APP"] = "src.app:app"
env["FLASK_RUN_PORT"] = "5000"

flask_proc = subprocess.Popen([sys.executable, "-m", "flask", "run"], env=env)
time.sleep(2)

print("3. Running MCP tests...")
test_env = os.environ.copy()
test_env["OPENAPI_FILE"] = "./openapi.yaml"
test_env["API_BASE_URL"] = "http://127.0.0.1:5000"

test_result = subprocess.run([sys.executable, "-m", "pytest", "tests_mcp/", "-v"], env=test_env)

print("Cleaning up...")
flask_proc.terminate()
flask_proc.wait()

if test_result.returncode == 0:
    print("================================================")
    print("  PRODUCT 005 MCP RESULTS: ALL TESTS PASSED")
    print("================================================")
else:
    print("================================================")
    print("  PRODUCT 005 MCP RESULTS: TESTS FAILED")
    print("================================================")
    sys.exit(test_result.returncode)
