import py_compile

from livekit_agent.prompts import system_instructions, opening_greeting
from app.tradie import load_profile


def test_agent_compiles_without_livekit():
    # agent.py imports livekit only inside entrypoint — must byte-compile clean
    # on machines (like CI) without livekit installed.
    py_compile.compile("livekit_agent/agent.py", doraise=True)


def test_instructions_carry_ranges_never_finals():
    p = load_profile("knowledge/tradie_profile.yaml")
    s = system_instructions(p)
    assert "£950" in s and "£1400" in s  # ranges present
    assert "ranges only" in s and "survey" in s
    assert "safety first" in s
    g = opening_greeting(p, 23)
    assert "burning" in g and "evening" in g
    assert "morning" in opening_greeting(p, 9)
