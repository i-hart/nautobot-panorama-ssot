#!/usr/bin/env python
"""Test Panorama authentication and API key.

Run with: nautobot-server shell < test_panorama_auth.py
"""

import requests
import xml.etree.ElementTree as ET

print("=" * 80)
print("PANORAMA AUTHENTICATION TEST")
print("=" * 80)

# Get config
from nautobot_panorama_ssot.models import SSOTPanoramaConfig
from nautobot.extras.choices import SecretsGroupAccessTypeChoices, SecretsGroupSecretTypeChoices

configs = SSOTPanoramaConfig.objects.all()
if not configs.exists():
    print("\n✗ No SSOTPanoramaConfig found!")
    print("Create one first.")
    exit(1)

config = configs.get(name='PRA TO NB TEST1')
print(f"\nUsing config: {config.name}")
print(f"Panorama URL: {config.panorama_instance.remote_url}")

# Get secrets
print("\n" + "=" * 80)
print("CHECKING SECRETS")
print("=" * 80)

if not config.panorama_instance.secrets_group:
    print("\n✗ No secrets group assigned to external integration!")
    exit(1)

print(f"Secrets Group: {config.panorama_instance.secrets_group.name}")

# Get username
try:
    username = config.panorama_instance.secrets_group.get_secret_value(
        access_type=SecretsGroupAccessTypeChoices.TYPE_HTTP,
        secret_type=SecretsGroupSecretTypeChoices.TYPE_USERNAME,
    )
    print(f"✓ Username found: {username[:3]}***")
except Exception as e:
    print(f"✗ Username not found: {e}")
    username = None

# Get token/password
try:
    token = config.panorama_instance.secrets_group.get_secret_value(
        access_type=SecretsGroupAccessTypeChoices.TYPE_HTTP,
        secret_type=SecretsGroupSecretTypeChoices.TYPE_TOKEN,
    )
    print(f"✓ Token found: {token[:5]}*** (length: {len(token)})")
    
    # Determine if this looks like an API key or password
    if len(token) > 30:
        print("  → Looks like a pre-generated API key (good!)")
        api_key = token
        is_api_key = True
    else:
        print("  → Looks like a password (will attempt to generate API key)")
        password = token
        is_api_key = False
except Exception as e:
    print(f"✗ Token not found: {e}")
    token = None
    exit(1)

# Test connection
print("\n" + "=" * 80)
print("TESTING CONNECTION")
print("=" * 80)

panorama_url = config.panorama_instance.remote_url
verify_ssl = config.panorama_instance.verify_ssl
timeout = config.panorama_instance.timeout

print(f"URL: {panorama_url}")
print(f"Verify SSL: {verify_ssl}")
print(f"Timeout: {timeout}")

session = requests.Session()
session.verify = verify_ssl

# Test 1: If we have an API key, test it directly
if is_api_key:
    print("\n[Test 1] Testing pre-generated API key...")
    try:
        params = {
            "type": "op",
            "cmd": "<show><system><info></info></system></show>",
            "key": api_key,
        }
        
        response = session.get(
            f"{panorama_url}/api/",
            params=params,
            timeout=timeout,
        )
        
        print(f"  Response status: {response.status_code}")
        
        if response.status_code == 200:
            root = ET.fromstring(response.text)
            status = root.attrib.get("status")
            print(f"  API response status: {status}")
            
            if status == "success":
                print("  ✓ API key is valid!")
                
                # Try to get system info
                hostname = root.find(".//hostname")
                if hostname is not None:
                    print(f"  Connected to: {hostname.text}")
            else:
                msg = root.find(".//msg")
                error = msg.text if msg is not None else "Unknown error"
                print(f"  ✗ API key invalid: {error}")
        else:
            print(f"  ✗ HTTP error: {response.status_code}")
            print(f"  Response: {response.text[:200]}")
            
    except Exception as e:
        print(f"  ✗ Connection failed: {e}")

# Test 2: If we have username/password, try to generate API key
else:
    print("\n[Test 2] Attempting to generate API key from credentials...")
    
    if not username:
        print("  ✗ Username is required to generate API key")
    else:
        try:
            params = {
                "type": "keygen",
                "user": username,
                "password": password,
            }
            
            print(f"  Requesting API key for user: {username}")
            
            response = session.get(
                f"{panorama_url}/api/",
                params=params,
                timeout=timeout,
            )
            
            print(f"  Response status: {response.status_code}")
            
            if response.status_code == 200:
                root = ET.fromstring(response.text)
                status = root.attrib.get("status")
                print(f"  API response status: {status}")
                
                if status == "success":
                    key_element = root.find(".//key")
                    if key_element is not None and key_element.text:
                        generated_key = key_element.text.strip()
                        print(f"  ✓ API key generated successfully!")
                        print(f"  Key: {generated_key[:10]}...{generated_key[-5:]}")
                        print(f"  Length: {len(generated_key)}")
                        
                        print("\n  → You can use this API key directly in your secrets!")
                        print("    Update your Token secret to use this generated key instead.")
                    else:
                        print("  ✗ No key in response")
                        print(f"  Response: {response.text[:500]}")
                else:
                    msg = root.find(".//msg")
                    error = msg.text if msg is not None else "Unknown error"
                    print(f"  ✗ Key generation failed: {error}")
            else:
                print(f"  ✗ HTTP error: {response.status_code}")
                print(f"  Response: {response.text[:200]}")
                
        except Exception as e:
            print(f"  ✗ Key generation failed: {e}")
            import traceback
            traceback.print_exc()

# Summary
print("\n" + "=" * 80)
print("SUMMARY & RECOMMENDATIONS")
print("=" * 80)

if is_api_key:
    print("\n✓ You have a pre-generated API key configured")
    print("  The adapter will use this key directly.")
    print("\nIf the job still fails, check:")
    print("  1. The API key is still valid in Panorama")
    print("  2. The Panorama URL is correct")
    print("  3. SSL certificate verification settings")
    print("  4. Network connectivity from Nautobot to Panorama")
else:
    print("\n⚠ You have username/password configured")
    print("  The adapter will try to generate an API key at runtime.")
    print("\nRECOMMENDATION:")
    print("  1. Generate an API key manually in Panorama")
    print("  2. Update your Token secret to use the API key directly")
    print("  3. This is more efficient and secure")
    print("\nTo generate API key manually:")
    print("  Panorama Web UI: Device > Setup > Management > API Key")
    print("  Or use the test above to generate one")

print("\n" + "=" * 80)
