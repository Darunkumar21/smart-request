# Panimalar Smart Campus Portal - HOD FIX

1. Extract this ZIP into a new folder.
2. Open PowerShell in the folder containing `app.py` and `requirements.txt`.
3. Run:
   `python -m pip install -r requirements.txt`
4. Run:
   `python -m streamlit run app.py`
5. Open the URL Streamlit displays (normally http://localhost:8501).

Demo accounts:
- Student: arun@demo.college.edu / student123
- Faculty: faculty@demo.college.edu / faculty123
- HOD: hod@demo.college.edu / hod123
- Admin: admin@demo.college.edu / admin123

Test flow:
Student creates request -> Faculty Verification Queue -> Verify & Send to HOD -> HOD Approval Queue.

Do not use real college credentials in the demo.
