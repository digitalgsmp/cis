#!/usr/bin/env python3
"""draft -> review1 + review2 -> artifact on disk."""
import json, os, sys, time, hashlib, pathlib, urllib.request

STAGES = [
    ("draft",   8645, "deepseek-v4-pro", "CIS_DRAFT_API_KEY"),
    ("review1", 8643, "qwen3.7-max",     "CIS_REVIEW1_API_KEY"),
    ("review2", 8647, "glm-5.2",         "CIS_REVIEW2_API_KEY"),
]

def call(port, model, key, prompt):
    body = json.dumps({"model": model,
        "messages": [{"role": "user", "content": prompt}]}).encode()
    req = urllib.request.Request(
        "http://127.0.0.1:%d/v1/chat/completions" % port, data=body,
        headers={"Authorization": "Bearer " + key,
                 "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as r:
        d = json.loads(r.read())
    return d["choices"][0]["message"]["content"]

def main():
    topic = sys.argv[1]
    run_id = time.strftime("%Y%m%d_%H%M%S")
    out = pathlib.Path("/workspace/cis/artifacts") / run_id
    out.mkdir(parents=True, exist_ok=True)

    spec = call(8645, "deepseek-v4-pro",
                os.environ["CIS_DRAFT_API_KEY"], topic)
    (out / "draft.md").write_text(spec)
    print("DRAFT_WRITTEN", len(spec))

    rprompt = ("Review this spec. List blocking issues only, "
               "one per line, each citing a line of the spec. "
               "No preamble.\n\n" + spec)
    for name, port, model, envkey in STAGES[1:]:
        try:
            rev = call(port, model, os.environ[envkey], rprompt)
        except Exception as e:
            rev = "REVIEW_FAILED: %s" % e
        (out / (name + ".md")).write_text(rev)
        print(name.upper() + "_WRITTEN", len(rev))

    print("RUN_ID", run_id)
    print("ARTIFACTS", str(out))



if __name__ == "__main__":
    main()
