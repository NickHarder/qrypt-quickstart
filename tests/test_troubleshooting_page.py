"""The troubleshooting page answers the error a developer is staring at.

RQ-06, RQ-12, RQ-15 and RQ-17 in docs/DELIVERABLES.md.
"""

import html
import re
from pathlib import Path
from typing import Final

import pytest

SITE: Final = Path(__file__).resolve().parents[1] / "site"
PAGE: Final = SITE / "troubleshooting.html"
SECTION_PATTERN: Final = re.compile(
    r'<section id="(?P<id>[a-z0-9-]+)"[^>]*>(?P<body>.*?)</section>', re.DOTALL
)
ERROR_SECTIONS: Final = [f"error-{code}" for code in (400, 401, 403, 429, 500, 503)]
MISTAKE_SECTIONS: Final = [
    "mistake-size-is-kib",
    "mistake-base64",
    "mistake-loop",
    "mistake-default-user-agent",
]
ENVIRONMENT_SECTIONS: Final = ["env-runtime", "env-missing-dotenv", "env-proxy-tls", "env-network"]


def sections() -> dict[str, str]:
    page = PAGE.read_text()
    return {
        match["id"]: html.unescape(re.sub(r"<[^>]+>", " ", match["body"]))
        for match in SECTION_PATTERN.finditer(page)
    }


@pytest.mark.parametrize("section_id", ERROR_SECTIONS + MISTAKE_SECTIONS + ENVIRONMENT_SECTIONS)
def test_each_problem_has_a_symptom_a_likely_cause_and_a_fix(section_id: str) -> None:
    section_text = sections()[section_id]
    for heading in ("Symptom", "Likely cause", "Fix"):
        assert heading in section_text, f"{section_id} has no {heading}"


def test_the_403_entry_puts_the_wrong_token_first_and_says_qrypt_documents_401() -> None:
    section_text = sections()["error-403"]
    assert "wrong token" in section_text
    assert "QRYPT_API_KEY" in section_text
    assert "Forbidden or entropy quota reached" in section_text
    assert "401" in section_text


def test_the_cloudflare_1010_entry_names_the_body_the_cause_and_the_fix() -> None:
    # Live, Cloudflare refused Python's default User-Agent with 403 error 1010 before Qrypt read the
    # token (evidence/live_probes.json, bad_token_python_default_client).
    section_text = sections()["mistake-default-user-agent"]
    for phrase in ("Error 1010: Access denied", "Python-urllib", "User-Agent", "Cloudflare"):
        assert phrase in section_text, phrase
    raw_sections = {
        match["id"]: match["body"] for match in SECTION_PATTERN.finditer(PAGE.read_text())
    }
    assert 'href="#mistake-default-user-agent"' in raw_sections["error-403"]


def test_the_key_handling_section_says_what_keeps_the_token_from_an_ai_agent() -> None:
    # Verified in the harness image (evidence/agent_token_guards.md): Claude Code's deny rules
    # stopped its file tool and its shell; Gemini CLI got the token through its shell regardless.
    section_text = sections()["key-handling"]
    for phrase in ("Read(./.env)", ".claude/settings.json", ".geminiignore", "cat", "new key"):
        assert phrase in section_text, phrase


def test_the_page_tells_the_rate_limit_from_the_allotment() -> None:
    page_sections = sections()
    assert "30 requests" in page_sections["error-429"]
    # Live, a trial key was refused far below the documented limit (evidence/live_rate_limit.json).
    assert "0.36 s" in page_sections["error-429"]
    assert "allotment" in page_sections["error-403"]
    assert "403" in page_sections["error-429"]
    assert "429" in page_sections["error-403"]


def test_the_proxy_fix_never_turns_off_certificate_checks() -> None:
    proxy_text = sections()["env-proxy-tls"]
    assert "SSL_CERT_FILE" in proxy_text
    assert "NODE_EXTRA_CA_CERTS" in proxy_text
    # The page must not hand a reader the switch that turns verification off, even as a warning.
    for unsafe_setting in ("NODE_TLS_REJECT_UNAUTHORIZED", "verify=False", "--insecure", "curl -k"):
        assert unsafe_setting not in PAGE.read_text()


def test_the_key_handling_rules_are_on_the_page() -> None:
    key_text = sections()["key-handling"]
    for rule in ("print", "log", "commit", "reuse"):
        assert rule in key_text


def test_the_quickstart_links_to_the_troubleshooting_page_and_back() -> None:
    assert 'href="troubleshooting.html"' in (SITE / "index.html").read_text()
    assert 'href="index.html"' in PAGE.read_text()
