"""Derive the GitHub presentation of the Stellaegis organization from what its repositories publish.

- The description of the organization is the first sentence of profile/README.md, without its subject.
- The "About" of each code repository is the first sentence of its README.md, without markdown.
- Its topics are the <PackageTags> of its packages, without "stellaegis", plus "dotnet" and "csharp", minus
  a short list of words too generic to help a search.

A README whose first sentence changes therefore changes the "About" of its repository. Nothing here is written
by hand on GitHub.

Usage, from anywhere:

    py -3 -B scripts/sync-about.py [--root <folder>] [--apply]

--root is the folder holding a clone of every code repository, each named after the repository without its
"Stellaegis." prefix, in lower case (Stellaegis.Caching -> caching). It defaults to the parent of this
repository. Without --apply the script only prints the differences. It needs the GitHub CLI, signed in with
the right to edit the organization and its repositories.
"""

import argparse
import json
import pathlib
import re
import subprocess
import sys

ORG = "Stellaegis"
PROFILE_REPO = ".github"
ORG_DESCRIPTION_MAX = 160
ABOUT_MAX = 350
TOPICS_MAX = 20
ADDED_TOPICS = {"dotnet", "csharp"}
STOP_TOPICS = {"stellaegis", "client", "http", "hub", "pages", "bounded", "guard", "result", "options",
               "modules", "database", "composition", "journal", "admission", "validation", "cache"}

HERE = pathlib.Path(__file__).resolve().parent.parent


def gh(*args, input=None):
    result = subprocess.run(["gh", *args], input=input, capture_output=True, text=True, encoding="utf-8")
    if result.returncode != 0:
        sys.exit(f"gh {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout


def first_sentence(readme: pathlib.Path) -> str:
    """The first sentence of the first paragraph after the title, skipping a language switch line."""
    paragraphs, current = [], []
    for line in readme.read_text(encoding="utf-8").splitlines()[1:]:
        if line.strip():
            current.append(line.strip())
        elif current:
            paragraphs.append(" ".join(current))
            current = []
    if current:
        paragraphs.append(" ".join(current))
    paragraph = next(p for p in paragraphs if not re.match(r"^\[?English\]?", p))
    match = re.search(r"^(.+?[.])(\s+[A-Z`]|$)", paragraph)
    sentence = match.group(1) if match else paragraph
    sentence = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", sentence)
    return sentence.replace("**", "").replace("`", "")


def topics(repo_folder: pathlib.Path) -> list[str]:
    tags = set()
    for project in (repo_folder / "src").glob("*/*.csproj"):
        match = re.search(r"<PackageTags>([^<]*)</PackageTags>", project.read_text(encoding="utf-8"))
        if match:
            tags.update(tag.strip().lower() for tag in match.group(1).split(";") if tag.strip())
    return sorted((tags | ADDED_TOPICS) - STOP_TOPICS)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=pathlib.Path, default=HERE.parent)
    parser.add_argument("--apply", action="store_true")
    options = parser.parse_args()

    changes = 0

    # The organization.
    sentence = first_sentence(HERE / "profile" / "README.md")
    wanted = re.sub(rf"^{ORG} is (\w)", lambda m: m.group(1).upper(), sentence)
    if len(wanted) > ORG_DESCRIPTION_MAX:
        sys.exit(f"Organization description is {len(wanted)} characters, GitHub allows {ORG_DESCRIPTION_MAX}.")
    current = json.loads(gh("api", f"orgs/{ORG}"))["description"] or ""
    if current != wanted:
        changes += 1
        print(f"organization\n  now : {current}\n  want: {wanted}")
        if options.apply:
            gh("api", "-X", "PATCH", f"orgs/{ORG}", "-f", f"description={wanted}")

    # The code repositories.
    repos = json.loads(gh("repo", "list", ORG, "--limit", "100", "--json", "name,description,repositoryTopics"))
    for repo in sorted(repos, key=lambda r: r["name"]):
        name = repo["name"]
        if name == PROFILE_REPO:
            continue
        folder = options.root / name.removeprefix(f"{ORG}.").lower()
        if not (folder / "README.md").is_file():
            print(f"{name}: no clone at {folder}, skipped")
            continue

        about = first_sentence(folder / "README.md")
        if len(about) > ABOUT_MAX:
            sys.exit(f"{name}: the first sentence of its README is {len(about)} characters, GitHub allows {ABOUT_MAX}.")
        wanted_topics = topics(folder)
        if len(wanted_topics) > TOPICS_MAX:
            sys.exit(f"{name}: {len(wanted_topics)} topics, GitHub allows {TOPICS_MAX}.")
        current_topics = sorted(t["name"] for t in (repo["repositoryTopics"] or []))

        if (repo["description"] or "") != about:
            changes += 1
            print(f"{name} about\n  now : {repo['description']}\n  want: {about}")
            if options.apply:
                gh("repo", "edit", f"{ORG}/{name}", "--description", about)
        if current_topics != wanted_topics:
            changes += 1
            print(f"{name} topics\n  now : {' '.join(current_topics)}\n  want: {' '.join(wanted_topics)}")
            if options.apply:
                gh("api", "-X", "PUT", f"repos/{ORG}/{name}/topics", "--input", "-",
                   input=json.dumps({"names": wanted_topics}))

    if not changes:
        print("Nothing to change: GitHub matches the repositories.")
    elif not options.apply:
        print(f"{changes} difference(s). Run again with --apply to write them to GitHub.")


if __name__ == "__main__":
    main()
