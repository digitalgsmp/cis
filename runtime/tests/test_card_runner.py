"""
test_card_runner.py — tests for runtime/card_runner.py (queue item WB.1B-2,
incl. its bounded-control addendum, and corrected by card WB.1B-2A).

No paid model calls. `claude`/`codex` are never actually invoked — dispatch()'s
`_test_command` seam (test-only; never used by the CLI or Flask routes)
substitutes a real, harmless `python3 -c ...` child process for the computed
argv, so the real spawn/wall-clock-timeout/process-group-kill/finalize
pipeline is exercised against an actual OS process, not a mocked function
call. A real temporary git repo (not the live one) backs the scope/
already-dirty-file checks; a real temporary sqlite db (migrations 0036+0037
applied) backs the card_factory_cards/card_runner_runs validation dispatch()
now does live, per WB.1B-2A's correction that "an inbox pathname is not
proof of validity."

Run: python3 runtime/tests/test_card_runner.py
"""
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Auth is fail-CLOSED (runtime/workbench_auth.py): an unset CIS_PIPELINE_API_KEY
# denies every request with 503 rather than granting anonymous access. A real
# key is configured and presented below, exactly as a real caller would.
TEST_API_KEY = "test-workbench-key"
os.environ["CIS_PIPELINE_API_KEY"] = TEST_API_KEY

REPO_SRC = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MIGRATION_0036 = os.path.join(REPO_SRC, "runtime", "schema", "migrations", "0036_card_factory.sql")
MIGRATION_0037 = os.path.join(REPO_SRC, "runtime", "schema", "migrations", "0037_card_runner.sql")
REAL_EXECUTION_RULES = os.path.join(REPO_SRC, "cards", "EXECUTION_RULES.md")
REAL_REVIEW_RULES = os.path.join(REPO_SRC, "cards", "REVIEW_RULES.md")

MODEL_CARD = """CARD cis-do-a-thing: Add a thing
SOURCE: message 1, 2026-09-17
INTENT (Eric, verbatim): "this is a fifteen-plus char test quote"
BUILD: Eric sees a new button.
DONE WHEN:
  - Eric clicks the button and sees a result.
EVIDENCE:
  - curl -s http://127.0.0.1:5000/ok
NOT IN THIS CARD: dashboards, refactors, other features, docs, migrations, telegram
"""

TERMINAL = {"completed", "failed", "timeout", "stopped", "stop_failed"}


def _py(code):
    return [sys.executable, "-c", code]


def _claude_mock(stdin_capture_path, extra_writes=None, num_turns=3, cost=0.01,
                  message="ok", exit_code=0, sleep_s=0.0):
    """argv for a python3 process that mimics `claude -p --output-format
    json`: captures stdin to an absolute path, optionally sleeps, optionally
    writes extra repo-relative files, then prints a claude-shaped JSON blob
    and exits with exit_code."""
    extra_writes = extra_writes or []
    writes_code = "".join(f"open({p!r}, 'w').write({c!r})\n" for p, c in extra_writes)
    code = (
        "import sys, time, json\n"
        "data = sys.stdin.read()\n"
        f"open({stdin_capture_path!r}, 'w').write(data)\n"
        f"time.sleep({sleep_s})\n"
        f"{writes_code}"
        "print(json.dumps({"
        f"'num_turns': {num_turns}, "
        "'usage': {'input_tokens': 100, 'cache_read_input_tokens': 10, 'output_tokens': 50}, "
        f"'total_cost_usd': {cost}, 'result': {message!r}"
        "}))\n"
        f"sys.exit({exit_code})\n"
    )
    return _py(code)


def _codex_mock(final_message_path, message="PASS\n- looks right", sleep_s=0.0, exit_code=0):
    code = (
        "import sys, time\n"
        "sys.stdin.read()\n"
        f"time.sleep({sleep_s})\n"
        f"open({final_message_path!r}, 'w').write({message!r})\n"
        f"sys.exit({exit_code})\n"
    )
    return _py(code)


def _sleeper(seconds):
    return _py(f"import time; time.sleep({seconds})")


def run():
    results = []

    def check(label, cond, detail=""):
        results.append((label, bool(cond)))
        print(f"{'PASS' if cond else 'FAIL'}  {label}" + (f"  -- {detail}" if not cond else ""))

    tmp_root = tempfile.mkdtemp(prefix="card_runner_test_")
    repo_root = os.path.join(tmp_root, "repo")
    os.makedirs(repo_root)
    subprocess.run(["git", "init", "-q"], cwd=repo_root, check=True)
    subprocess.run(["git", "config", "user.email", "t@example.com"], cwd=repo_root, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=repo_root, check=True)
    os.makedirs(os.path.join(repo_root, "runtime"))
    baseline_path = os.path.join(repo_root, "runtime", "tracked.py")
    with open(baseline_path, "w") as f:
        f.write("x = 1\n")
    subprocess.run(["git", "add", "-A"], cwd=repo_root, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=repo_root, check=True)
    # already-dirty before any dispatch happens
    with open(baseline_path, "w") as f:
        f.write("x = 1  # dirty baseline\n")

    cards_dir = os.path.join(repo_root, "cards")
    inbox_dir = os.path.join(cards_dir, "inbox")
    os.makedirs(inbox_dir)
    handoffs_dir = os.path.join(repo_root, "data", "agent_handoffs")
    os.makedirs(handoffs_dir)
    shutil.copy(REAL_EXECUTION_RULES, os.path.join(cards_dir, "EXECUTION_RULES.md"))
    shutil.copy(REAL_REVIEW_RULES, os.path.join(cards_dir, "REVIEW_RULES.md"))

    log_dir = os.path.join(tmp_root, "logs")
    db_path = os.path.join(tmp_root, "test.db")
    conn = sqlite3.connect(db_path)
    conn.executescript(open(MIGRATION_0037).read())
    conn.executescript(open(MIGRATION_0036).read())
    conn.commit()
    conn.close()

    import card_runner
    card_runner.REPO_ROOT = repo_root
    card_runner.DB_PATH = db_path
    card_runner.CARDS_DIR = cards_dir
    card_runner.EXECUTION_RULES_PATH = os.path.join(cards_dir, "EXECUTION_RULES.md")
    card_runner.REVIEW_RULES_PATH = os.path.join(cards_dir, "REVIEW_RULES.md")
    card_runner.HANDOFFS_DIR = handoffs_dir
    card_runner.LOG_DIR = log_dir
    # card_runner.API_KEY = "" removed: the module constant no longer exists
    # and blanking it would no longer disable auth anyway. Credentials are
    # presented on the client instead (below).

    from flask import Flask
    app = Flask(__name__)
    app.register_blueprint(card_runner.card_runner_bp)
    client = app.test_client()
    client.environ_base["HTTP_AUTHORIZATION"] = f"Bearer {TEST_API_KEY}"

    # ── DB fixture helpers: real card_factory_asks/card_factory_cards rows,
    # exactly what card_factory_app.py itself would have written. ──
    def db():
        c = sqlite3.connect(db_path)
        c.row_factory = sqlite3.Row
        return c

    def make_ask(project="cis", ask_text="do a thing", revision=1):
        c = db()
        cur = c.execute(
            "INSERT INTO card_factory_asks (project, ask_text, revision) VALUES (?, ?, ?)",
            (project, ask_text, revision),
        )
        c.commit()
        ask_id = cur.lastrowid
        c.close()
        return ask_id

    def bump_ask_revision(ask_id, new_revision):
        c = db()
        c.execute("UPDATE card_factory_asks SET revision = ? WHERE id = ?", (new_revision, ask_id))
        c.commit()
        c.close()

    def make_card(ask_id, ask_revision=1, card_text=MODEL_CARD, status="pass", is_current=1,
                  save_file=True, tamper_file_text=None):
        c = db()
        cur = c.execute(
            "INSERT INTO card_factory_cards (ask_id, ask_revision, card_revision, is_current, "
            "card_text, status) VALUES (?, ?, 1, ?, ?, ?)",
            (ask_id, ask_revision, is_current, card_text, status),
        )
        card_id = cur.lastrowid
        c.execute("UPDATE card_factory_cards SET lineage_id = ? WHERE id = ?", (card_id, card_id))
        c.commit()
        if save_file:
            filename = f"cardfactory-{card_id:06d}-cis.md"
            full_path = os.path.join(inbox_dir, filename)
            with open(full_path, "w") as f:
                f.write(tamper_file_text if tamper_file_text is not None else card_text)
            c.execute("UPDATE card_factory_cards SET saved_path = ? WHERE id = ?", (full_path, card_id))
            c.commit()
        c.close()
        return card_id

    def fp(text=MODEL_CARD):
        return card_runner._sha256_text(text)

    def wait_terminal(run_id, timeout=10):
        deadline = time.time() + timeout
        while time.time() < deadline:
            row = card_runner.run_status(run_id)
            if row["status"] in TERMINAL:
                return row
            time.sleep(0.05)
        raise TimeoutError(f"run {run_id} never reached a terminal state")

    def next_id():
        c = sqlite3.connect(db_path)
        row = c.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM card_runner_runs").fetchone()
        c.close()
        return row[0]

    def run_count():
        return len(card_runner.ledger()["runs"])

    # ── _build_command: limit flags present, fresh session (no resume flags) ──
    perm_impl = card_runner._permission_plan("claude", "implement", ["pytest"])
    cmd = card_runner._build_command("claude", "implement", "claude-haiku-4-5-20251001",
                                      "sess-1", perm_impl, 2.5, None)
    check("claude cmd has --max-budget-usd when budget_usd set", "--max-budget-usd" in cmd and "2.5" in cmd, cmd)
    check("claude cmd has --safe-mode", "--safe-mode" in cmd, cmd)
    check("claude cmd has --session-id", "--session-id" in cmd, cmd)
    check("claude cmd has no resume/continue flags", not ({"-r", "--resume", "-c", "--continue",
          "--fork-session"} & set(cmd)), cmd)

    perm_rev = card_runner._permission_plan("claude", "review", [])
    cmd_rev = card_runner._build_command("claude", "review", "claude-haiku-4-5-20251001",
                                          "sess-2", perm_rev, None, None)
    check("claude review cmd allows only Read/Glob/Grep", "Read Glob Grep" in cmd_rev, cmd_rev)
    check("claude review cmd disallows Edit/Write/Bash", "Edit Write Bash" in cmd_rev, cmd_rev)

    perm_codex_impl = card_runner._permission_plan("codex", "implement", [])
    cmd_codex = card_runner._build_command("codex", "implement", None, "sess-3",
                                            perm_codex_impl, None, "/tmp/fm.txt")
    check("codex implement cmd uses workspace-write + --approve-for-me",
          "workspace-write" in cmd_codex and "--approve-for-me" in cmd_codex, cmd_codex)
    check("codex cmd has no resume/fork subcommand", "resume" not in cmd_codex and "fork" not in cmd_codex, cmd_codex)
    check("codex cmd uses --ephemeral (fresh session)", "--ephemeral" in cmd_codex, cmd_codex)

    perm_codex_rev = card_runner._permission_plan("codex", "review", [])
    cmd_codex_rev = card_runner._build_command("codex", "review", None, "sess-4",
                                                perm_codex_rev, None, "/tmp/fm2.txt")
    check("codex review cmd uses read-only sandbox", "read-only" in cmd_codex_rev, cmd_codex_rev)

    # ── _parse_target_output: ledger parse from sample JSON ──
    sample = json.dumps({
        "is_error": False, "duration_api_ms": 524698, "num_turns": 77, "stop_reason": "end_turn",
        "session_id": "abc", "total_cost_usd": 2.4969978,
        "usage": {"input_tokens": 10, "cache_read_input_tokens": 5, "output_tokens": 20},
        "result": "done here",
    }).encode()
    parsed = card_runner._parse_target_output("claude", sample)
    check("parse claude sample: num_turns", parsed["num_turns"] == 77, parsed)
    check("parse claude sample: cost", parsed["cost_usd"] == 2.4969978, parsed)
    check("parse claude sample: cached tokens", parsed["cached_input_tokens"] == 5, parsed)
    check("parse claude sample: not usage_unknown", parsed["usage_unknown"] is False, parsed)
    bad = card_runner._parse_target_output("claude", b"not json{{{")
    check("parse malformed claude output -> usage_unknown, no crash", bad["usage_unknown"] is True, bad)

    # ── Database-validated dispatch: current, PASS, matching ask revision, ──
    # ── matching content — "an inbox pathname is not proof of validity" ──
    ask1 = make_ask(project="cis")
    card1 = make_card(ask1, ask_revision=1)

    try:
        card_runner.dispatch(999999, "implement", "claude", request_id="r-notfound",
                              expected_card_fingerprint=fp(), authorized_by="eric",
                              accept_time_only_control=True, permitted_files=["runtime/x.py"])
        check("dispatch refused for unknown card_factory_card_id", False)
    except card_runner.RunnerError:
        check("dispatch refused for unknown card_factory_card_id", True)

    # not current (superseded) — file still physically present in inbox
    superseded = make_card(ask1, ask_revision=1, status="pass", is_current=0)
    try:
        card_runner.dispatch(superseded, "implement", "claude", request_id="r-superseded",
                              expected_card_fingerprint=fp(), authorized_by="eric",
                              accept_time_only_control=True, permitted_files=["runtime/x.py"])
        check("dispatch refused for superseded (non-current) db row despite file in inbox", False)
    except card_runner.RevisionMismatch:
        check("dispatch refused for superseded (non-current) db row despite file in inbox", True)

    # not PASS — file still physically present in inbox (edge case; card_factory_app.py
    # itself never saves a non-pass file, but the DB check must be the actual gate, not the file)
    failed_card = make_card(ask1, ask_revision=1, status="fail")
    try:
        card_runner.dispatch(failed_card, "implement", "claude", request_id="r-notpass",
                              expected_card_fingerprint=fp(), authorized_by="eric",
                              accept_time_only_control=True, permitted_files=["runtime/x.py"])
        check("dispatch refused for non-PASS db row despite file in inbox", False)
    except card_runner.RunnerError:
        check("dispatch refused for non-PASS db row despite file in inbox", True)

    # stale: ask edited after the card was generated — file in inbox is untouched/unchanged
    ask2 = make_ask(project="cis", ask_text="do a different thing")
    stale_card = make_card(ask2, ask_revision=1)
    bump_ask_revision(ask2, 2)  # ask has since moved on; card was generated against revision 1
    try:
        card_runner.dispatch(stale_card, "implement", "claude", request_id="r-stale",
                              expected_card_fingerprint=fp(), authorized_by="eric",
                              accept_time_only_control=True, permitted_files=["runtime/x.py"])
        check("dispatch refused for stale ask revision despite file remaining in inbox unchanged", False)
    except card_runner.RevisionMismatch:
        check("dispatch refused for stale ask revision despite file remaining in inbox unchanged", True)

    # content mismatch: caller's fingerprint doesn't match the DB's card_text
    try:
        card_runner.dispatch(card1, "implement", "claude", request_id="r-mismatch",
                              expected_card_fingerprint="0" * 64, authorized_by="eric",
                              accept_time_only_control=True, permitted_files=["runtime/x.py"])
        check("revision/approval fingerprint mismatch rejected", False)
    except card_runner.RevisionMismatch:
        check("revision/approval fingerprint mismatch rejected", True)

    # on-disk file tampered out of band: no longer matches the DB's card_text
    tampered = make_card(ask1, ask_revision=1, card_text=MODEL_CARD, tamper_file_text=MODEL_CARD + "\nEXTRA\n")
    try:
        card_runner.dispatch(tampered, "implement", "claude", request_id="r-tampered",
                              expected_card_fingerprint=fp(), authorized_by="eric",
                              accept_time_only_control=True, permitted_files=["runtime/x.py"])
        check("dispatch refused when on-disk file no longer matches the database's card_text", False)
    except card_runner.RevisionMismatch:
        check("dispatch refused when on-disk file no longer matches the database's card_text", True)

    # missing saved_path (e.g. never made it to inbox)
    no_file_card = make_card(ask1, ask_revision=1, save_file=False)
    try:
        card_runner.dispatch(no_file_card, "implement", "claude", request_id="r-nofile",
                              expected_card_fingerprint=fp(), authorized_by="eric",
                              accept_time_only_control=True, permitted_files=["runtime/x.py"])
        check("dispatch refused when db row has no saved_path", False)
    except card_runner.RunnerError:
        check("dispatch refused when db row has no saved_path", True)

    # ── unsupported-cap rejection ──
    try:
        card_runner.dispatch(card1, "implement", "codex", request_id="r-cap1",
                              expected_card_fingerprint=fp(), authorized_by="eric",
                              accept_time_only_control=True, permitted_files=["runtime/x.py"], max_turns=5)
        check("codex max_turns rejected (unavailable)", False)
    except card_runner.RunnerError as e:
        check("codex max_turns rejected (unavailable)", "unavailable" in str(e) or "unsupported" in str(e), str(e))
    try:
        card_runner.dispatch(card1, "implement", "codex", request_id="r-cap2",
                              expected_card_fingerprint=fp(), authorized_by="eric",
                              budget_usd=5.0, permitted_files=["runtime/x.py"])
        check("codex budget_usd rejected (unsupported)", False)
    except card_runner.RunnerError as e:
        check("codex budget_usd rejected (unsupported)", "unsupported" in str(e), str(e))
    try:
        card_runner.dispatch(card1, "implement", "claude", request_id="r-cap3",
                              expected_card_fingerprint=fp(), authorized_by="eric",
                              accept_time_only_control=True, permitted_files=["runtime/x.py"], max_turns=5)
        check("claude max_turns without ack rejected", False)
    except card_runner.RunnerError as e:
        check("claude max_turns without ack rejected", "observation" in str(e) or "ack" in str(e), str(e))
    try:
        card_runner.dispatch(card1, "implement", "claude", request_id="r-cap4",
                              expected_card_fingerprint=fp(), authorized_by="",
                              accept_time_only_control=True, permitted_files=["runtime/x.py"])
        check("empty authorized_by rejected", False)
    except card_runner.RunnerError:
        check("empty authorized_by rejected", True)
    try:
        card_runner.dispatch(card1, "implement", "claude", request_id="r-cap5",
                              expected_card_fingerprint=fp(), authorized_by="eric",
                              permitted_files=["runtime/x.py"])
        check("no budget & no accept_time_only_control rejected", False)
    except card_runner.RunnerError:
        check("no budget & no accept_time_only_control rejected", True)
    try:
        card_runner.dispatch(card1, "implement", "claude", request_id="r-cap6",
                              expected_card_fingerprint=fp(), authorized_by="eric",
                              accept_time_only_control=True, permitted_files=["runtime/x.py"],
                              review_of_run_id=1)
        check("implement dispatch with review_of_run_id rejected", False)
    except card_runner.RunnerError:
        check("implement dispatch with review_of_run_id rejected", True)
    try:
        card_runner.dispatch(card1, "review", "claude", request_id="r-cap7",
                              expected_card_fingerprint=fp(), authorized_by="eric",
                              accept_time_only_control=True)
        check("review dispatch without review_of_run_id rejected", False)
    except card_runner.RunnerError:
        check("review dispatch without review_of_run_id rejected", True)

    runs_before = run_count()
    check("no DB rows created by any rejected dispatch above", run_count() == runs_before, runs_before)

    # ── Full implement dispatch: rules prepended, permitted write ok, ──
    # ── out-of-scope flag, own run folder exempt, completion.json status read ──
    stdin_capture = os.path.join(tmp_root, "stdin_capture_1.txt")
    permitted_rel = "runtime/permitted.py"
    unpermitted_rel = "runtime/surprise.py"
    mock1 = _claude_mock(
        stdin_capture,
        extra_writes=[
            (permitted_rel, "# permitted change\n"),
            (unpermitted_rel, "# should be flagged\n"),
            ("runtime/tracked.py", "x = 1  # further dirtied during run\n"),
        ],
        num_turns=4, cost=0.03, message="did the thing",
    )
    row1, dup1 = card_runner.dispatch(
        card1, "implement", "claude", request_id="r-impl-1", expected_card_fingerprint=fp(),
        authorized_by="eric", accept_time_only_control=True, permitted_files=[permitted_rel],
        _test_command=mock1,
    )
    check("first dispatch is not a duplicate", dup1 is False, dup1)
    run_dir_abs_1 = os.path.join(repo_root, row1["run_dir"])
    completion_path_1 = os.path.join(run_dir_abs_1, "completion.json")
    with open(completion_path_1, "w") as f:
        json.dump({"card_id": "x", "status": "BLOCKED", "changed_files": [], "tests": {},
                   "remaining_limitations": []}, f)
    row1 = wait_terminal(row1["id"])
    check("implement dispatch completes", row1["status"] == "completed", row1)
    check("permission_mode recorded", row1["permission_mode"] == "acceptEdits", row1)
    check("run_dir is unique per run, linked to the card", f"run-{row1['id']}-implement" in row1["run_dir"], row1)
    check("CARD.md written with Folder: line", os.path.isfile(os.path.join(run_dir_abs_1, "CARD.md")), None)
    card_md = open(os.path.join(run_dir_abs_1, "CARD.md")).read()
    check("CARD.md starts with Folder: line matching run_dir", card_md.startswith(f"Folder: {row1['run_dir']}/"), card_md[:80])
    stdin_sent = open(stdin_capture).read()
    check("rules prepended: prompt starts with EXECUTION_RULES.md content",
          stdin_sent.startswith(open(os.path.join(cards_dir, "EXECUTION_RULES.md")).read()), stdin_sent[:80])
    check("rules prepended: prompt contains the card body", "Add a thing" in stdin_sent, None)
    out_of_scope = set(row1["out_of_scope"])
    check("out-of-scope flags the untouched-by-card new file", unpermitted_rel in out_of_scope, out_of_scope)
    check("out-of-scope flags an already-dirty file further modified", "runtime/tracked.py" in out_of_scope, out_of_scope)
    check("out-of-scope does NOT flag the permitted file", permitted_rel not in out_of_scope, out_of_scope)
    check("out-of-scope does NOT flag the run's own evidence folder", row1["run_dir"] + "/completion.json" not in out_of_scope, out_of_scope)
    check("completion.json status read", row1["card_completion_status"] == "BLOCKED", row1)
    check("ledger totals include this run's project (cis)", "cis" in card_runner.ledger()["totals_by_project"], None)
    c = db()
    c.execute("UPDATE card_factory_cards SET usage_input_tokens=500, usage_output_tokens=200, "
              "usage_cost_usd=0.02 WHERE id=?", (card1,))
    c.commit()
    c.close()
    gen = card_runner.ledger()["totals_by_project"]["cis"].get("generation")
    check("ledger totals merge Generate attempts (card_factory_cards, unchanged by this correction)",
          gen is not None and gen["generate_attempts"] >= 1 and gen["input_tokens"] >= 500, gen)

    # ── duplicate dispatch refusal ──
    row1_dup, dup2 = card_runner.dispatch(
        card1, "implement", "claude", request_id="r-impl-1", expected_card_fingerprint=fp(),
        authorized_by="eric", accept_time_only_control=True, permitted_files=[permitted_rel],
        _test_command=mock1,
    )
    check("replaying request_id returns duplicate=True", dup2 is True, dup2)
    check("replaying request_id returns the same run id (no second run started)",
          row1_dup["id"] == row1["id"], (row1_dup["id"], row1["id"]))
    check("no extra ledger row from the duplicate call", run_count() == runs_before + 1, run_count())

    # ── Implementation then separately authorized review: both evidence ──
    # ── sets coexist, neither overwrites the other ──
    stdin_capture_rev = os.path.join(tmp_root, "stdin_capture_rev.txt")
    row_rev, dup_rev = card_runner.dispatch(
        card1, "review", "claude", request_id="r-review-of-impl-1",
        expected_card_fingerprint=fp(), authorized_by="eric", accept_time_only_control=True,
        review_of_run_id=row1["id"],
        _test_command=_claude_mock(stdin_capture_rev, message="PASS\n- looks right"),
    )
    check("review dispatch is not a duplicate", dup_rev is False, dup_rev)
    check("review run_dir differs from the implementation's run_dir",
          row_rev["run_dir"] != row1["run_dir"], (row_rev["run_dir"], row1["run_dir"]))
    row_rev = wait_terminal(row_rev["id"])
    check("review dispatch completes", row_rev["status"] == "completed", row_rev)
    review_prompt = open(stdin_capture_rev).read()
    check("review prompt prepends REVIEW_RULES.md, not EXECUTION_RULES.md",
          review_prompt.startswith(open(os.path.join(cards_dir, "REVIEW_RULES.md")).read()), review_prompt[:80])
    check("review prompt points at the implementation's evidence folder",
          f"Implementation to review: {row1['run_dir']}/" in review_prompt, review_prompt[:400])
    review_md_path = os.path.join(repo_root, row_rev["run_dir"], "review.md")
    check("runner writes review.md into the review's OWN folder",
          os.path.isfile(review_md_path) and open(review_md_path).read() == "PASS\n- looks right", None)
    # both evidence sets still intact, untouched by the other run
    check("implementation's completion.json is untouched by the review",
          json.load(open(completion_path_1))["status"] == "BLOCKED", None)
    check("implementation's CARD.md is untouched by the review",
          open(os.path.join(run_dir_abs_1, "CARD.md")).read() == card_md, None)
    check("review's out_of_scope does not flag the implementation's folder (it only referenced it)",
          not any(p.startswith(row1["run_dir"]) for p in row_rev["out_of_scope"]), row_rev["out_of_scope"])

    # review_of_run_id validation
    try:
        card_runner.dispatch(card1, "review", "claude", request_id="r-rev-badref",
                              expected_card_fingerprint=fp(), authorized_by="eric",
                              accept_time_only_control=True, review_of_run_id=999999)
        check("review_of_run_id referencing unknown run rejected", False)
    except card_runner.RunnerError:
        check("review_of_run_id referencing unknown run rejected", True)
    try:
        card_runner.dispatch(card1, "review", "claude", request_id="r-rev-badmode",
                              expected_card_fingerprint=fp(), authorized_by="eric",
                              accept_time_only_control=True, review_of_run_id=row_rev["id"])
        check("review_of_run_id referencing a review (not implement) run rejected", False)
    except card_runner.RunnerError:
        check("review_of_run_id referencing a review (not implement) run rejected", True)
    other_ask = make_ask(project="cis", ask_text="a different card entirely")
    other_card = make_card(other_ask, ask_revision=1)
    try:
        card_runner.dispatch(other_card, "review", "claude", request_id="r-rev-othercard",
                              expected_card_fingerprint=fp(), authorized_by="eric",
                              accept_time_only_control=True, review_of_run_id=row1["id"])
        check("review_of_run_id belonging to a different card rejected", False)
    except card_runner.RunnerError:
        check("review_of_run_id belonging to a different card rejected", True)

    # ── one run at a time per repo ──
    ask3 = make_ask(project="cis")
    card2 = make_card(ask3, ask_revision=1)
    ask4 = make_ask(project="cis")
    card3 = make_card(ask4, ask_revision=1)
    row2, _ = card_runner.dispatch(
        card2, "implement", "claude", request_id="r-busy-1", expected_card_fingerprint=fp(),
        authorized_by="eric", accept_time_only_control=True, permitted_files=["runtime/other.py"],
        _test_command=_sleeper(5),
    )
    try:
        card_runner.dispatch(
            card3, "implement", "claude", request_id="r-busy-2", expected_card_fingerprint=fp(),
            authorized_by="eric", accept_time_only_control=True, permitted_files=["runtime/other2.py"],
            _test_command=_sleeper(5),
        )
        check("second concurrent dispatch refused (one at a time)", False)
    except card_runner.RunnerBusy:
        check("second concurrent dispatch refused (one at a time)", True)

    # ── Stop: durable cancellation, real process-group kill ──
    stopped = card_runner.stop(row2["id"])
    check("stop() reports stopped", stopped["status"] == "stopped", stopped)
    check("stop() clears active_lock", stopped["active_lock"] is False, stopped)
    time.sleep(0.3)
    try:
        os.kill(row2["pid"], 0)
        alive = True
    except ProcessLookupError:
        alive = False
    check("stopped process is actually dead", alive is False, None)
    time.sleep(0.5)  # let any in-flight finalize thread settle
    check("stopped run stays 'stopped' (finalize thread does not resurrect it)",
          card_runner.run_status(row2["id"])["status"] == "stopped",
          card_runner.run_status(row2["id"])["status"])

    # lock released: a new dispatch now succeeds
    row3, _ = card_runner.dispatch(
        card3, "implement", "claude", request_id="r-after-stop", expected_card_fingerprint=fp(),
        authorized_by="eric", accept_time_only_control=True, permitted_files=["runtime/other2.py"],
        _test_command=_claude_mock(os.path.join(tmp_root, "stdin_capture_3.txt")),
    )
    row3 = wait_terminal(row3["id"])
    check("dispatch after stop succeeds (lock released)", row3["status"] == "completed", row3)

    # ── no restart after cancellation (direct guard test on _finalize) ──
    ask5 = make_ask(project="cis")
    card4 = make_card(ask5, ask_revision=1)
    row4, _ = card_runner.dispatch(
        card4, "implement", "claude", request_id="r-guard", expected_card_fingerprint=fp(),
        authorized_by="eric", accept_time_only_control=True, permitted_files=["runtime/g.py"],
        _test_command=_sleeper(5),
    )
    stop4 = card_runner.stop(row4["id"])
    check("guard setup: run is stopped before the late-finalize race", stop4["status"] == "stopped", stop4)

    class _FakeLateProc:
        pid = 99999999
        returncode = 0

        def communicate(self, timeout=None):
            return (b'{"num_turns": 1, "usage": {}, "total_cost_usd": 0.001, "result": "late success"}', b"")

    card_runner._finalize(row4["id"], _FakeLateProc(), time.monotonic(), {}, [], "implement", "claude",
                           30, os.path.join(log_dir, "late.log"), None, row4["run_dir"], None)
    late_row = card_runner.run_status(row4["id"])
    check("a late 'successful' finalize cannot resurrect a stopped run",
          late_row["status"] == "stopped", late_row["status"])

    # ── timeout kill ──
    ask6 = make_ask(project="cis")
    card5 = make_card(ask6, ask_revision=1)
    row5, _ = card_runner.dispatch(
        card5, "implement", "claude", request_id="r-timeout", expected_card_fingerprint=fp(),
        authorized_by="eric", accept_time_only_control=True, permitted_files=["runtime/t.py"],
        wall_clock_timeout_seconds=1, _test_command=_sleeper(30),
    )
    row5 = wait_terminal(row5["id"], timeout=15)
    check("wall-clock timeout kills the run", row5["status"] == "timeout", row5)
    time.sleep(0.3)
    try:
        os.kill(row5["pid"], 0)
        alive5 = True
    except ProcessLookupError:
        alive5 = False
    check("timed-out process is actually dead", alive5 is False, None)

    # ── setup/launch failure: no orphan process, lock released, recoverable ──
    ask7 = make_ask(project="cis")
    card6 = make_card(ask7, ask_revision=1)
    try:
        card_runner.dispatch(
            card6, "implement", "claude", request_id="r-launchfail",
            expected_card_fingerprint=fp(), authorized_by="eric", accept_time_only_control=True,
            permitted_files=["runtime/lf.py"],
            _test_command=["/nonexistent/binary/should-not-exist-xyz"],
        )
        check("launch failure (missing binary) raises", False)
    except card_runner.RunnerError:
        check("launch failure (missing binary) raises", True)
    failed_row = [r for r in card_runner.ledger()["runs"] if r["request_id"] == "r-launchfail"][0]
    check("launch failure recorded as status='failed'", failed_row["status"] == "failed", failed_row)
    check("launch failure releases active_lock", failed_row["active_lock"] is False, failed_row)
    check("launch failure records an error message", bool(failed_row.get("error")), failed_row)
    # lock released: an unrelated dispatch succeeds immediately, no orphan blocking it
    ask8 = make_ask(project="cis")
    card7 = make_card(ask8, ask_revision=1)
    row7, _ = card_runner.dispatch(
        card7, "implement", "claude", request_id="r-after-launchfail",
        expected_card_fingerprint=fp(), authorized_by="eric", accept_time_only_control=True,
        permitted_files=["runtime/lf2.py"],
        _test_command=_claude_mock(os.path.join(tmp_root, "stdin_capture_lf.txt")),
    )
    row7 = wait_terminal(row7["id"])
    check("dispatch after a launch failure succeeds (no orphan lock)", row7["status"] == "completed", row7)

    # ── correction: missing rules file is a guarded setup failure too ──
    # (originally happened AFTER the run reservation committed but outside
    # any try/except — left the row stuck at status='queued', active_lock=1,
    # error=null, forever. Now guarded like every other pre-launch step.)
    ask_mr = make_ask(project="cis")
    card_mr = make_card(ask_mr, ask_revision=1)
    real_rules_path = card_runner.EXECUTION_RULES_PATH
    card_runner.EXECUTION_RULES_PATH = os.path.join(tmp_root, "no-such-rules-file.md")
    try:
        card_runner.dispatch(
            card_mr, "implement", "claude", request_id="r-missing-rules",
            expected_card_fingerprint=fp(), authorized_by="eric", accept_time_only_control=True,
            permitted_files=["runtime/mr.py"],
            _test_command=_claude_mock(os.path.join(tmp_root, "stdin_capture_mr.txt")),
        )
        check("dispatch with a missing rules file raises", False)
    except card_runner.RunnerError:
        check("dispatch with a missing rules file raises", True)
    finally:
        card_runner.EXECUTION_RULES_PATH = real_rules_path
    mr_row = [r for r in card_runner.ledger()["runs"] if r["request_id"] == "r-missing-rules"][0]
    check("missing-rules failure recorded as status='failed' (not stuck at queued)",
          mr_row["status"] == "failed", mr_row)
    check("missing-rules failure releases active_lock", mr_row["active_lock"] is False, mr_row)
    check("missing-rules failure records an actionable error message", bool(mr_row.get("error")), mr_row)
    check("missing-rules failure: no child was ever spawned (pid never recorded)",
          mr_row["pid"] is None, mr_row)
    ask_mr2 = make_ask(project="cis")
    card_mr2 = make_card(ask_mr2, ask_revision=1)
    row_mr2, _ = card_runner.dispatch(
        card_mr2, "implement", "claude", request_id="r-after-missing-rules",
        expected_card_fingerprint=fp(), authorized_by="eric", accept_time_only_control=True,
        permitted_files=["runtime/mr2.py"],
        _test_command=_claude_mock(os.path.join(tmp_root, "stdin_capture_mr2.txt")),
    )
    row_mr2 = wait_terminal(row_mr2["id"])
    check("dispatch after a missing-rules failure succeeds (no orphan lock)",
          row_mr2["status"] == "completed", row_mr2)

    # ── correction: failed log-directory creation is a guarded setup ──
    # failure too (same original bug — os.makedirs(LOG_DIR) ran unguarded).
    ask_ld = make_ask(project="cis")
    card_ld = make_card(ask_ld, ask_revision=1)
    blocked_log_dir = os.path.join(tmp_root, "log-dir-blocked-by-a-file")
    with open(blocked_log_dir, "w") as f:
        f.write("a plain file sits where the log directory needs to be created\n")
    real_log_dir = card_runner.LOG_DIR
    card_runner.LOG_DIR = blocked_log_dir  # os.makedirs(..., exist_ok=True) fails: not a directory
    try:
        card_runner.dispatch(
            card_ld, "implement", "claude", request_id="r-logdir-fail",
            expected_card_fingerprint=fp(), authorized_by="eric", accept_time_only_control=True,
            permitted_files=["runtime/ld.py"],
            _test_command=_claude_mock(os.path.join(tmp_root, "stdin_capture_ld.txt")),
        )
        check("dispatch with an unusable log directory raises", False)
    except card_runner.RunnerError:
        check("dispatch with an unusable log directory raises", True)
    finally:
        card_runner.LOG_DIR = real_log_dir
    ld_row = [r for r in card_runner.ledger()["runs"] if r["request_id"] == "r-logdir-fail"][0]
    check("log-directory failure recorded as status='failed' (not stuck at queued)",
          ld_row["status"] == "failed", ld_row)
    check("log-directory failure releases active_lock", ld_row["active_lock"] is False, ld_row)
    check("log-directory failure records an actionable error message", bool(ld_row.get("error")), ld_row)
    check("log-directory failure: no child was ever spawned (pid never recorded)",
          ld_row["pid"] is None, ld_row)
    ask_ld2 = make_ask(project="cis")
    card_ld2 = make_card(ask_ld2, ask_revision=1)
    row_ld2, _ = card_runner.dispatch(
        card_ld2, "implement", "claude", request_id="r-after-logdir-fail",
        expected_card_fingerprint=fp(), authorized_by="eric", accept_time_only_control=True,
        permitted_files=["runtime/ld2.py"],
        _test_command=_claude_mock(os.path.join(tmp_root, "stdin_capture_ld2.txt")),
    )
    row_ld2 = wait_terminal(row_ld2["id"])
    check("dispatch after a log-directory failure succeeds (no orphan lock)",
          row_ld2["status"] == "completed", row_ld2)

    # ── codex target: usage always recorded unknown ──
    # A second, separately authorized review of the SAME implementation
    # (row1) is allowed — reviews aren't limited to one per implementation.
    predicted_id = next_id()
    final_message_path = os.path.join(log_dir, f"run-{predicted_id}.final_message.txt")
    row8, _ = card_runner.dispatch(
        card1, "review", "codex", request_id="r-codex-1", expected_card_fingerprint=fp(),
        authorized_by="eric", accept_time_only_control=True, review_of_run_id=row1["id"],
        _test_command=_codex_mock(final_message_path, message="FAIL\n- missing tests"),
    )
    check("predicted run id matched codex mock's final_message_path", row8["id"] == predicted_id, (row8["id"], predicted_id))
    row8 = wait_terminal(row8["id"])
    check("codex dispatch completes", row8["status"] == "completed", row8)
    check("codex usage is always recorded unknown", row8["usage_unknown"] is True, row8)
    check("codex token fields are unknown (None), never guessed", row8["input_tokens"] is None, row8)

    # ── Flask routes: dispatch, stop, run status, ledger ──
    # The route body has no _test_command field (an HTTP caller must never
    # control the child argv) — route-level tests instead set the
    # module-global test-only fallback so no real claude/codex call happens.
    ask10 = make_ask(project="cis")
    card9 = make_card(ask10, ask_revision=1)
    card_runner._TEST_COMMAND_OVERRIDE = _claude_mock(os.path.join(tmp_root, "stdin_capture_route.txt"))
    resp = client.post("/api/cardrunner/dispatch", json={
        "card_factory_card_id": card9, "mode": "implement", "target": "claude", "request_id": "r-route-1",
        "expected_card_fingerprint": fp(), "authorized_by": "eric",
        "accept_time_only_control": True, "permitted_files": ["runtime/route.py"],
    })
    check("route dispatch returns 201 with a run id", resp.status_code == 201 and "run" in resp.get_json(), resp.status_code)
    route_run_id = resp.get_json()["run"]["id"]
    wait_terminal(route_run_id)
    status_resp_ok = client.get(f"/api/cardrunner/runs/{route_run_id}")
    check("route status: known run id -> 200 completed",
          status_resp_ok.status_code == 200
          and status_resp_ok.get_json()["run"]["status"] == "completed", status_resp_ok.get_json())
    card_runner._TEST_COMMAND_OVERRIDE = None

    ask11 = make_ask(project="cis")
    card10 = make_card(ask11, ask_revision=1)
    card_runner._TEST_COMMAND_OVERRIDE = _sleeper(5)
    resp9 = client.post("/api/cardrunner/dispatch", json={
        "card_factory_card_id": card10, "mode": "implement", "target": "claude", "request_id": "r-route-2",
        "expected_card_fingerprint": fp(), "authorized_by": "eric",
        "accept_time_only_control": True, "permitted_files": ["runtime/route2.py"],
    })
    run9_id = resp9.get_json()["run"]["id"]
    stop_route_resp = client.post(f"/api/cardrunner/runs/{run9_id}/stop")
    check("route stop: known run id -> 200 stopped",
          stop_route_resp.status_code == 200 and stop_route_resp.get_json()["run"]["status"] == "stopped",
          stop_route_resp.get_json())
    card_runner._TEST_COMMAND_OVERRIDE = None

    status_resp = client.get(f"/api/cardrunner/runs/999999999")
    check("route status: unknown run id -> 404", status_resp.status_code == 404, status_resp.status_code)
    ledger_resp = client.get("/api/cardrunner/runs")
    check("route ledger: 200 with runs/totals shape", ledger_resp.status_code == 200
          and "runs" in ledger_resp.get_json() and "totals_by_project" in ledger_resp.get_json(),
          ledger_resp.status_code)
    stop_resp = client.post(f"/api/cardrunner/runs/999999999/stop")
    check("route stop: unknown run id -> 404", stop_resp.status_code == 404, stop_resp.status_code)

    # ══ Run artifacts (WB.1B-3 CORRECTION.md F5a): a run-id-scoped, fixed- ══
    # ══ name read of the actual saved evidence.md/review.md — never       ══
    # ══ final_message, never an arbitrary path.                          ══
    evidence_path_1 = os.path.join(run_dir_abs_1, "evidence.md")
    with open(evidence_path_1, "w") as f:
        f.write("EVIDENCE: did the permitted change, verified via curl.\n")
    art = card_runner.run_artifact(row1["id"], "evidence.md")
    check("run_artifact reads the saved evidence.md for an implement run",
          art["found"] is True and art["content"].startswith("EVIDENCE: did the permitted change"), art)
    art_missing = card_runner.run_artifact(row1["id"], "review.md")
    check("run_artifact reports an honest missing state for a file that was never written "
          "(no review.md on an implement run) — never a crash, never fabricated content",
          art_missing["found"] is False and art_missing["content"] is None, art_missing)
    art_review = card_runner.run_artifact(row_rev["id"], "review.md")
    check("run_artifact reads the review.md the runner itself wrote for a review run, "
          "matching exactly what was independently confirmed on disk earlier",
          art_review["found"] is True and art_review["content"] == open(review_md_path).read(), art_review)

    try:
        card_runner.run_artifact(row1["id"], "../../../../etc/passwd")
        check("run_artifact rejects a non-allowlisted name outright (no path ever built from it)", False)
    except card_runner.RunnerError:
        check("run_artifact rejects a non-allowlisted name outright (no path ever built from it)", True)
    try:
        card_runner.run_artifact(999999999, "evidence.md")
        check("run_artifact raises NotFound for an unknown run id", False)
    except card_runner.NotFound:
        check("run_artifact raises NotFound for an unknown run id", True)

    orig_max_artifact = card_runner.MAX_ARTIFACT_READ_CHARS
    card_runner.MAX_ARTIFACT_READ_CHARS = 20
    try:
        big_path = os.path.join(run_dir_abs_1, "completion.json")
        with open(big_path, "w") as f:
            f.write("x" * 500)
        art_big = card_runner.run_artifact(row1["id"], "completion.json")
        check("run_artifact bounds a large file read and flags it truncated",
              art_big["truncated"] is True and len(art_big["content"]) == 20, art_big)
    finally:
        card_runner.MAX_ARTIFACT_READ_CHARS = orig_max_artifact
        with open(big_path, "w") as f:  # restore for anything reading it again below
            json.dump({"card_id": "x", "status": "BLOCKED", "changed_files": [], "tests": {},
                       "remaining_limitations": []}, f)

    # Flask route
    art_resp = client.get(f"/api/cardrunner/runs/{row1['id']}/artifact/evidence.md")
    check("route artifact: 200 with found content", art_resp.status_code == 200
          and art_resp.get_json()["found"] is True, art_resp.get_json())
    bad_name_resp = client.get(f"/api/cardrunner/runs/{row1['id']}/artifact/secrets.env")
    check("route artifact: disallowed name -> 400", bad_name_resp.status_code == 400, bad_name_resp.status_code)
    unknown_run_resp = client.get("/api/cardrunner/runs/999999999/artifact/evidence.md")
    check("route artifact: unknown run id -> 404", unknown_run_resp.status_code == 404, unknown_run_resp.status_code)

    # ══ Review of a superseded implementation snapshot (F5b): a review    ══
    # ══ must remain possible for a historical card even after a later    ══
    # ══ correction moves the lineage on — while IMPLEMENT against that   ══
    # ══ same superseded card stays refused, unchanged.                   ══
    def supersede(card_id):
        c = db()
        c.execute("UPDATE card_factory_cards SET is_current = 0 WHERE id = ?", (card_id,))
        c.commit()
        c.close()

    ask_sup = make_ask(project="cis", ask_text="a card that will be superseded")
    card_sup = make_card(ask_sup, ask_revision=1)
    row_sup_impl, _ = card_runner.dispatch(
        card_sup, "implement", "claude", request_id="r-sup-impl",
        expected_card_fingerprint=fp(), authorized_by="eric", accept_time_only_control=True,
        permitted_files=["runtime/sup.py"],
        _test_command=_claude_mock(os.path.join(tmp_root, "stdin_capture_sup.txt")),
    )
    row_sup_impl = wait_terminal(row_sup_impl["id"])
    check("superseded-card fixture: implementation completes", row_sup_impl["status"] == "completed", row_sup_impl)

    # A correction supersedes card_sup (a new revision becomes current) —
    # mirrors what card_factory_app.edit_card actually does to the old row.
    supersede(card_sup)
    bump_ask_revision(ask_sup, 2)

    try:
        card_runner.dispatch(
            card_sup, "implement", "claude", request_id="r-sup-implement-again",
            expected_card_fingerprint=fp(), authorized_by="eric", accept_time_only_control=True,
            permitted_files=["runtime/sup.py"],
        )
        check("IMPLEMENT against a superseded card stays refused — current-card check unchanged", False)
    except card_runner.RevisionMismatch:
        check("IMPLEMENT against a superseded card stays refused — current-card check unchanged", True)

    row_sup_review, dup_sup_review = card_runner.dispatch(
        card_sup, "review", "claude", request_id="r-sup-review",
        expected_card_fingerprint=fp(), authorized_by="eric", accept_time_only_control=True,
        review_of_run_id=row_sup_impl["id"],
        _test_command=_claude_mock(os.path.join(tmp_root, "stdin_capture_sup_review.txt"), message="PASS"),
    )
    check("REVIEW of that SAME superseded card's own implementation is allowed",
          dup_sup_review is False, dup_sup_review)
    row_sup_review = wait_terminal(row_sup_review["id"])
    check("historical review completes", row_sup_review["status"] == "completed", row_sup_review)
    check("the reviewed card_factory_card_id is still exactly the superseded one — never silently "
          "substituted for the new current card",
          row_sup_review["card_factory_card_id"] == card_sup, row_sup_review)

    passed = sum(1 for _, ok in results if ok)
    total = len(results)
    print(f"\n{passed}/{total} passed")
    shutil.rmtree(tmp_root, ignore_errors=True)
    if passed != total:
        sys.exit(1)


if __name__ == "__main__":
    run()
