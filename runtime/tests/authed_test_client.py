"""authed_test_client.py — shared test-only helper that makes
`app.test_client()` present a credential.

WHY IT EXISTS. Before the revision-127 containment, the four Workbench read
models (system context + recovery packet, build path, destination
architecture, project intelligence) and the container_app system-health /
enforcement-audit routes were UNAUTHENTICATED, so their test files could call
`app.test_client().get(route)` and get a 200. They now sit behind
runtime/workbench_auth.check_auth(), which is fail-closed: an unconfigured
server answers 503 and an uncredentialled request answers 401.

Those test files are about the READ MODELS — whether the route returns the same
object the read model returns, whether a caller can forge a database path,
whether the Mermaid source is generated from the same phases. They are not
about authorization, which has its own file
(runtime/tests/test_revision_127_containment.py). So rather than thread a
header through every `client.get(...)` call site in four large files, each
installs this client class once and keeps its assertions unchanged.

HOW. `install(app)` configures a server credential in the environment and sets
`app.test_client_class`, so every subsequent `app.test_client()` carries the
Authorization header. Flask reads the key through workbench_auth on every
call, so this is not import-order sensitive.

WHAT IT DELIBERATELY DOES NOT DO. It does not bypass, stub or monkeypatch
check_auth(). There is no test hook in the auth path and this helper does not
add one: it configures a real credential and presents it, exactly as a real
machine caller does. A test that wants to observe a DENIAL simply uses
`app.test_client(use_cookies=True)` with no header — see
test_revision_127_containment.py, which builds its clients directly and never
imports this module.
"""
import os

from flask.testing import FlaskClient

# Test-only, and not a secret: it is created here, lives for the process, and
# authorizes nothing outside this test run. The live container's key comes from
# /workspace/secrets.env and never appears in the repository.
TEST_API_KEY = "test-only-read-model-api-key"


def make_client_class(api_key=TEST_API_KEY):
    class _AuthedClient(FlaskClient):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.environ_base["HTTP_AUTHORIZATION"] = f"Bearer {api_key}"

    return _AuthedClient


def install(app, api_key=TEST_API_KEY):
    """Configure the server credential and make app.test_client() present it.

    Returns the key, so a caller that wants to assert on the header can.
    """
    os.environ["CIS_PIPELINE_API_KEY"] = api_key
    app.test_client_class = make_client_class(api_key)
    return api_key
