"""Profile Qrypt's documented first-run contract, read only, for the audit in docs/AUDIT.md.

The audit's data is not a table but the contract a first-time developer reads: the Quantum Entropy
page at docs.qrypt.com, its examples, and what the site offers an agent (llms.txt, the sitemap).
This script fetches those public pages, never the API, and prints one line per fact the audit's
findings rest on, with what the page says. It sends no token and requests no entropy.

Run it from the repository's root:

    python3 -I docs/audit/qrypt_docs_profile.py

or replay a saved copy of the Quantum Entropy page offline:

    python3 -I docs/audit/qrypt_docs_profile.py --page-file saved-eaas.html

The last line is the SHA-256 of the page's text, so a later run shows whether the page changed.
"""

import argparse
import hashlib
import html
import re
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Final

DOCS_ROOT_URL: Final = "https://docs.qrypt.com"
ENTROPY_PAGE_URL: Final = f"{DOCS_ROOT_URL}/eaas/"
SDK_PAGE_URL: Final = f"{DOCS_ROOT_URL}/sdk/"
AGENT_INDEX_URL: Final = f"{DOCS_ROOT_URL}/llms.txt"
ROBOTS_URL: Final = f"{DOCS_ROOT_URL}/robots.txt"
SITEMAP_URL: Final = f"{DOCS_ROOT_URL}/sitemap.xml"
REQUEST_TIMEOUT_SECONDS: Final = 20
DOCUMENTED_ERROR_STATUSES: Final = ("400", "401", "403", "429", "500", "503")
EXAMPLE_HEADINGS: Final = ("Curl", "PowerShell", "Python", "JavaScript")


@dataclass(frozen=True)
class FetchedPage:
    """One page as the server answered it.

    Attributes:
        status_code: The HTTP status, or 0 when the request did not complete.
        body_text: The body decoded as UTF-8, empty when there was none.
    """

    status_code: int
    body_text: str


@dataclass(frozen=True)
class ProfileFact:
    """One fact of the contract, as the profile observed it.

    Attributes:
        fact_name: A short name for the fact, stable across runs.
        observed_value: What the page says or what the server answered.
    """

    fact_name: str
    observed_value: str


def fetch_page(page_url: str) -> FetchedPage:
    """Fetch one public documentation page, keeping the status of a failed answer.

    Args:
        page_url: An https URL under docs.qrypt.com.

    Returns:
        The page's status and body; status 0 when the network failed.
    """
    # Both noqa: S310 below: the URL is one of this module's https constants, never user input.
    request = urllib.request.Request(page_url, headers={"User-Agent": "qrypt-audit"})  # noqa: S310
    try:
        with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:  # noqa: S310
            response_bytes: bytes = response.read()
            return FetchedPage(
                status_code=response.status, body_text=response_bytes.decode("utf-8")
            )
    except urllib.error.HTTPError as http_error:
        return FetchedPage(status_code=http_error.code, body_text="")
    except urllib.error.URLError:
        return FetchedPage(status_code=0, body_text="")


def html_to_text(page_html: str) -> str:
    """Reduce a page's HTML to its visible text, one block a line.

    Args:
        page_html: The page's HTML.

    Returns:
        The text a reader sees, with blank lines collapsed.
    """
    without_scripts = re.sub(r"(?s)<(script|style)[^>]*>.*?</\1>", "", page_html)
    with_line_breaks = re.sub(r"<br\s*/?>|</(p|div|h\d|li|tr|pre|code)>", "\n", without_scripts)
    without_tags = re.sub(r"<[^>]+>", "", with_line_breaks)
    unescaped_text = html.unescape(without_tags)
    return re.sub(r"\n\s*\n+", "\n", unescaped_text)


def example_section(page_text: str, heading: str) -> str:
    """Return the text of one example, from its heading to the next example's heading.

    Args:
        page_text: The Quantum Entropy page's text.
        heading: One of EXAMPLE_HEADINGS.

    Returns:
        The example's text, empty when the heading is not on the page.
    """
    examples_start = page_text.find("\nExamples\n")
    examples_text = page_text[examples_start:] if examples_start >= 0 else ""
    heading_pattern = "|".join(EXAMPLE_HEADINGS)
    section_match = re.search(
        rf"\n{heading}\n(.*?)(?=\n(?:{heading_pattern})\n|\Z)", examples_text, flags=re.DOTALL
    )
    return section_match.group(1) if section_match else ""


def contract_facts(page_text: str) -> list[ProfileFact]:
    """Read the facts the audit rests on from the Quantum Entropy page's text.

    Args:
        page_text: The page's visible text.

    Returns:
        One fact per line of the profile, in a stable order.
    """
    single_line_text = re.sub(r"\s+", " ", page_text)
    statuses_listed = [
        status for status in DOCUMENTED_ERROR_STATUSES if f" {status} " in single_line_text
    ]
    examples_with_accept = [
        f"{heading}={'yes' if 'Accept' in example_section(page_text, heading) else 'no'}"
        for heading in EXAMPLE_HEADINGS
    ]
    region_subdomains = sorted(set(re.findall(r"\b(api-[a-z]+)\b", page_text)))
    allotment_sentence_match = re.search(r"maximum allotment[^.]*\.", single_line_text)
    allotment_sentence = allotment_sentence_match.group(0) if allotment_sentence_match else ""
    python_example = example_section(page_text, "Python")
    javascript_example = example_section(page_text, "JavaScript")
    powershell_example = example_section(page_text, "PowerShell")
    return [
        ProfileFact(
            "size range stated",
            str("minimum value is 1 and the maximum value is 512" in single_line_text),
        ),
        ProfileFact(
            "size default stated as 1", str("default value is one (1)" in single_line_text)
        ),
        ProfileFact("size unit is KiB", str("kibibytes (1,024 bytes)" in single_line_text)),
        ProfileFact(
            "Accept header in the request table", str("Accept (header)" in single_line_text)
        ),
        ProfileFact("Accept header in each example", ", ".join(examples_with_accept)),
        ProfileFact("error statuses listed", ", ".join(statuses_listed)),
        ProfileFact(
            "rate limit 30 per 10 seconds",
            str("(30)" in single_line_text and "(10 seconds)" in single_line_text),
        ),
        ProfileFact("Retry-After mentioned", str("Retry-After" in single_line_text)),
        ProfileFact(
            "error body shape documented",
            str(re.search(r'"(error|message)"', page_text) is not None),
        ),
        ProfileFact(
            "status for a missing Accept stated",
            str(re.search(r"without[^.]*Accept", single_line_text) is not None),
        ),
        ProfileFact(
            "allotment amount stated", str(re.search(r"\d", allotment_sentence) is not None)
        ),
        ProfileFact("region subdomains", ", ".join(region_subdomains)),
        ProfileFact("token obtained by contacting Qrypt", str("contact us" in single_line_text)),
        ProfileFact("portal registration linked", str("portal.qrypt.com/register" in page_text)),
        ProfileFact(
            "Python example writes the token in source", str("accesstoken = '" in python_example)
        ),
        ProfileFact(
            "Python example prints every entropy byte", str("print( f'{b}')" in python_example)
        ),
        ProfileFact(
            "Python example checks the status",
            str("status_code" in python_example or "raise_for_status" in python_example),
        ),
        ProfileFact(
            "JavaScript example checks the status",
            str("response.ok" in javascript_example or ".status" in javascript_example),
        ),
        ProfileFact(
            "JavaScript size placeholder spelled { kib_entropy }",
            str("{ kib_entropy }" in javascript_example),
        ),
        ProfileFact(
            "PowerShell reads response.random without $",
            str(re.search(r"(?<!\$)\bresponse\.random", powershell_example) is not None),
        ),
        ProfileFact(
            "NIST, SP 800-22 or ESV mentioned",
            str(re.search(r"NIST|800-22|ESV", single_line_text) is not None),
        ),
        ProfileFact("words 'truly random' on the page", str("truly random" in single_line_text)),
    ]


def site_facts() -> list[ProfileFact]:
    """Read what the documentation site offers an agent: llms.txt, robots.txt, the sitemap, the SDK.

    Returns:
        One fact per probe, in a stable order.
    """
    agent_index_page = fetch_page(AGENT_INDEX_URL)
    robots_page = fetch_page(ROBOTS_URL)
    sitemap_page = fetch_page(SITEMAP_URL)
    sdk_page = fetch_page(SDK_PAGE_URL)
    sitemap_hosts = sorted(set(re.findall(r"<loc>(https?://[^/<]+)", sitemap_page.body_text)))
    sdk_quickstart_paths = sorted(
        set(re.findall(r"<loc>[^<]*?(/sdk/quickstarts/[^<]+)</loc>", sitemap_page.body_text))
    )
    return [
        ProfileFact("llms.txt status", str(agent_index_page.status_code)),
        ProfileFact("robots.txt status", str(robots_page.status_code)),
        ProfileFact("sitemap hosts", ", ".join(sitemap_hosts)),
        ProfileFact("SDK quickstart pages in the sitemap", ", ".join(sdk_quickstart_paths)),
        ProfileFact(
            "SDK page names a 'Qrypt SDK'", str("Qrypt SDK" in html_to_text(sdk_page.body_text))
        ),
    ]


def main() -> int:
    """Print the profile, one fact a line, then the page's SHA-256.

    Returns:
        0 when the Quantum Entropy page was read, 1 when it could not be.
    """
    argument_parser = argparse.ArgumentParser(
        description=__doc__.splitlines()[0] if __doc__ else None
    )
    argument_parser.add_argument(
        "--page-file", help="a saved copy of the Quantum Entropy page's HTML"
    )
    parsed_arguments = argument_parser.parse_args()
    page_file: str | None = parsed_arguments.page_file
    if page_file is not None:
        with Path(page_file).open(encoding="utf-8") as saved_page:
            entropy_page = FetchedPage(status_code=200, body_text=saved_page.read())
    else:
        entropy_page = fetch_page(ENTROPY_PAGE_URL)
    if entropy_page.status_code != 200:
        sys.stderr.write(f"the Quantum Entropy page answered {entropy_page.status_code}\n")
        return 1
    page_text = html_to_text(entropy_page.body_text)
    all_facts = [ProfileFact("Quantum Entropy page status", str(entropy_page.status_code))]
    all_facts.extend(contract_facts(page_text))
    if page_file is None:
        all_facts.extend(site_facts())
    for fact in all_facts:
        sys.stdout.write(f"{fact.fact_name}: {fact.observed_value}\n")
    page_text_digest = hashlib.sha256(page_text.encode("utf-8")).hexdigest()
    sys.stdout.write(f"page text sha256: {page_text_digest}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
