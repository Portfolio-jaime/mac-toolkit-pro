from pathlib import Path

HOME = Path.home()

# Analyzer targets
REPO_ROOTS = [HOME / "arqueanja", HOME / "arheanja"]

BROWSER_CACHE_PATHS = {
    "Chrome":  HOME / "Library/Caches/Google/Chrome",
    "Safari":  HOME / "Library/Caches/com.apple.Safari",
    "Firefox": HOME / "Library/Caches/Firefox",
    "Edge":    HOME / "Library/Caches/Microsoft Edge",
}

LOG_DIRS = [
    HOME / "Library/Logs",
    Path("/Library/Logs"),
    Path("/var/log"),
]

DOWNLOAD_DIRS = [
    HOME / "Downloads",
    HOME / "Desktop",
]

APP_SUPPORT_DIR = HOME / "Library/Application Support"
CACHES_DIR = HOME / "Library/Caches"
OLLAMA_MODELS_DIR = HOME / ".ollama/models"

# Safety blacklist — these paths are NEVER touched by cleaners
BLACKLISTED_PATHS = {
    "com.apple.dock",
    "com.apple.finder",
    "com.apple.spotlight",
}
BLACKLISTED_PREFIXES = [
    Path("/System"),
    Path("/usr"),
    Path("/bin"),
    Path("/sbin"),
    Path("/private/var/db"),
]

# Thresholds
ANALYZER_TIMEOUT_SECONDS = 120
DEFAULT_MIN_SIZE_MB = 50
SEVERITY_CRITICAL_GB = 10
SEVERITY_HIGH_GB = 1
SEVERITY_MEDIUM_MB = 100

# Reports
REPORTS_DIR = Path(__file__).parent.parent.parent / "reports"
