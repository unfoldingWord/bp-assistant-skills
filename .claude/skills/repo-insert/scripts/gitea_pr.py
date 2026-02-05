#!/usr/bin/env python3
"""
gitea_pr.py - Create a pull request on git.door43.org via the Gitea API.

Usage:
  python3 gitea_pr.py \
    --repo en_ult \
    --head psa-119-100-104 \
    --base auto-deferredreward-PSA \
    --title "PSA 119:100-104 AI ULT"

Reads DOOR43_TOKEN from .env file in the project root.
"""

import argparse
import json
import os
import sys
import urllib.request
import urllib.error

GITEA_API = "https://git.door43.org/api/v1"
ORG = "unfoldingWord"


def load_env(env_path=None):
    """Load variables from a .env file."""
    if env_path is None:
        # Walk up from script location to find .env
        d = os.path.dirname(os.path.abspath(__file__))
        for _ in range(6):
            candidate = os.path.join(d, '.env')
            if os.path.exists(candidate):
                env_path = candidate
                break
            d = os.path.dirname(d)

    if env_path is None or not os.path.exists(env_path):
        return {}

    env = {}
    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' in line:
                key, val = line.split('=', 1)
                env[key.strip()] = val.strip()
    return env


def create_pr(token, repo, head, base, title, body=""):
    """Create a pull request via Gitea API."""
    url = f"{GITEA_API}/repos/{ORG}/{repo}/pulls"
    data = json.dumps({
        "title": title,
        "head": head,
        "base": base,
        "body": body,
    }).encode('utf-8')

    req = urllib.request.Request(url, data=data, method='POST')
    req.add_header('Content-Type', 'application/json')
    req.add_header('Authorization', f'token {token}')

    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            return result
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        print(f"ERROR: Gitea API returned {e.code}", file=sys.stderr)
        print(f"  {error_body}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description='Create a pull request on git.door43.org'
    )
    parser.add_argument('--repo', required=True,
                        help='Repository name (e.g., en_ult, en_ust, en_tn)')
    parser.add_argument('--head', required=True,
                        help='Source branch name')
    parser.add_argument('--base', required=True,
                        help='Target branch name')
    parser.add_argument('--title', required=True,
                        help='Pull request title')
    parser.add_argument('--body', default='',
                        help='Pull request description')

    args = parser.parse_args()

    # Get token
    env = load_env()
    token = os.environ.get('DOOR43_TOKEN') or env.get('DOOR43_TOKEN')

    if not token:
        print("ERROR: No DOOR43_TOKEN found.", file=sys.stderr)
        print("Set it in .env or as an environment variable.", file=sys.stderr)
        print("Create a token at: https://git.door43.org/user/settings/applications",
              file=sys.stderr)
        sys.exit(1)

    result = create_pr(token, args.repo, args.head, args.base, args.title, args.body)

    pr_url = result.get('html_url', '')
    pr_number = result.get('number', '?')
    print(f"PR #{pr_number} created: {pr_url}")


if __name__ == '__main__':
    main()
