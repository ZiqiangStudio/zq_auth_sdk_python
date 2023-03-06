import logging
import os
import re
from pathlib import Path
from typing import Optional

import auto_changelog
from auto_changelog.__main__ import generate_changelog
from auto_changelog.presenter import MarkdownPresenter
from auto_changelog.repository import GitRepository


def main(
    path_repo: str = "../",
    github: bool = True,
    title: str = "Changelog",
    description: str = "",
    latest_version: Optional[str] = None,
    unreleased: bool = True,
    template: str = "compact",
    diff_url: Optional[str] = None,
    issue_url: Optional[str] = None,
    issue_pattern: str = r"(#([\w-]+))",
    tag_prefix: str = "v",
    starting_commit: str = "",
    stopping_commit: str = "HEAD",
    debug: bool = False,
):
    changelog = get_all_changelog(
        debug,
        description,
        diff_url,
        github,
        issue_pattern,
        issue_url,
        latest_version,
        path_repo,
        starting_commit,
        stopping_commit,
        tag_prefix,
        template,
        title,
        unreleased,
    )

    new_content = get_new_content(changelog, tag_prefix)

    repo_path = Path(path_repo)
    changelog_path = repo_path / "CHANGELOG.md"
    if os.path.exists(changelog_path):
        with open(changelog_path, "r", encoding="utf8") as f:
            old_content = f.read()
    else:
        old_content = "# Changelog\n\n"

    old_content_list = old_content.split("\n## ")
    content_list = old_content_list[:1] + [new_content] + old_content_list[1:]
    content = "\n## ".join(content_list)

    with open(changelog_path, "w", encoding="utf8") as f:
        f.write(content)


def get_new_content(changelog, tag_prefix):
    changelog_list = changelog.split("\n## ")
    unreleased_content: str = changelog_list[1]
    if not unreleased_content.startswith("Unreleased"):
        logging.error("No unreleased content found")
        exit()
    unreleased_content = "__NEXT_VERSION__" + unreleased_content[10:]
    if len(changelog_list) == 2:  # no previous version
        return unreleased_content
    commit = re.findall(
        r"\n\nFull set of changes: \[`+"
        + tag_prefix
        + r"\d+.\d+.\d+...([0-9a-f]{7})`\]",
        unreleased_content,
    )[0]
    return unreleased_content.replace(commit, "__NEXT_VERSION__")


def get_all_changelog(
    debug,
    description,
    diff_url,
    github,
    issue_pattern,
    issue_url,
    latest_version,
    path_repo,
    starting_commit,
    stopping_commit,
    tag_prefix,
    template,
    title,
    unreleased,
):
    if debug:
        logging.basicConfig(level=logging.DEBUG)
        logging.debug("Logging level has been set to DEBUG")
    if github:
        auto_changelog.set_github()
    # Convert the repository name to an absolute path
    repo = os.path.abspath(path_repo)
    repository = GitRepository(
        repo,
        latest_version=latest_version,
        skip_unreleased=not unreleased,
        tag_prefix=tag_prefix,
    )
    presenter = MarkdownPresenter(template=template)
    changelog = generate_changelog(
        repository,
        presenter,
        title,
        description,
        issue_pattern=issue_pattern,
        issue_url=issue_url,
        diff_url=diff_url,
        starting_commit=starting_commit,
        stopping_commit=stopping_commit,
    )
    return changelog


if __name__ == "__main__":
    main(
        path_repo=r"..",
        stopping_commit="origin/master",
    )
