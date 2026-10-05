#!/usr/bin/env python3
"""Publish one release announcement to GitHub Discussions using GITHUB_TOKEN."""
from __future__ import annotations

import argparse
import json
import os
import urllib.request


def graphql(query: str, variables: dict) -> dict:
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise RuntimeError("GITHUB_TOKEN is not set")
    request = urllib.request.Request("https://api.github.com/graphql", data=json.dumps({"query": query, "variables": variables}).encode(), headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json", "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(request, timeout=30) as response:
        data = json.loads(response.read().decode())
    if data.get("errors"):
        raise RuntimeError(json.dumps(data["errors"], ensure_ascii=False))
    return data["data"]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--owner", required=True)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--body-file", required=True)
    args = parser.parse_args()
    body = open(args.body_file, encoding="utf-8").read()
    repo = graphql("query($owner:String!,$repo:String!){repository(owner:$owner,name:$repo){id discussionCategories(first:20){nodes{id name}}}}", {"owner": args.owner, "repo": args.repo})["repository"]
    categories = repo["discussionCategories"]["nodes"]
    category = next((item for item in categories if item["name"].lower() in {"announcements", "general"}), None)
    if not category:
        raise RuntimeError("No Announcements or General discussion category exists")
    result = graphql("mutation($repoId:ID!,$categoryId:ID!,$title:String!,$body:String!){createDiscussion(input:{repositoryId:$repoId,categoryId:$categoryId,title:$title,body:$body}){discussion{url}}}", {"repoId": repo["id"], "categoryId": category["id"], "title": args.title, "body": body})
    print(result["createDiscussion"]["discussion"]["url"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
