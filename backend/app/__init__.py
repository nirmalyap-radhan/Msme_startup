"""
Udyog Sathi Backend App Package.
"""
import sys

# Ensure both `app` and `apps.api` import paths resolve to this module
_app_module = sys.modules.get(__name__)
if _app_module:
    sys.modules.setdefault("app", _app_module)
    sys.modules.setdefault("apps.api", _app_module)
