#!/usr/bin/env python3
# Admin CLI for API Key Management
"""
Internal tool to create and manage API keys.

Usage:
    python -m admin.api_keys create <customer_id> [--name "key name"] [--test]
    python -m admin.api_keys list <customer_id>
    python -m admin.api_keys revoke <api_key>

Examples:
    # Create production key for customer
    python -m admin.api_keys create acme_corp --name "Production Key"
    
    # Create test key
    python -m admin.api_keys create acme_corp --name "Test Key" --test
    
    # List all keys for customer
    python -m admin.api_keys list acme_corp
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from api.auth import (
    create_api_key,
    list_customer_keys,
    revoke_api_key,
    validate_api_key
)
from core.customer import CustomerManager
from config import WORKSPACE_DIR


def cmd_create(args):
    """Create a new API key for a customer."""
    customer_id = args.customer_id
    name = args.name or "default"
    is_test = args.test
    
    # Ensure customer exists
    manager = CustomerManager()
    
    try:
        if manager.customer_exists(customer_id):
            ctx = manager.get_customer(customer_id)
        else:
            ctx = manager.create_customer(customer_id)
        ctx.ensure_exists()
        print(f"\n📁 Customer workspace: {ctx.root_dir}")
    except ValueError as e:
        print(f"\n❌ Error: {e}")
        return 1
    
    # Create key
    api_key = create_api_key(customer_id, name, is_test)
    
    key_type = "TEST" if is_test else "LIVE"
    
    print(f"\n{'='*60}")
    print(f"✅ {key_type} API Key Created!")
    print(f"{'='*60}")
    print(f"\n🔑 API Key (SAVE THIS - shown only once!):\n")
    print(f"   {api_key}")
    print(f"\n📋 Details:")
    print(f"   Customer ID: {customer_id}")
    print(f"   Key Name: {name}")
    print(f"   Type: {key_type}")
    print(f"   Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"\n⚠️  IMPORTANT: Store this key securely. It cannot be retrieved later.")
    print(f"{'='*60}\n")
    
    return 0


def cmd_list(args):
    """List all API keys for a customer."""
    customer_id = args.customer_id
    
    keys = list_customer_keys(customer_id)
    
    if not keys:
        print(f"\n📭 No API keys found for customer: {customer_id}")
        return 0
    
    print(f"\n🔑 API Keys for {customer_id}:")
    print(f"{'='*70}")
    
    for i, key in enumerate(keys, 1):
        status = "✅ Active" if key["is_active"] else "❌ Revoked"
        key_type = "TEST" if key.get("is_test") else "LIVE"
        last_used = key.get("last_used", "Never")
        
        print(f"\n  {i}. {key['key_prefix']}")
        print(f"     Name: {key['name']}")
        print(f"     Type: {key_type}")
        print(f"     Status: {status}")
        print(f"     Created: {key.get('created_at', 'Unknown')}")
        print(f"     Last Used: {last_used}")
    
    print(f"\n{'='*70}\n")
    return 0


def cmd_revoke(args):
    """Revoke an API key."""
    api_key = args.api_key
    
    # Validate key first
    key_info = validate_api_key(api_key)
    
    if not key_info:
        print(f"\n❌ Invalid or already revoked API key")
        return 1
    
    # Confirm
    customer_id = key_info["customer_id"]
    print(f"\n⚠️  WARNING: About to revoke API key for customer: {customer_id}")
    print(f"   Key prefix: {api_key[:12]}...")
    
    confirm = input("\n   Type 'REVOKE' to confirm: ")
    if confirm != "REVOKE":
        print("\n❌ Cancelled")
        return 1
    
    # Revoke
    success = revoke_api_key(api_key)
    
    if success:
        print(f"\n✅ API key revoked successfully")
    else:
        print(f"\n❌ Failed to revoke key")
        return 1
    
    return 0


def cmd_test(args):
    """Test an API key."""
    api_key = args.api_key
    
    key_info = validate_api_key(api_key)
    
    if key_info:
        print(f"\n✅ Valid API key")
        print(f"   Customer: {key_info['customer_id']}")
        print(f"   Name: {key_info['name']}")
        print(f"   Active: {key_info['is_active']}")
    else:
        print(f"\n❌ Invalid or revoked API key")
        return 1
    
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="LedgerMind API Key Management",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Create key:  python -m admin.api_keys create acme_corp --name "Prod"
  List keys:   python -m admin.api_keys list acme_corp
  Test key:    python -m admin.api_keys test lm_live_sk_xxxxx
  Revoke key:  python -m admin.api_keys revoke lm_live_sk_xxxxx
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Create command
    create_parser = subparsers.add_parser("create", help="Create new API key")
    create_parser.add_argument("customer_id", help="Customer ID")
    create_parser.add_argument("--name", "-n", default="default", help="Key name")
    create_parser.add_argument("--test", "-t", action="store_true", help="Create test key")
    create_parser.set_defaults(func=cmd_create)
    
    # List command
    list_parser = subparsers.add_parser("list", help="List customer API keys")
    list_parser.add_argument("customer_id", help="Customer ID")
    list_parser.set_defaults(func=cmd_list)
    
    # Revoke command
    revoke_parser = subparsers.add_parser("revoke", help="Revoke an API key")
    revoke_parser.add_argument("api_key", help="Full API key to revoke")
    revoke_parser.set_defaults(func=cmd_revoke)
    
    # Test command
    test_parser = subparsers.add_parser("test", help="Test an API key")
    test_parser.add_argument("api_key", help="Full API key to test")
    test_parser.set_defaults(func=cmd_test)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())

