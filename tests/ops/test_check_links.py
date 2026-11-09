"""The Markdown link checker."""

from check_links import anchors, broken_links, slug


def test_slug_matches_github_anchors():
    assert slug("How the notebooks work") == "how-the-notebooks-work"
    assert slug("1. Setup") == "1-setup"
    assert slug("Results: `n = 73`") == "results-n--73"


def test_repeated_headings_get_numbered_anchors():
    assert anchors("# A\n## A\n```\n# not a heading\n```\n") == {"a", "a-1"}


def test_broken_files_and_headings_are_reported_and_good_links_pass(tmp_path):
    (tmp_path / "other.md").write_text("# Real heading\n", encoding="utf-8")
    page = tmp_path / "page.md"
    page.write_text(
        "[ok](other.md) [ok](other.md#real-heading) [ok](#top) [web](https://example.com/x)\n"
        "[gone](missing.md) [bad](other.md#nope) `[code](ignored.md)`\n# Top\n",
        encoding="utf-8")
    assert broken_links([page], root=tmp_path) == [
        "page.md: missing.md (no such file)",
        "page.md: other.md#nope (no such heading)",
    ]
