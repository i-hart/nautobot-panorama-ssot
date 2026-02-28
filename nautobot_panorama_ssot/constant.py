"""Constants for use with the Panorama SSoT app."""

# ==========================================================
# VISUAL / TAGGING
# ==========================================================

TAG_COLOR = "FA582D"

# ==========================================================
# PANORAMA DEFAULTS
# ==========================================================

DEFAULT_DEVICE_GROUP = "shared"
DEFAULT_TEMPLATE = "BASE"
DEFAULT_REQUEST_TIMEOUT = 60
DEFAULT_STATUS_NAME = "Active"

PANORAMA_API_VERSION = "v11.1"
PANORAMA_API_PATH = "/api/"

# ==========================================================
# ENV VARS
# ==========================================================

ENV_VAR_USERNAME = "NAUTOBOT_PANORAMA_SSOT_USERNAME"
ENV_VAR_TOKEN = "NAUTOBOT_PANORAMA_SSOT_TOKEN"
ENV_VAR_URL = "NAUTOBOT_PANORAMA_SSOT_URL"

# ==========================================================
# RUNTIME DEFAULTS (SAFE)
# ==========================================================

DEFAULT_CHANGE_WINDOW_ONLY = False
DEFAULT_ALLOWED_HOURS = (0, 23)

DEFAULT_DRIFT_ONLY = False
DEFAULT_ALLOW_DELETE = False
DEFAULT_SIMULATION_MODE = False
DEFAULT_AUTO_REORDER = False

DEFAULT_SAFE_COMMIT_MODE = "advisory"
DEFAULT_SAFE_COMMIT_THRESHOLD = 70
