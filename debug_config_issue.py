#!/usr/bin/env python
"""Debug why SSOTPanoramaConfig doesn't show in job dropdown.

Run with: nautobot-server shell < debug_config_issue.py
"""

print("=" * 80)
print("DEBUGGING CONFIG DROPDOWN ISSUE")
print("=" * 80)

# Check 1: Import models
print("\n[1/6] Checking imports...")
try:
    from nautobot_panorama_ssot.models import SSOTPanoramaConfig
    from nautobot.extras.models import ExternalIntegration
    print("  ✓ Models imported successfully")
except Exception as e:
    print(f"  ✗ Import failed: {e}")
    exit(1)

# Check 2: Count SSOTPanoramaConfig objects
print("\n[2/6] Checking SSOTPanoramaConfig objects...")
try:
    configs = SSOTPanoramaConfig.objects.all()
    count = configs.count()
    print(f"  Total configs: {count}")
    
    if count == 0:
        print("  ⚠ No configs found! Create one first.")
    else:
        for idx, config in enumerate(configs, 1):
            print(f"\n  Config {idx}:")
            print(f"    ID: {config.pk}")
            print(f"    Name: {config.name}")
            print(f"    Panorama Instance: {config.panorama_instance}")
            print(f"    Device Group: {config.device_group}")
            print(f"    Template: {config.template}")
            
            # Check if it has the filter fields
            if hasattr(config, 'enable_sync_to_nautobot'):
                print(f"    enable_sync_to_nautobot: {config.enable_sync_to_nautobot}")
            else:
                print(f"    ⚠ Missing field: enable_sync_to_nautobot")
            
            if hasattr(config, 'job_enabled'):
                print(f"    job_enabled: {config.job_enabled}")
            else:
                print(f"    ⚠ Missing field: job_enabled")
                
except Exception as e:
    print(f"  ✗ Query failed: {e}")
    import traceback
    traceback.print_exc()

# Check 3: Check ExternalIntegration objects
print("\n[3/6] Checking ExternalIntegration objects...")
try:
    ei_list = ExternalIntegration.objects.all()
    ei_count = ei_list.count()
    print(f"  Total external integrations: {ei_count}")
    
    if ei_count == 0:
        print("  ⚠ No external integrations found!")
    else:
        print("\n  Available External Integrations:")
        for idx, ei in enumerate(ei_list, 1):
            print(f"    {idx}. {ei.name}")
            print(f"       URL: {ei.remote_url}")
            print(f"       Has SecretsGroup: {bool(ei.secrets_group)}")
            
            # Check if linked to a config
            try:
                linked_configs = SSOTPanoramaConfig.objects.filter(panorama_instance=ei)
                if linked_configs.exists():
                    print(f"       Linked to configs: {', '.join([c.name for c in linked_configs])}")
                else:
                    print(f"       ⚠ Not linked to any config")
            except Exception as e:
                print(f"       Error checking configs: {e}")
                
except Exception as e:
    print(f"  ✗ Query failed: {e}")

# Check 4: Test the job's ObjectVar
print("\n[4/6] Testing job's ObjectVar configuration...")
try:
    from nautobot_panorama_ssot.jobs import PanoramaDataSource
    from nautobot.apps.jobs import ObjectVar
    
    job_class = PanoramaDataSource
    
    if hasattr(job_class, 'config'):
        config_field = job_class.config
        print(f"  ✓ config field exists")
        print(f"    Type: {type(config_field).__name__}")
        print(f"    Model: {config_field.model.__name__}")
        print(f"    Required: {config_field.required}")
        
        # Check if query_params exist
        if hasattr(config_field, 'query_params'):
            print(f"    query_params: {config_field.query_params}")
            
            # Test if the query params would filter anything
            if config_field.query_params:
                try:
                    filtered_qs = config_field.model.objects.filter(**config_field.query_params)
                    print(f"    Filtered queryset count: {filtered_qs.count()}")
                    
                    if filtered_qs.count() == 0:
                        print(f"    ⚠ ISSUE: query_params filter returns 0 results!")
                        print(f"       This is why dropdown is empty!")
                        
                        # Try without filters
                        all_qs = config_field.model.objects.all()
                        print(f"    Without filters would show: {all_qs.count()} configs")
                except Exception as e:
                    print(f"    ✗ Error testing query_params: {e}")
                    print(f"       Likely the fields in query_params don't exist!")
        else:
            print(f"    No query_params (good - will show all)")
            
        # Test the actual queryset
        try:
            test_qs = config_field.model.objects.all()
            print(f"    Model queryset count: {test_qs.count()}")
        except Exception as e:
            print(f"    ✗ Error querying model: {e}")
    else:
        print("  ✗ config field not found on job!")
        
except Exception as e:
    print(f"  ✗ Test failed: {e}")
    import traceback
    traceback.print_exc()

# Check 5: Verify model fields
print("\n[5/6] Checking SSOTPanoramaConfig model fields...")
try:
    from nautobot_panorama_ssot.models import SSOTPanoramaConfig
    
    # Get all field names
    field_names = [f.name for f in SSOTPanoramaConfig._meta.get_fields()]
    print(f"  Available fields: {', '.join(field_names)}")
    
    # Check for the filter fields
    required_fields = ['enable_sync_to_nautobot', 'job_enabled']
    missing_fields = [f for f in required_fields if f not in field_names]
    
    if missing_fields:
        print(f"\n  ⚠ Missing fields: {', '.join(missing_fields)}")
        print(f"     These fields are referenced in query_params but don't exist!")
        print(f"     Solution: Remove query_params from ObjectVar or add fields to model")
    else:
        print(f"  ✓ All required fields exist")
        
except Exception as e:
    print(f"  ✗ Check failed: {e}")

# Check 6: Test creating a config (if none exist and EI exists)
print("\n[6/6] Quick fix suggestions...")

configs_exist = SSOTPanoramaConfig.objects.exists()
ei_exists = ExternalIntegration.objects.exists()

if not configs_exist and ei_exists:
    print("\n  ISSUE: No SSOTPanoramaConfig objects exist")
    print("  SOLUTION: Create one manually:")
    print("\n  nautobot-server shell")
    print("  >>> from nautobot_panorama_ssot.models import SSOTPanoramaConfig")
    print("  >>> from nautobot.extras.models import ExternalIntegration")
    print("  >>> ei = ExternalIntegration.objects.first()")
    print("  >>> config = SSOTPanoramaConfig.objects.create(")
    print("  ...     name='Test Config',")
    print("  ...     description='Test',")
    print("  ...     panorama_instance=ei,")
    print("  ...     device_group='shared',")
    print("  ...     template='default'")
    print("  ... )")
    
elif configs_exist and not ei_exists:
    print("\n  ISSUE: No ExternalIntegration objects exist")
    print("  SOLUTION: Create one in UI or via shell")
    
elif not configs_exist and not ei_exists:
    print("\n  ISSUE: Neither configs nor external integrations exist")
    print("  SOLUTION: Create ExternalIntegration first, then SSOTPanoramaConfig")
    
else:
    # Both exist but dropdown is empty
    print("\n  Checking job configuration...")
    try:
        from nautobot_panorama_ssot.jobs import PanoramaDataSource
        
        if hasattr(PanoramaDataSource, 'config'):
            if hasattr(PanoramaDataSource.config, 'query_params') and PanoramaDataSource.config.query_params:
                print("\n  ISSUE: Job has query_params that filter out all configs")
                print(f"  Current query_params: {PanoramaDataSource.config.query_params}")
                print("\n  SOLUTION 1: Remove query_params from jobs.py:")
                print("    config = ObjectVar(")
                print("        model=SSOTPanoramaConfig,")
                print("        description='Select config',")
                print("        required=True,")
                print("        # Remove query_params line")
                print("    )")
                print("\n  SOLUTION 2: Add missing fields to model and run migrations:")
                print("    - enable_sync_to_nautobot")
                print("    - job_enabled")
                print("    Then set them to True on existing configs")
            else:
                print("  ✓ Configuration looks good!")
                print("  Configs should appear in dropdown after restarting services")
                
    except Exception as e:
        print(f"  Could not check job config: {e}")

print("\n" + "=" * 80)
print("DIAGNOSTIC COMPLETE")
print("=" * 80)
print("\nIf dropdown is still empty after fixing above issues:")
print("1. Run migrations: nautobot-server migrate")
print("2. Restart services: sudo systemctl restart nautobot nautobot-worker")
print("3. Clear cache: nautobot-server shell -c 'from django.core.cache import cache; cache.clear()'")
print("=" * 80)
