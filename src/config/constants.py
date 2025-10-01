"""Constants for video generation configuration."""

# Timeout Configuration (seconds)
TIMEOUT_CONNECT = 60.0  # Connection establishment timeout
TIMEOUT_READ = 600.0    # Read timeout (10 minutes for long video generation)
TIMEOUT_WRITE = 60.0    # Write timeout for uploading data
TIMEOUT_POOL = 30.0     # Connection pool timeout

# Progress Calculation
PROGRESS_SCALE_FACTOR = 0.1  # Scale factor for progress percentage calculation

# Status Progress Mapping
STATUS_PROGRESS_MAP = {
    'starting': 10.0,
    'processing': 50.0,
    'succeeded': 100.0
}

# Polling Configuration
DEFAULT_POLL_INTERVAL = 3  # Seconds between status checks
MAX_WAIT_TIME = 1200      # Maximum wait time for video generation (20 minutes)

# Retry Configuration
MAX_RETRIES = 3           # Maximum retry attempts for API calls
RATE_LIMIT_RETRY_DELAY = 60  # Delay when rate limited (seconds)