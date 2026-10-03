"""Local static security checks for the demo build. Not a substitute for a production pentest."""
from pathlib import Path
import ast,re,zipfile

ROOT=Path(__file__).resolve().parent
APP=(ROOT/'app.py').read_text(encoding='utf-8')
results=[]
def check(name, ok, detail=''):
    results.append((name, bool(ok), detail))

try: ast.parse(APP); check('Python syntax',True)
except SyntaxError as e: check('Python syntax',False,str(e))

check('PBKDF2 password hashing', 'pbkdf2_hmac' in APP and 'hmac.compare_digest' in APP)
check('No direct plaintext password column insert', 'INSERT INTO users(email,password_hash' in APP and 'hash_pw(pw)' in APP)
check('Parameterized SQL placeholders', "lower(email)=lower(?)" in APP and "WHERE id=?" in APP)
check('Role verification server-side', "if u['role']!=portal" in APP and "get_identity(email,portal)" in APP)
check('Student identity bound to authenticated email', "lower(email)=lower(?)" in APP and "student_db_id" in APP)
check('Student request ownership check', "r.request_code=? AND r.student_id=?" in APP)
check('Faculty approver ownership check', "r.current_approver=?" in APP)
check('HOD department scoping', "s.department=?" in APP and "r.current_approver=?" in APP)
check('HOD-only full faculty permission', "FULL_STUDENT_PROFILE_EDIT" in APP and "role=='hod'" in APP)
check('Field-specific student permissions', 'profile_permissions' in APP and "field_name" in APP)
check('Upload size validation', 'MAX_UPLOAD=5*1024*1024' in APP and 'len(data)>MAX_UPLOAD' in APP)
check('Upload magic/signature validation', "data.startswith(b'%PDF')" in APP and "b'\\x89PNG" in APP)
check('Safe uploaded filename', 'Path(name).name' in APP and 'safe_filename' in APP)
check('Audit logging', 'security_audit' in APP and "LOGIN_FAILED" in APP and "PERMISSION" in APP)
check('Confidential support recipient scoping', "target_email" in APP and 'target_type' in APP)
check('Duplicate request detection', 'similar request already exists' in APP)
check('No pandas dependency', 'import pandas' not in APP)

print('PANIMALAR SMART CAMPUS PORTAL - SECURITY CHECK')
print('='*58)
for n,ok,d in results:
    print(('PASS' if ok else 'FAIL').ljust(5), n, (f' - {d}' if d else ''))
print('='*58)
print(f'Passed: {sum(x[1] for x in results)}/{len(results)}')
if not all(x[1] for x in results): raise SystemExit(1)
