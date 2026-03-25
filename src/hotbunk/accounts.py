"""Account management -- credential storage, switching, and policy."""

import json
import shutil
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

import yaml


HOTBUNK_DIR = Path.home() / ".hotbunk"
ACCOUNTS_DIR = HOTBUNK_DIR / "accounts"
CONFIG_PATH = HOTBUNK_DIR / "config.yaml"
CLAUDE_DIR = Path.home() / ".claude"
CLAUDE_CREDS = CLAUDE_DIR / ".credentials.json"


@dataclass
class AccountPolicy:
    """What an account owner consents to."""

    owner: str
    email: str
    interactive_priority: str = "always"
    allow_automated: bool = True
    automated_types: list[str] = field(default_factory=lambda: ["militia", "training", "ci"])
    sleep_window: Optional[str] = None  # "22:00-06:00"
    availability: str = "always"  # always | workdays | weekdays | custom
    max_automated_concurrent: int = 2

    def to_yaml(self) -> str:
        return yaml.dump(asdict(self), default_flow_style=False, sort_keys=False)

    @classmethod
    def from_yaml(cls, path: Path) -> "AccountPolicy":
        with open(path) as f:
            data = yaml.safe_load(f)
        return cls(**data)


@dataclass
class AccountInfo:
    """Runtime info about an account."""

    name: str
    email: str
    subscription_type: str
    rate_limit_tier: str
    has_credentials: bool
    policy: Optional[AccountPolicy] = None


class AccountManager:
    """Manages multiple Claude Code credential sets."""

    def __init__(self):
        HOTBUNK_DIR.mkdir(exist_ok=True)
        ACCOUNTS_DIR.mkdir(exist_ok=True)

    def list_accounts(self) -> list[AccountInfo]:
        """List all registered accounts."""
        accounts = []
        for account_dir in sorted(ACCOUNTS_DIR.iterdir()):
            if not account_dir.is_dir():
                continue
            info = self._load_account_info(account_dir)
            if info:
                accounts.append(info)
        return accounts

    def register_current(self, name: str, email: str) -> AccountInfo:
        """Register the currently logged-in Claude account under a name.

        Copies the current ~/.claude/.credentials.json into the hotbunk
        account store. The original file is not modified.
        """
        if not CLAUDE_CREDS.exists():
            raise FileNotFoundError(
                "No Claude credentials found. Run 'claude auth login' first."
            )

        account_dir = ACCOUNTS_DIR / name
        account_dir.mkdir(exist_ok=True)

        # Copy current credentials
        creds_dest = account_dir / ".credentials.json"
        shutil.copy2(CLAUDE_CREDS, creds_dest)
        creds_dest.chmod(0o600)

        # Read credential metadata
        with open(CLAUDE_CREDS) as f:
            creds = json.load(f)
        oauth = creds.get("claudeAiOauth", {})

        # Create default policy
        policy = AccountPolicy(owner=name, email=email)
        policy_path = account_dir / "policy.yaml"
        with open(policy_path, "w") as f:
            f.write(policy.to_yaml())

        return AccountInfo(
            name=name,
            email=email,
            subscription_type=oauth.get("subscriptionType", "unknown"),
            rate_limit_tier=oauth.get("rateLimitTier", "unknown"),
            has_credentials=True,
            policy=policy,
        )

    def get_account(self, name: str) -> Optional[AccountInfo]:
        """Get info about a specific account."""
        account_dir = ACCOUNTS_DIR / name
        if not account_dir.exists():
            return None
        return self._load_account_info(account_dir)

    def get_credentials_dir(self, name: str) -> Optional[Path]:
        """Get the CLAUDE_CONFIG_DIR path for an account.

        This is the directory that should be set as CLAUDE_CONFIG_DIR
        when launching a Claude Code session under this account.
        """
        account_dir = ACCOUNTS_DIR / name
        creds_file = account_dir / ".credentials.json"
        if not creds_file.exists():
            return None
        return account_dir

    def activate(self, name: str) -> bool:
        """Activate an account by copying its credentials to ~/.claude/.

        Returns True if successful.
        """
        account_dir = ACCOUNTS_DIR / name
        creds_src = account_dir / ".credentials.json"
        if not creds_src.exists():
            return False

        # Backup current credentials if they exist and differ
        if CLAUDE_CREDS.exists():
            current_account = self._identify_current_account()
            if current_account and current_account != name:
                # Save current credentials back to their account dir
                current_dir = ACCOUNTS_DIR / current_account
                if current_dir.exists():
                    shutil.copy2(CLAUDE_CREDS, current_dir / ".credentials.json")

        # Copy new credentials in
        shutil.copy2(creds_src, CLAUDE_CREDS)
        CLAUDE_CREDS.chmod(0o600)
        return True

    def refresh_credentials(self, name: str) -> bool:
        """Update stored credentials from the current ~/.claude/ state.

        Call this after a successful token refresh to keep the stored
        copy up to date.
        """
        if not CLAUDE_CREDS.exists():
            return False
        account_dir = ACCOUNTS_DIR / name
        if not account_dir.exists():
            return False
        shutil.copy2(CLAUDE_CREDS, account_dir / ".credentials.json")
        return True

    def _identify_current_account(self) -> Optional[str]:
        """Figure out which account is currently active by comparing tokens."""
        if not CLAUDE_CREDS.exists():
            return None
        with open(CLAUDE_CREDS) as f:
            current = json.load(f)
        current_token = current.get("claudeAiOauth", {}).get("accessToken", "")

        for account_dir in ACCOUNTS_DIR.iterdir():
            if not account_dir.is_dir():
                continue
            creds_file = account_dir / ".credentials.json"
            if not creds_file.exists():
                continue
            with open(creds_file) as f:
                stored = json.load(f)
            stored_token = stored.get("claudeAiOauth", {}).get("accessToken", "")
            if current_token and current_token == stored_token:
                return account_dir.name
        return None

    def _load_account_info(self, account_dir: Path) -> Optional[AccountInfo]:
        """Load account info from a directory."""
        creds_file = account_dir / ".credentials.json"
        policy_file = account_dir / "policy.yaml"

        if not creds_file.exists():
            return None

        with open(creds_file) as f:
            creds = json.load(f)
        oauth = creds.get("claudeAiOauth", {})

        policy = None
        if policy_file.exists():
            policy = AccountPolicy.from_yaml(policy_file)

        return AccountInfo(
            name=account_dir.name,
            email=policy.email if policy else "unknown",
            subscription_type=oauth.get("subscriptionType", "unknown"),
            rate_limit_tier=oauth.get("rateLimitTier", "unknown"),
            has_credentials=True,
            policy=policy,
        )
