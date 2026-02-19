#!/usr/bin/env python3
"""
gitea_pr.py - Create (and optionally merge) a pull request on git.door43.org.

Usage:
  python3 gitea_pr.py \
    --repo en_tn \
    --head AI-PSA-120 \
    --base master \
    --title "AI TN for PSA 120 [deferredreward]" \
    --merge

Token lookup order (.env files first -- env vars may be stale in Docker):
  1. DOOR43_TOKEN in project-root .env (walks up from script location)
  2. GITEA_TOKEN in project-root .env
  3. DOOR43_TOKEN in config/.env
  4. GITEA_TOKEN in config/.env
  5. DOOR43_TOKEN env var (lowest priority)
  6. GITEA_TOKEN env var (lowest priority)
"""

import argparse
import json
import os
import sys
import time
import urllib.request
import urllib.error

GITEA_API = "https://git.door43.org/api/v1"
ORG = "unfoldingWord"
SERVER_ENV = "config/.env"


def load_env(env_path):
    """Load variables from a .env file. Returns {} if file missing."""
    if not env_path or not os.path.exists(env_path):
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


def find_project_env():
    """Walk up from script location to find the nearest .env file."""
    d = os.path.dirname(os.path.abspath(__file__))
    for _ in range(6):
        candidate = os.path.join(d, '.env')
        if os.path.exists(candidate):
            return candidate
        d = os.path.dirname(d)
    return None


def get_token():
    """Return the API token, trying multiple sources.

    .env files are checked first because env vars may be inherited stale
    from a Docker image while .env files are mounted fresh.
    """
    # 1-2. Project-root .env (highest priority -- user-controlled file)
    proj_path = find_project_env()
    project_env = load_env(proj_path)
    token = project_env.get('DOOR43_TOKEN') or project_env.get('GITEA_TOKEN')
    if token:
        key = 'DOOR43_TOKEN' if project_env.get('DOOR43_TOKEN') else 'GITEA_TOKEN'
        print(f"Token: {key} from {proj_path}", file=sys.stderr)
        return token

    # 3-4. Server config .env
    server_env = load_env(SERVER_ENV)
    token = server_env.get('DOOR43_TOKEN') or server_env.get('GITEA_TOKEN')
    if token:
        key = 'DOOR43_TOKEN' if server_env.get('DOOR43_TOKEN') else 'GITEA_TOKEN'
        print(f"Token: {key} from {SERVER_ENV}", file=sys.stderr)
        return token

    # 5-6. Env vars (lowest priority -- may be stale in Docker)
    token = os.environ.get('DOOR43_TOKEN') or os.environ.get('GITEA_TOKEN')
    if token:
        key = 'DOOR43_TOKEN' if os.environ.get('DOOR43_TOKEN') else 'GITEA_TOKEN'
        print(f"Token: {key} from environment variable (may be stale)", file=sys.stderr)
        return token

    return None


def api_request(method, path, token, data=None):
    """Make a Gitea API request. Returns (status_code, response_body)."""
    url = f"{GITEA_API}{path}"
    body = json.dumps(data).encode('utf-8') if data else None
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header('Content-Type', 'application/json')
    req.add_header('Authorization', f'token {token}')
    try:
        with urllib.request.urlopen(req) as response:
            raw = response.read().decode('utf-8')
            return response.status, json.loads(raw) if raw.strip() else {}
    except urllib.error.HTTPError as e:
        raw = e.read().decode('utf-8')
        return e.code, json.loads(raw) if raw.strip() else {}


def create_or_get_pr(token, repo, head, base, title, body=""):
    """Create a PR; if one already exists return its number."""
    status, result = api_request(
        'POST',
        f"/repos/{ORG}/{repo}/pulls",
        token,
        {"title": title, "head": head, "base": base, "body": body},
    )
    if status in (200, 201):
        return result['number'], result.get('html_url', '')
    if status == 409:
        # Already exists — extract id from message
        msg = result.get('message', '')
        # message contains "id: NNNN, issue_id: MMMM"
        import re
        m = re.search(r'issue_id:\s*(\d+)', msg)
        if m:
            pr_number = int(m.group(1))
            print(f"PR already exists: #{pr_number}")
            return pr_number, f"https://git.door43.org/{ORG}/{repo}/pulls/{pr_number}"
    print(f"ERROR: Gitea API returned {status}", file=sys.stderr)
    print(f"  {result}", file=sys.stderr)
    sys.exit(1)


def merge_pr(token, repo, pr_number, message=""):
    """Merge the PR. Returns True on success (including already-merged)."""
    status, result = api_request(
        'POST',
        f"/repos/{ORG}/{repo}/pulls/{pr_number}/merge",
        token,
        {"Do": "merge", "merge_message_field": message},
    )
    if status in (200, 204):
        return True
    # 405 means the PR is not mergeable -- typically already merged
    if status == 405:
        print(f"PR #{pr_number} is already merged (or not mergeable).")
        return True
    print(f"ERROR: Merge failed with status {status}", file=sys.stderr)
    print(f"  {result}", file=sys.stderr)
    sys.exit(1)


def delete_branch(token, repo, branch):
    """Delete a remote branch via the Gitea API."""
    status, result = api_request(
        'DELETE',
        f"/repos/{ORG}/{repo}/branches/{branch}",
        token,
    )
    if status in (200, 204):
        return True
    # 404 means already gone — that's fine
    if status == 404:
        return True
    print(f"WARNING: Could not delete branch {branch}: {status} {result}", file=sys.stderr)
    return False


def main():
    parser = argparse.ArgumentParser(
        description='Create (and optionally merge) a PR on git.door43.org'
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
    parser.add_argument('--merge', action='store_true',
                        help='Merge the PR immediately after creating it')
    parser.add_argument('--no-delete', action='store_true',
                        help='Skip deleting the head branch after merge')

    args = parser.parse_args()

    token = get_token()
    if not token:
        print("ERROR: No API token found.", file=sys.stderr)
        print("Set DOOR43_TOKEN in .env or as an environment variable.", file=sys.stderr)
        print("Create a token at: https://git.door43.org/user/settings/applications",
              file=sys.stderr)
        sys.exit(1)

    pr_number, pr_url = create_or_get_pr(
        token, args.repo, args.head, args.base, args.title, args.body
    )
    print(f"PR #{pr_number} created: {pr_url}")

    if args.merge:
        merge_message = f"Merge {args.title}"
        merge_pr(token, args.repo, pr_number, merge_message)
        print(f"PR #{pr_number} merged.")

        if not args.no_delete:
            deleted = delete_branch(token, args.repo, args.head)
            if deleted:
                print(f"Branch {args.head} deleted.")


if __name__ == '__main__':
    main()
