# HOD Forwarding and Timeline Fix

## Fixed issues
1. Faculty **Verify & Send to HOD** now uses the student's stored `hod_email` mapping and falls back to the active HOD for the student's department.
2. The request approval timeline now reads the aliased database fields correctly (`Action`, `Role`, `Time`, `Remarks`) instead of looking for a non-existent lowercase `action` key.

## Testing
- Security/static test suite: **18/18 passed**.
- Python syntax check: passed.
- Streamlit runtime was not executed in this build environment because Streamlit is not installed here; please run it locally using the included requirements file.

## Important
Use this package in a **new extracted folder** so an old `portal.db` or old `app.py` is not accidentally reused.
