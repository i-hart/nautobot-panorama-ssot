# Nautobot Panorama SSOT

A Nautobot app that synchronizes firewall objects from Palo Alto Panorama to Nautobot using the SSoT framework version 3.

## Features

- Sync Address Objects from Panorama to Nautobot
- Sync Service Objects from Panorama to Nautobot
- Sync Security Zones from Panorama to Nautobot
- Sync Security Policies and Rules from Panorama to Nautobot
- Leverages Nautobot's External Integrations for secure credential storage
- Built on nautobot-firewall-models for standardized firewall object representation
- Full SSoT v3 integration with diff viewing and dry-run capabilities

## Requirements

- Nautobot >= 2.10.0
- nautobot-ssot >= 3.0.0
- nautobot-firewall-models >= 2.0.0
- Python >= 3.8

## Installation

1. Install the package:

```bash
pip install nautobot-panorama-ssot
```

2. Add to your Nautobot configuration (`nautobot_config.py`):

```python
PLUGINS = [
    "nautobot_firewall_models",
    "nautobot_ssot",
    "nautobot_panorama_ssot",
]
```

3. Run migrations:

```bash
nautobot-server migrate
```

4. Collect static files:

```bash
nautobot-server collectstatic --no-input
```

5. Restart Nautobot services

## Configuration

### Step 1: Create a Secrets Group

1. Navigate to **Extensibility > Secrets Groups**
2. Create a new Secrets Group (e.g., "Panorama Credentials")
3. Add a Secret with:
   - **Name**: API Token
   - **Type**: Token
   - **Provider**: Environment Variable or Text File
   - **Value**: Your Panorama API token

### Step 2: Create an External Integration

1. Navigate to **Extensibility > External Integrations**
2. Create a new External Integration:
   - **Name**: "Production Panorama" (or similar)
   - **Remote URL**: `https://your-panorama-host`
   - **Verify SSL**: Check if using valid certificates
   - **Secrets Group**: Select the Secrets Group created above
   - **Extra Config**: Leave empty or add custom configuration

### Step 3: Create a Panorama Connection

1. Navigate to **Plugins > Panorama SSOT > Connections**
2. Click **Add**
3. Fill in the form:
   - **External Integration**: Select the External Integration created above
   - **Device Group**: Enter the Panorama device group to sync (e.g., "shared")
   - **Template**: Enter the Panorama template name (e.g., "default")
   - **Verify SSL**: Match the External Integration setting

### Step 4: Run the Sync Job

1. Navigate to **Jobs > Jobs**
2. Find "Panorama to Nautobot" job
3. Click **Run**
4. Select your Panorama Connection
5. Choose whether to run in **Dry Run** mode (recommended for first run)
6. Click **Run Job**

## Usage

### Viewing Sync Results

After running the sync job, you can view:

- **Job Results**: In the Jobs interface, see detailed logs and statistics
- **Sync Logs**: Navigate to **Plugins > Panorama SSOT > Sync Logs** to see historical sync runs
- **Objects**: View synced objects in their respective apps:
  - Address Objects: **Firewall > Address Objects**
  - Service Objects: **Firewall > Service Objects**
  - Security Zones: **Firewall > Zones**
  - Security Policies: **Firewall > Security Policies**

### API Access

The app provides REST API endpoints:

```bash
# List Panorama connections
GET /api/plugins/panorama-ssot/connections/

# Get specific connection
GET /api/plugins/panorama-ssot/connections/{id}/

# List sync logs
GET /api/plugins/panorama-ssot/sync-logs/

# Get specific sync log
GET /api/plugins/panorama-ssot/sync-logs/{id}/
```

## Architecture

### Models

- **PanoramaConnection**: Stores connection details using External Integration
- **PanoramaSyncLog**: Tracks sync job execution and results

### Adapters

- **PanoramaAdapter**: Source adapter that loads data from Panorama API
- **NautobotAdapter**: Target adapter (built-in to SSOT) that receives data

### Data Flow

1. Job starts and creates PanoramaAdapter with connection details
2. PanoramaAdapter loads data from Panorama API
3. Data is transformed into nautobot-firewall-models objects
4. SSOT framework diffs source and target data
5. Changes are applied to Nautobot (or shown in dry-run)
6. Sync log is updated with results

## Generating API Token in Panorama

To generate an API token in Panorama:

1. SSH into your Panorama instance
2. Run: `curl -k -X GET 'https://localhost/api/?type=keygen&user=USERNAME&password=PASSWORD'`
3. Extract the `<key>` value from the XML response
4. Use this key as your API token in the Secrets Group

Alternatively, use the Panorama web UI to generate an API key under **Device > Setup > Management > API Key**

## Troubleshooting

### "API token not found in External Integration secrets group"

- Verify the Secrets Group is attached to the External Integration
- Ensure the Secret type is "token"
- Check the Secret has a valid value

### "Connection refused" or SSL errors

- Verify the Remote URL in External Integration is correct
- Check network connectivity from Nautobot to Panorama
- If using self-signed certificates, set **Verify SSL** to False

### No objects synced

- Verify the Device Group and Template names are correct
- Check Panorama has objects in the specified Device Group
- Review job logs for API errors

## Development

### Project Structure

```
nautobot_panorama_ssot/
├── __init__.py           # App configuration
├── models.py             # Django models
├── adapters.py           # SSOT adapters
├── jobs.py               # SSOT jobs
├── views.py              # UI views
├── admin.py              # Django admin
├── forms.py              # Django forms
├── filters.py            # Django filters
├── tables.py             # Django tables
├── urls.py               # URL routing
├── api/
│   ├── views.py          # API views
│   ├── serializers.py    # API serializers
│   └── urls.py           # API URLs
└── migrations/           # Database migrations
```

### Running Tests

```bash
poetry install
poetry run pytest
```

### Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Write tests
5. Submit a pull request

## License

Apache License 2.0

## Support

For issues and questions:
- GitHub Issues: https://github.com/yourusername/nautobot-panorama-ssot/issues
- Nautobot Slack: #nautobot channel
