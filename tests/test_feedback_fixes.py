import json

from app import ittools
from app.guard import check
from app.llm import parse_json_answer
from app.pii import scrub_all, scrub_secrets


def test_pii_tiers():
    assert "hunter2" not in scrub_secrets("password: hunter2")
    assert "sk-abc123XYZ" not in scrub_secrets("key sk-abc123XYZ here")
    assert "[REDACTED_CONTACT]" in scrub_all("email hunter@example.com")
    assert "[REDACTED_CONTACT]" in scrub_all("call 07700900111")
    assert "[REDACTED_CONTACT]" in scrub_all("lives at E2 8AA")


def test_store_and_case_drop_secrets_keep_callbacks(tmp_path):
    from app.store import Store
    from app.cases import CaseStore
    import app.cases as C
    s = Store(str(tmp_path / "s.db"))
    s.add_message("s1", "user", "my password: hunter2, call 07700900111", {})
    assert "hunter2" not in s.history("s1")[0]["content"]
    assert "07700900111" in s.history("s1")[0]["content"]  # callbacks need it
    cs = CaseStore(str(tmp_path / "cases"))
    case = C.new_case("x", "web")
    C.apply(case, {"type": "observation.added",
                   "payload": {"otype": "text", "value": "token=abc, phone 07700900111",
                               "confidence": 1.0}})
    cs.save(case)
    raw = cs._file(case["case_id"]).read_text()
    assert "token=abc" not in raw and "07700900111" in raw


def test_price_tripwire():
    assert check("That will cost £950 all in.")["reasons"] == ["price-fabrication"]
    assert check("Rough range £950-£1400 incl cert, valid 14 days.")["trip"] is False
    assert check("Callout £65/hr weekdays.")["trip"] is False
    assert check("OZEV grant (£350) is renters/flats only.")["trip"] is False


def test_confirm_128bit_and_rate_limit(monkeypatch):
    monkeypatch.setenv("IT_RESTART_ALLOWLIST", "")
    ittools.OUTSTANDING.clear()
    ittools.ATTEMPTS.clear()
    p = ittools.propose("s-rate", "clear_dns_cache", {})
    assert p["ok"] and len(p["confirm_token"].split("_", 1)[1]) == 32  # 128-bit hex
    for _ in range(5):
        ittools.execute("s-rate", "bogus")
    assert ittools.execute("s-rate", "bogus")["ok"] is False
    assert "too many" in ittools.execute("s-rate", "bogus")["error"]


def test_restart_allowlist_and_action_scan(monkeypatch):
    monkeypatch.setenv("IT_RESTART_ALLOWLIST", "")
    r = ittools.propose("s", "restart_process", {"process": "nginx"})
    assert r["ok"] is False and "allowlist" in r["error"]
    monkeypatch.setenv("IT_RESTART_ALLOWLIST", "nginx")
    assert ittools.propose("s", "restart_process", {"process": "nginx"})["ok"] is True
    assert ittools.propose("s", "delete_files", {})["tier"] == "critical"
    assert ittools.propose("s", "x", {"note": "pass_word please"})["tier"] == "critical"


def test_sqlite_backed_tokens_survive_restart(monkeypatch, tmp_path):
    monkeypatch.setattr(ittools, "STATE_DB", tmp_path / "st.db")
    ittools.OUTSTANDING.clear()
    ittools.ATTEMPTS.clear()
    p = ittools.propose("s-db", "clear_dns_cache", {})
    ittools.OUTSTANDING.clear()  # simulate process restart
    e = ittools.execute("s-db", p["confirm_token"])
    assert "action" in e  # token honored from SQLite, not memory


def test_diagnose_input_validation():
    assert ittools.diagnose("ping_gateway", {"host": "8.8.8.8; rm -rf"})["ok"] is False
    assert ittools.diagnose("read_logs", {"unit": "../../etc/passwd"})["ok"] is False


def test_parse_json_nested():
    txt = 'Sure! {"answer": "hi", "tool_args": {"a": {"b": 1}}, "confidence": 0.9} bye'
    obj = parse_json_answer(txt)
    assert obj and obj["tool_args"] == {"a": {"b": 1}} and obj["tool"] is None
    assert parse_json_answer("no json here") is None


def test_env_example_covers_settings():
    import re
    keys = set(re.findall(r"^([A-Z_]+)=", open(".env.example").read(), re.M))
    for k in ["BUSINESS_CONFIG", "LLM_PROVIDER", "LLM_BASE_URL", "LLM_API_KEY",
              "LLM_MODEL", "TTS_PROVIDER", "SPARKY_API_KEYS",
              "IT_RESTART_ALLOWLIST", "SUPPLIER_MCP_URL", "RETAIN_CASE_DAYS"]:
        assert k in keys, k
