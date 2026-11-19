"""Environment pinned before Django settings are imported."""

import os

# Keep the test process off Ray and S3. An explicit environment value wins
# only when it is set before this file is imported; load_dotenv() does not
# override variables that are already present.
os.environ["USE_RAY"] = "false"
os.environ.setdefault("STORAGES_MODE", "local")
# Playwright starts an event loop before Django creates the test database.
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "back.config.settings")
