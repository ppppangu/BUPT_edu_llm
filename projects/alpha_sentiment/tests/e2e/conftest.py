"""Fixtures for end-to-end tests"""
import pytest
import subprocess
import time
import httpx
import os
import signal


@pytest.fixture(scope="module")
def server_url():
    """Server URL for e2e tests"""
    return os.getenv("TEST_SERVER_URL", "http://127.0.0.1:5001")


@pytest.fixture(scope="module")
def running_server(server_url):
    """
    Start the server for e2e tests.

    Set TEST_SERVER_URL env var to use an existing server,
    otherwise starts a new server process.
    """
    if os.getenv("TEST_SERVER_URL"):
        # Use existing server
        yield server_url
        return

    # Start new server
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    proc = subprocess.Popen(
        ["uv", "run", "python", "-m", "backend.main"],
        cwd=project_root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=True if os.name == 'nt' else False,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
    )

    # Wait for server to start
    max_retries = 30
    for i in range(max_retries):
        try:
            response = httpx.get(f"{server_url}/api/health", timeout=1)
            if response.status_code == 200:
                break
        except (httpx.ConnectError, httpx.ReadTimeout):
            pass
        time.sleep(0.5)
    else:
        proc.terminate()
        raise RuntimeError("Server failed to start")

    yield server_url

    # Cleanup
    if os.name == 'nt':
        proc.send_signal(signal.CTRL_BREAK_EVENT)
    else:
        proc.terminate()
    proc.wait(timeout=5)


@pytest.fixture
def client(running_server):
    """HTTP client for e2e tests"""
    with httpx.Client(base_url=running_server, timeout=30) as client:
        yield client
