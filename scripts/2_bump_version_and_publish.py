import logging
import os
import re
import subprocess
from pathlib import Path

SRC_FOLDER = "zq_auth_sdk"
ROOT_FOLDER = Path(__file__).resolve().parent.parent
os.chdir(ROOT_FOLDER)


def ask_confirm(text):
    while True:
        answer = input(f"{text} [y/n]: ").lower()
        if answer in ("j", "y", "ja", "yes"):
            return True
        if answer in ("n", "no", "nein"):
            return False


def set_version():
    """
    - reads and validates version number
    - updates __version__.py
    - updates pyproject.toml
    - Searches for '__NEXT_VERSION__' in changelog and replaces it with current version and date
    """
    from zq_auth_sdk import __version__ as current_version

    print(f"Current version is {current_version}.")

    version_list = current_version.split(".")
    version_bump_1 = ".".join(
        version_list[:-1] + [str(int(version_list[-1]) + 1)]
    )
    version_bump_2 = ".".join(
        version_list[:-2] + [str(int(version_list[-2]) + 1), "0"]
    )
    version_bump_3 = ".".join([str(int(version_list[0]) + 1), "0", "0"])
    print(
        f"Possible version bumps:\n "
        f"\t[1] {version_bump_1}\n"
        f"\t[2] {version_bump_2}\n"
        f"\t[3] {version_bump_3}"
    )
    print("Please select a version bump [1/2/3 or else] (default 1): ", end="")
    version_bump = input()
    if version_bump == "1" or version_bump == "":
        version = version_bump_1
    elif version_bump == "2":
        version = version_bump_2
    elif version_bump == "3":
        version = version_bump_3
    else:
        version = version_bump

    # validate and remove 'v' if present
    version = version.lower()
    if not re.match(r"v?\d+\.\d+.*", version):
        return
    if version.startswith("v"):
        version = version[1:]

    # safety check
    if not ask_confirm(f"Creating version v{version}. Continue?"):
        return

    # update library version
    versionfile = ROOT_FOLDER / SRC_FOLDER / "__init__.py"
    with open(versionfile, "r") as f:
        content = f.read()

    with open(versionfile, "w") as f:
        print(f"Updating {versionfile}")
        f.write(
            re.sub(r"__version__ = .*", f'__version__ = "{version}"', content)
        )

    # update poetry version
    print("Updating pyproject.toml")
    subprocess.run(["poetry", "version", version], check=True)

    # update changelog
    print("Updating CHANGELOG.md")
    with open(ROOT_FOLDER / "CHANGELOG.md", "r", encoding="utf8") as f:
        changelog = f.read()
        if "__NEXT_VERSION__" not in changelog:
            logging.warning("Could not find __NEXT_VERSION__ in CHANGELOG.md")
    changelog = changelog.replace("__NEXT_VERSION__", f"v{version}")
    with open(ROOT_FOLDER / "CHANGELOG.md", "w", encoding="utf8") as f:
        f.write(changelog)

    commit_content = f"build: bump version to v{version}"

    # check if commit
    command = 'git log HEAD -n 1 --pretty=format:"%s"'
    commit_message = subprocess.check_output(command, shell=True).decode(
        "utf-8"
    )
    while commit_message != commit_content:
        if ask_confirm(f"Waiting for commit changes\n\n{commit_content}\n\n"):
            pass
        commit_message = subprocess.check_output(command, shell=True).decode(
            "utf-8"
        )

    print("Success.")

    return version


def publish(version):
    """
    - reads version
    - reads changes from changelog
    - creates git tag
    - pushes to github
    - publishes on pypi
    - creates github release
    """

    if not ask_confirm(f"Publishing version {version}. Is this correct?"):
        return

    print("Running the tests")
    os.system("python runtests.py --coverage-local")

    # create git tag ('vXXX')
    if ask_confirm("Create tag?"):
        subprocess.run(["git", "tag", "-a", f"v{version}", "-m", f"v{version}"])

    # push to github
    if ask_confirm("Push to github?"):
        print("Pushing to github")
        subprocess.run(["git", "push", "--follow-tags"], check=True)

    print("Success.")


if __name__ == "__main__":
    version = set_version()
    publish(version)
