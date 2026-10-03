import streamlit as st
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
import hashlib, hmac, secrets, csv, io, html, re, time

BASE=Path(__file__).resolve().parent
DB=BASE/'portal.db'
UPLOADS=BASE/'uploads'
UPLOADS.mkdir(exist_ok=True)
MAX_UPLOAD=5*1024*1024
ALLOWED_EXT={'.pdf','.png','.jpg','.jpeg'}

st.set_page_config(page_title='Panimalar Smart Campus Portal', page_icon='🎓', layout='wide', initial_sidebar_state='expanded')

# ---------------- Styling ----------------
st.markdown('''
<style>
:root{--navy:#063b7a;--blue:#0b73d1;--cyan:#14b8d4;--gold:#f4b400;--ink:#172033;--muted:#607086;--bg:#f4f8ff;--card:#ffffff;--ok:#168a58;--danger:#d64545;}
.stApp{background:linear-gradient(135deg,#f4f8ff 0%,#eef9ff 52%,#fff9ea 100%);color:var(--ink)}
[data-testid="stHeader"]{background:transparent}
.block-container{max-width:1250px;padding-top:1rem;padding-bottom:3rem}
.login-shell{max-width:980px;margin:1.2rem auto}
.brand-card{background:linear-gradient(135deg,#062d66,#0b66bd);color:#fff;border-radius:26px;padding:34px 28px;text-align:center;box-shadow:0 16px 42px rgba(6,45,102,.22)}
.college-logo-img{width:150px;height:150px;object-fit:contain;border-radius:18px;background:#fff;padding:8px;margin:0 auto 16px;display:block}.brand-logo{width:92px;height:92px;border-radius:50%;margin:0 auto 14px;display:flex;align-items:center;justify-content:center;background:rgba(255,255,255,.14);border:2px solid rgba(255,255,255,.35);font-size:44px}
.brand-card h1{font-size:32px;margin:0;font-weight:850}.brand-card p{margin:.45rem 0 0;opacity:.94;font-size:15px}.brand-badge{display:inline-block;margin-top:14px;background:#f4b400;color:#12233e;border-radius:999px;padding:7px 13px;font-weight:800;font-size:12px}
.login-card{background:#fff;border:1px solid #e1e9f4;border-radius:22px;padding:26px;box-shadow:0 10px 30px rgba(19,49,90,.10);margin-top:18px}
.login-choice button{min-height:54px!important}
.info-box{background:#eaf5ff;border:1px solid #cbe5fb;color:#173b62;border-radius:14px;padding:13px 15px;margin:12px 0}
.feature-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin-top:20px}.feature{background:#fff;border:1px solid #e5ebf3;border-radius:17px;padding:18px;box-shadow:0 7px 20px rgba(19,49,90,.07)}.feature h4{margin:0 0 7px;color:#073d7c}.feature p{margin:0;color:#617087;font-size:13px;line-height:1.5}
header[data-testid="stHeader"] + div{color:var(--ink)}
section[data-testid="stSidebar"]{background:linear-gradient(180deg,#052f68,#0868bd);border-right:1px solid rgba(255,255,255,.15)}
section[data-testid="stSidebar"] *{color:#fff!important} section[data-testid="stSidebar"] .stButton>button{background:rgba(255,255,255,.12);border:1px solid rgba(255,255,255,.18);color:#fff!important}
.topbar{background:#fff;border:1px solid #e5ebf3;border-radius:18px;padding:15px 18px;margin-bottom:18px;box-shadow:0 7px 20px rgba(19,49,90,.06)}
.card{background:#fff;border:1px solid #e1e9f4;border-radius:18px;padding:20px;box-shadow:0 7px 20px rgba(19,49,90,.06);margin-bottom:16px}
.small-muted{color:#64748b;font-size:13px}.status{display:inline-block;border-radius:999px;padding:4px 10px;font-size:12px;font-weight:800}.status-ok{background:#dff6ea;color:#12683f}.status-pending{background:#fff2cc;color:#795b00}.status-danger{background:#ffe1e1;color:#8c2222}.status-info{background:#e2f1ff;color:#075a9e}
.profile{display:flex;gap:18px;align-items:center}.avatar{width:88px;height:88px;border-radius:18px;object-fit:cover;border:2px solid #d9e5f3;background:#eef5ff}.avatar-placeholder{width:88px;height:88px;border-radius:18px;background:#dcecff;display:flex;align-items:center;justify-content:center;font-size:34px}
.timeline{border-left:3px solid #cfe2f5;padding-left:16px}.timeline-item{margin:0 0 16px}.timeline-item b{color:#0b5eac}
div[data-testid="stForm"]{border:1px solid #e1e9f4!important;border-radius:16px!important;background:#fff!important;padding:18px!important}
.stButton>button,.stFormSubmitButton>button{border-radius:11px;font-weight:800;min-height:42px}.stTextInput label,.stTextInput label p,.stTextArea label,.stTextArea label p,.stSelectbox label,.stSelectbox label p,.stDateInput label,.stDateInput label p,.stFileUploader label,.stFileUploader label p{color:#172033!important;font-weight:700!important}.stTextInput input,.stTextArea textarea{color:#172033!important;background:#fff!important}.stTextInput input::placeholder,.stTextArea textarea::placeholder{color:#718096!important}.stTextInput input,.stTextArea textarea,.stSelectbox div[data-baseweb="select"]>div{border-radius:10px}
.table-wrap{overflow-x:auto;border:1px solid #e3eaf4;border-radius:12px;background:#fff}.table-wrap table{width:100%;border-collapse:collapse;font-size:13px}.table-wrap th{background:#edf5ff;color:#0b4f91;text-align:left;padding:10px}.table-wrap td{padding:9px;border-top:1px solid #edf0f5;color:#27364a}
.footer{text-align:center;color:#738197;font-size:12px;padding:20px}
@media(max-width:900px){.feature-grid{grid-template-columns:1fr 1fr}.brand-card h1{font-size:25px}.profile{align-items:flex-start}}
@media(max-width:650px){.block-container{padding:.7rem .65rem 2.5rem}.feature-grid{grid-template-columns:1fr}.brand-card{padding:25px 16px}.brand-card h1{font-size:22px}.login-card{padding:16px}.avatar,.avatar-placeholder{width:72px;height:72px}}
</style>
''', unsafe_allow_html=True)

# ---------------- DB ----------------
def conn():
    c=sqlite3.connect(DB, timeout=10, check_same_thread=False)
    c.row_factory=sqlite3.Row
    c.execute('PRAGMA foreign_keys=ON')
    return c

def init_db():
    c=conn(); c.executescript('''
    CREATE TABLE IF NOT EXISTS students(
      id INTEGER PRIMARY KEY AUTOINCREMENT, student_id TEXT UNIQUE NOT NULL,
      reg_no TEXT UNIQUE NOT NULL, name TEXT NOT NULL, email TEXT UNIQUE NOT NULL,
      phone TEXT DEFAULT '', photo_path TEXT DEFAULT '', programme TEXT DEFAULT 'B.Tech',
      department TEXT NOT NULL, year TEXT NOT NULL, semester TEXT DEFAULT '', section TEXT NOT NULL,
      batch TEXT DEFAULT '', class_advisor_email TEXT DEFAULT '', hod_email TEXT DEFAULT '',
      accommodation TEXT NOT NULL DEFAULT 'Day Scholar', active INTEGER NOT NULL DEFAULT 1,
      created_at TEXT NOT NULL, updated_at TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS staff(
      id INTEGER PRIMARY KEY AUTOINCREMENT, staff_id TEXT UNIQUE NOT NULL, name TEXT NOT NULL,
      email TEXT UNIQUE NOT NULL, phone TEXT DEFAULT '', designation TEXT DEFAULT '',
      role TEXT NOT NULL CHECK(role IN ('faculty','hod')), department TEXT NOT NULL,
      active INTEGER NOT NULL DEFAULT 1, created_at TEXT NOT NULL, updated_at TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS users(
      id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT UNIQUE NOT NULL,
      password_hash TEXT NOT NULL, role TEXT NOT NULL CHECK(role IN ('student','faculty','hod','admin')),
      student_db_id INTEGER, staff_db_id INTEGER, active INTEGER NOT NULL DEFAULT 1,
      FOREIGN KEY(student_db_id) REFERENCES students(id), FOREIGN KEY(staff_db_id) REFERENCES staff(id));
    CREATE TABLE IF NOT EXISTS requests(
      id INTEGER PRIMARY KEY AUTOINCREMENT, request_code TEXT UNIQUE NOT NULL,
      student_id INTEGER NOT NULL, request_type TEXT NOT NULL, title TEXT NOT NULL, details TEXT NOT NULL,
      event_date TEXT DEFAULT '', attachment_path TEXT DEFAULT '', status TEXT NOT NULL,
      current_approver TEXT DEFAULT '', created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
      remarks TEXT DEFAULT '', FOREIGN KEY(student_id) REFERENCES students(id));
    CREATE TABLE IF NOT EXISTS approval_history(
      id INTEGER PRIMARY KEY AUTOINCREMENT, request_id INTEGER NOT NULL, actor_email TEXT NOT NULL,
      actor_role TEXT NOT NULL, action TEXT NOT NULL, remarks TEXT DEFAULT '', timestamp TEXT NOT NULL,
      FOREIGN KEY(request_id) REFERENCES requests(id));
    CREATE TABLE IF NOT EXISTS notifications(
      id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT NOT NULL, message TEXT NOT NULL,
      created_at TEXT NOT NULL, is_read INTEGER NOT NULL DEFAULT 0);
    CREATE TABLE IF NOT EXISTS profile_permissions(
      id INTEGER PRIMARY KEY AUTOINCREMENT, target_student_id INTEGER NOT NULL, field_name TEXT NOT NULL,
      granted_by TEXT NOT NULL, granted_at TEXT NOT NULL, expires_at TEXT DEFAULT '', active INTEGER NOT NULL DEFAULT 1,
      UNIQUE(target_student_id,field_name), FOREIGN KEY(target_student_id) REFERENCES students(id));
    CREATE TABLE IF NOT EXISTS staff_permissions(
      id INTEGER PRIMARY KEY AUTOINCREMENT, faculty_id INTEGER NOT NULL, permission TEXT NOT NULL,
      granted_by TEXT NOT NULL, granted_at TEXT NOT NULL, active INTEGER NOT NULL DEFAULT 1,
      UNIQUE(faculty_id,permission), FOREIGN KEY(faculty_id) REFERENCES staff(id));
    CREATE TABLE IF NOT EXISTS support_threads(
      id INTEGER PRIMARY KEY AUTOINCREMENT, thread_code TEXT UNIQUE NOT NULL, student_id INTEGER NOT NULL,
      target_type TEXT NOT NULL CHECK(target_type IN ('faculty','hod')), target_email TEXT NOT NULL,
      category TEXT NOT NULL, subject TEXT NOT NULL, confidentiality TEXT NOT NULL DEFAULT 'confidential',
      status TEXT NOT NULL DEFAULT 'Open', created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
      FOREIGN KEY(student_id) REFERENCES students(id));
    CREATE TABLE IF NOT EXISTS support_messages(
      id INTEGER PRIMARY KEY AUTOINCREMENT, thread_id INTEGER NOT NULL, sender_email TEXT NOT NULL,
      sender_role TEXT NOT NULL, message TEXT NOT NULL, created_at TEXT NOT NULL,
      FOREIGN KEY(thread_id) REFERENCES support_threads(id));
    CREATE TABLE IF NOT EXISTS security_audit(
      id INTEGER PRIMARY KEY AUTOINCREMENT, actor_email TEXT NOT NULL, role TEXT NOT NULL,
      event TEXT NOT NULL, target TEXT DEFAULT '', details TEXT DEFAULT '', timestamp TEXT NOT NULL);
    CREATE INDEX IF NOT EXISTS idx_req_student ON requests(student_id);
    CREATE INDEX IF NOT EXISTS idx_req_status ON requests(status);
    CREATE INDEX IF NOT EXISTS idx_notif_email ON notifications(email,is_read);
    CREATE INDEX IF NOT EXISTS idx_support_target ON support_threads(target_type,target_email);
    ''')
    seed(c); c.commit(); c.close()

def now(): return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
def esc(x): return html.escape(str(x if x is not None else ''))

def hash_pw(password):
    salt=secrets.token_bytes(16); dk=hashlib.pbkdf2_hmac('sha256',password.encode(),salt,210000)
    return f'pbkdf2_sha256$210000${salt.hex()}${dk.hex()}'

def verify_pw(password, stored):
    try:
        alg,it,salt_hex,dk_hex=stored.split('$'); salt=bytes.fromhex(salt_hex)
        got=hashlib.pbkdf2_hmac('sha256',password.encode(),salt,int(it))
        return hmac.compare_digest(got.hex(),dk_hex)
    except Exception: return False

def seed(c):
    t=now()
    # demo records only; these are clearly marked and can be replaced by Admin import.
    students=[
      ('STU-DEMO-001','25CSE001','Arun Kumar','arun@demo.college.edu','9000000001','', 'B.Tech','CSE','III','5','A','2024-2028','faculty@demo.college.edu','hod@demo.college.edu','Day Scholar'),
      ('STU-DEMO-002','25CSE002','Priya S','priya@demo.college.edu','9000000002','','B.Tech','CSE','III','5','A','2024-2028','faculty@demo.college.edu','hod@demo.college.edu','Hostel'),
      ('STU-DEMO-003','25CSE003','Rahul M','rahul@demo.college.edu','9000000003','','B.Tech','CSE','III','5','B','2024-2028','faculty@demo.college.edu','hod@demo.college.edu','Hostel')]
    for s in students:
      c.execute('''INSERT OR IGNORE INTO students(student_id,reg_no,name,email,phone,photo_path,programme,department,year,semester,section,batch,class_advisor_email,hod_email,accommodation,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',s+(t,t))
    staff=[('FAC-DEMO-001','Faculty Demo','faculty@demo.college.edu','9000000010','Assistant Professor','faculty','CSE'),('HOD-DEMO-001','HOD Demo','hod@demo.college.edu','9000000020','Head of Department','hod','CSE')]
    for s in staff: c.execute('''INSERT OR IGNORE INTO staff(staff_id,name,email,phone,designation,role,department,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?)''',s+(t,t))
    # Re-link staff mappings and users after IDs exist.
    stmap={r['email']:r['id'] for r in c.execute('SELECT id,email FROM students')}
    fac=c.execute("SELECT id FROM staff WHERE email='faculty@demo.college.edu'").fetchone()['id']; hod=c.execute("SELECT id FROM staff WHERE email='hod@demo.college.edu'").fetchone()['id']
    c.execute("UPDATE students SET class_advisor_email='faculty@demo.college.edu',hod_email='hod@demo.college.edu' WHERE department='CSE'")
    users=[('arun@demo.college.edu','student','student123',stmap.get('arun@demo.college.edu'),None),('priya@demo.college.edu','student','student123',stmap.get('priya@demo.college.edu'),None),('rahul@demo.college.edu','student','student123',stmap.get('rahul@demo.college.edu'),None),('faculty@demo.college.edu','faculty','faculty123',None,fac),('hod@demo.college.edu','hod','hod123',None,hod),('admin@demo.college.edu','admin','admin123',None,None)]
    for email,role,pw,sid,fid in users:
      if not c.execute('SELECT 1 FROM users WHERE lower(email)=lower(?)',(email,)).fetchone(): c.execute('INSERT INTO users(email,password_hash,role,student_db_id,staff_db_id) VALUES(?,?,?,?,?)',(email,hash_pw(pw),role,sid,fid))

init_db()

# ---------------- Security / authorization ----------------
def audit(actor,role,event,target='',details=''):
    c=conn(); c.execute('INSERT INTO security_audit(actor_email,role,event,target,details,timestamp) VALUES(?,?,?,?,?,?)',(actor,role,event,target,details,now())); c.commit(); c.close()

def q(sql,params=()):
    c=conn(); rows=[dict(x) for x in c.execute(sql,params).fetchall()]; c.close(); return rows

def one(sql,params=()):
    c=conn(); r=c.execute(sql,params).fetchone(); c.close(); return dict(r) if r else None

def notify(email,message):
    c=conn(); c.execute('INSERT INTO notifications(email,message,created_at) VALUES(?,?,?)',(email,message,now())); c.commit(); c.close()

def get_identity(email,role):
    u=one('SELECT * FROM users WHERE lower(email)=lower(?) AND active=1',(email,))
    if not u or u['role']!=role: return None
    if role=='student': return one('SELECT * FROM students WHERE id=? AND active=1 AND lower(email)=lower(?)',(u['student_db_id'],email))
    if role in ('faculty','hod'): return one('SELECT * FROM staff WHERE id=? AND active=1 AND lower(email)=lower(?) AND role=?',(u['staff_db_id'],email,role))
    return {'email':email,'role':'admin'} if role=='admin' else None

def auth_login(email,password,portal):
    email=email.strip().lower()
    u=one('SELECT * FROM users WHERE lower(email)=lower(?) AND active=1',(email,))
    if not u or not verify_pw(password,u['password_hash']):
        audit(email,portal,'LOGIN_FAILED',details='Invalid credentials'); return None
    if u['role']!=portal:
        audit(email,portal,'LOGIN_ROLE_MISMATCH',details=f"Account role is {u['role']}"); return None
    ident=get_identity(email,portal)
    if not ident:
        audit(email,portal,'IDENTITY_MAPPING_FAILED'); return None
    audit(email,portal,'LOGIN_SUCCESS'); return {'email':email,'role':portal,'identity':ident}

def require_role(role): return st.session_state.get('user',{}).get('role')==role

def can_staff_edit_student(staff_email, student_id, field):
    staff=one('SELECT * FROM staff WHERE lower(email)=lower(?) AND active=1',(staff_email,))
    if not staff: return False
    perm=one('''SELECT 1 FROM staff_permissions WHERE faculty_id=? AND permission='FULL_STUDENT_PROFILE_EDIT' AND active=1''',(staff['id'],))
    if perm: return True
    student=one('SELECT * FROM students WHERE id=?',(student_id,))
    return bool(student and staff['role']=='faculty' and student['class_advisor_email'].lower()==staff_email.lower() and field in {'phone','photo_path','accommodation'})

def has_student_permission(student_id,field):
    row=one('SELECT * FROM profile_permissions WHERE target_student_id=? AND field_name=? AND active=1',(student_id,field))
    if not row: return False
    if row['expires_at'] and row['expires_at']<now(): return False
    return True

def safe_filename(name):
    name=Path(name).name
    return re.sub(r'[^A-Za-z0-9._-]','_',name)[:100]

def save_upload(upload,owner):
    if upload is None: return ''
    ext=Path(upload.name).suffix.lower()
    if ext not in ALLOWED_EXT: raise ValueError('Unsupported file type.')
    data=upload.getvalue()
    if len(data)>MAX_UPLOAD: raise ValueError('File is larger than 5 MB.')
    # Basic signature checks for common file types.
    ok=True
    if ext=='.pdf': ok=data.startswith(b'%PDF')
    elif ext in {'.jpg','.jpeg'}: ok=data.startswith(b'\xff\xd8\xff')
    elif ext=='.png': ok=data.startswith(b'\x89PNG\r\n\x1a\n')
    if not ok: raise ValueError('File content does not match its extension.')
    token=secrets.token_hex(12); path=UPLOADS/f'{token}_{safe_filename(upload.name)}'; path.write_bytes(data); return str(path.relative_to(BASE))

def req_code(prefix='REQ'):
    return f'{prefix}-{datetime.now().strftime("%Y%m%d")}-{secrets.token_hex(3).upper()}'

def support_code(): return f'SUP-{datetime.now().strftime("%Y%m%d")}-{secrets.token_hex(3).upper()}'

def add_hist(rid,actor,role,action,remarks=''):
    c=conn(); c.execute('INSERT INTO approval_history(request_id,actor_email,actor_role,action,remarks,timestamp) VALUES(?,?,?,?,?,?)',(rid,actor,role,action,remarks,now())); c.commit(); c.close()

def status_badge(s):
    cls='status-info'
    if 'Approved' in s: cls='status-ok'
    elif 'Rejected' in s: cls='status-danger'
    elif 'Pending' in s or 'Review' in s: cls='status-pending'
    return f'<span class="status {cls}">{esc(s)}</span>'

def render_table(rows,cols=None):
    if not rows: st.info('No records found.'); return
    cols=cols or list(rows[0].keys()); h=''.join(f'<th>{esc(c)}</th>' for c in cols); body=''
    for r in rows: body+='<tr>'+''.join(f'<td>{esc(r.get(c,""))}</td>' for c in cols)+'</tr>'
    st.markdown(f'<div class="table-wrap"><table><thead><tr>{h}</tr></thead><tbody>{body}</tbody></table></div>',unsafe_allow_html=True)

# ---------------- Landing/login ----------------
def brand():
    logo=BASE/'college_logo.png'
    if logo.exists():
        import base64
        logo_html=f'<img src="data:image/png;base64,{base64.b64encode(logo.read_bytes()).decode()}" class="college-logo-img">'
    else:
        logo_html='<div class="brand-logo">🎓</div>'
    st.markdown(f'<div class="login-shell"><div class="brand-card">{logo_html}<h1>PANIMALAR ENGINEERING COLLEGE</h1><p>An Autonomous Institution</p><p>Affiliated to Anna University, Chennai</p><p>(JAISAKTHI EDUCATIONAL TRUST)</p></div></div>',unsafe_allow_html=True)

def login_page():
    brand()
    st.markdown('<div class="login-shell"><div class="login-card">',unsafe_allow_html=True)
    st.markdown('### 🔐 Choose your secure login')
    st.caption('Your role is verified by the server. Selecting a button does not grant that role.')
    cols=st.columns(3)
    if cols[0].button('🎓 Student Login',use_container_width=True): st.session_state.portal='student'; st.rerun()
    if cols[1].button('👨‍🏫 Faculty Login',use_container_width=True): st.session_state.portal='faculty'; st.rerun()
    if cols[2].button('👩‍💼 HOD Login',use_container_width=True): st.session_state.portal='hod'; st.rerun()
    portal=st.session_state.get('portal')
    if portal:
        labels={'student':'🎓 Student Login','faculty':'👨‍🏫 Faculty Login','hod':'👩‍💼 HOD Login'}
        st.markdown(f'## {labels[portal]}')
        if portal=='student': msg='Use your official college email and password. Your register number, department, year and section are retrieved from the official student record.'
        elif portal=='faculty': msg='Faculty accounts are provisioned by the college. Your role and staff identity are verified server-side.'
        else: msg='HOD accounts are provisioned by the college. HOD privileges cannot be self-selected.'
        st.markdown(f'<div class="info-box">🔒 {esc(msg)}</div>',unsafe_allow_html=True)
        with st.form('secure_login',clear_on_submit=False):
            email=st.text_input('Official college email',placeholder='name@college.edu')
            password=st.text_input('Password',type='password',placeholder='Enter password')
            submitted=st.form_submit_button('Sign in securely',type='primary',use_container_width=True)
        if submitted:
            if not email.strip() or not password: st.error('Please enter both email and password.')
            else:
                result=auth_login(email,password,portal)
                if result:
                    st.session_state.user=result; st.session_state.pop('portal',None); st.rerun()
                else: st.error('Login failed. Check your official email/password and account role.')
        if st.button('← Back to login choices',key='backlogin'): st.session_state.pop('portal',None); st.rerun()
    st.markdown('</div></div>',unsafe_allow_html=True)
    st.markdown('<div class="login-shell"><div class="info-box"><b>🔒 Security:</b> Your role is verified server-side. Student identity is matched to the official college record; the portal does not use a roll number typed into a request as proof of identity.</div><div class="info-box"><b>📱 Access:</b> The same portal is responsive on laptop and mobile browsers.</div></div>',unsafe_allow_html=True)
    st.markdown('<div class="footer">Demo environment • Do not enter real college passwords or personal data</div>',unsafe_allow_html=True)

if 'user' not in st.session_state: st.session_state.user=None
if not st.session_state.user:
    login_page(); st.stop()

# ---------------- Authenticated shell ----------------
u=st.session_state.user; role=u['role']; email=u['email']; ident=u['identity']
st.sidebar.markdown('## 🎓 Panimalar\n### Engineering College')
st.sidebar.caption('Smart Campus Portal')
st.sidebar.markdown(f'**Signed in:** {esc(email)}')
if st.sidebar.button('🚪 Log out',use_container_width=True):
    audit(email,role,'LOGOUT'); st.session_state.clear(); st.rerun()

# Admin nav
if role=='student': nav=st.sidebar.radio('Menu',['🏠 Dashboard','📝 New Request','📋 My Requests','💬 Contact Faculty','🏛️ Contact HOD','👤 My Profile','🔔 Notifications'])
elif role=='faculty': nav=st.sidebar.radio('Menu',['🏠 Dashboard','📥 Verification Queue','💬 Student Support','👤 Student Permissions','🧑‍🎓 Manage Student Profile','🔔 Notifications'])
elif role=='hod': nav=st.sidebar.radio('Menu',['🏠 Dashboard','📥 Approval Queue','🔎 Search & History','💬 HOD Support','🔐 Faculty Permissions','🔔 Notifications'])
else: nav=st.sidebar.radio('Menu',['🏠 Dashboard','👥 Student Management','👨‍🏫 Faculty & HOD Management','📋 Requests','🛡️ Security Audit'])

# ---------------- Student ----------------
if role=='student':
    s=ident
    st.markdown(f'<div class="topbar"><b>Welcome, {esc(s["name"])}</b><br><span class="small-muted">{esc(s["reg_no"])} • {esc(s["department"])} • Year {esc(s["year"])} • Section {esc(s["section"])} • {esc(s["accommodation"])}</span></div>',unsafe_allow_html=True)
    if nav=='🏠 Dashboard':
        total=one('SELECT COUNT(*) n FROM requests WHERE student_id=?',(s['id'],))['n']; pending=one("SELECT COUNT(*) n FROM requests WHERE student_id=? AND status NOT LIKE 'Approved%' AND status NOT LIKE 'Rejected%'",(s['id'],))['n']; unread=one('SELECT COUNT(*) n FROM notifications WHERE lower(email)=lower(?) AND is_read=0',(email,))['n']
        a,b,c=st.columns(3); a.metric('My Requests',total); b.metric('In Progress',pending); c.metric('Unread Notifications',unread)
        st.markdown('### Quick access')
        a,b,c,d=st.columns(4); a.button('📝 New Request',use_container_width=True); b.button('📋 My Requests',use_container_width=True); c.button('💬 Contact Faculty',use_container_width=True); d.button('🏛️ Contact HOD',use_container_width=True)
        st.markdown('### How your request moves'); st.markdown('**Student → Assigned Faculty → HOD → Student**  \nRoutine issues can be resolved by faculty; support cases can be escalated to the HOD.')
    elif nav=='📝 New Request':
        st.header('📝 Submit a Request'); st.caption('Your identity is automatically attached from the official student record.')
        types=['Leave','OD','Apology','Late Permission','Club Inauguration','Event Permission','Workshop / Seminar','Industrial Visit','Guest Lecture','Other']
        with st.form('request_form'):
            rt=st.selectbox('Request type',types)
            title=st.text_input('Title')
            event_date=st.date_input('Date (if applicable)',value=datetime.now().date())
            details=''; attachment=None
            if rt=='Leave':
                reason=st.selectbox('Leave reason',['Medical Leave','Personal Leave','Family Function','Emergency','Other / Customise'])
                custom=st.text_area('Custom reason / message') if reason=='Other / Customise' else ''
                details=f'Reason: {reason}\n{custom}'
                attachment=st.file_uploader('Medical/supporting document (optional)',type=['pdf','png','jpg','jpeg'])
            elif rt=='OD':
                event=st.text_input('Event / programme name'); venue=st.text_input('Venue'); org=st.text_input('Organising institution'); details=f'Event: {event}\nVenue: {venue}\nOrganisation: {org}\n{st.text_area("Additional details")}'
                attachment=st.file_uploader('Invitation / proof (optional)',type=['pdf','png','jpg','jpeg'])
            elif rt in ['Event Permission','Club Inauguration','Workshop / Seminar','Industrial Visit','Guest Lecture']:
                venue=st.text_input('Venue'); coordinator=st.text_input('Faculty coordinator'); expected=st.number_input('Expected participants',min_value=1,max_value=10000,value=10); details=f'Venue: {venue}\nFaculty coordinator: {coordinator}\nExpected participants: {expected}\n{st.text_area("Description / requirements")}'
                attachment=st.file_uploader('Proposal / supporting document (optional)',type=['pdf','png','jpg','jpeg'])
            else: details=st.text_area('Explain your request / issue'); attachment=st.file_uploader('Supporting document (optional)',type=['pdf','png','jpg','jpeg'])
            submit=st.form_submit_button('Submit request',type='primary',use_container_width=True)
        if submit:
            if not title.strip() or not details.strip(): st.error('Title and details are required.')
            else:
                dup=one("SELECT request_code,status FROM requests WHERE student_id=? AND request_type=? AND event_date=? AND status NOT LIKE 'Rejected%' ORDER BY id DESC LIMIT 1",(s['id'],rt,str(event_date)))
                if dup: st.warning(f'A similar request already exists: {dup["request_code"]} ({dup["status"]}).')
                else:
                    try: ap=save_upload(attachment,s['student_id']) if attachment else ''
                    except Exception as e: st.error(str(e)); ap=''
                    if attachment and not ap: st.stop()
                    fac=s['class_advisor_email'] or 'faculty@demo.college.edu'; code=req_code('REQ'); t=now(); c=conn(); c.execute('INSERT INTO requests(request_code,student_id,request_type,title,details,event_date,attachment_path,status,current_approver,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)',(code,s['id'],rt,title,details,str(event_date),ap,'Pending Faculty Verification',fac,t,t)); rid=c.execute('SELECT last_insert_rowid()').fetchone()[0]; c.commit(); c.close(); add_hist(rid,email,'student','SUBMITTED'); notify(fac,f'New request {code} from {s["name"]}.'); st.success(f'Request submitted successfully. Request ID: {code}')
    elif nav=='📋 My Requests':
        st.header('📋 My Requests'); rows=q('SELECT request_code AS "Request ID",request_type AS Type,title AS Title,event_date AS Date,status AS Status,updated_at AS "Last Updated" FROM requests WHERE student_id=? ORDER BY id DESC',(s['id'],)); render_table(rows)
        if rows:
            code=st.selectbox('Open request',[x['Request ID'] for x in rows]); r=one('SELECT r.*,s.name,s.reg_no,s.email FROM requests r JOIN students s ON s.id=r.student_id WHERE r.request_code=? AND r.student_id=?',(code,s['id']))
            if r:
                st.markdown(f'### {esc(r["request_code"])} {status_badge(r["status"])}',unsafe_allow_html=True); st.write(r['details'])
                hist=q('SELECT actor_role AS Role,action AS Action,remarks AS Remarks,timestamp AS Time FROM approval_history WHERE request_id=? ORDER BY id',(r['id'],)); st.markdown('#### Approval timeline');
                for h in hist: st.markdown(f'<div class="timeline"><div class="timeline-item"><b>{esc(h["Action"])}</b><br>{esc(h["Role"])} • {esc(h["Time"])}<br><span class="small-muted">{esc(h["Remarks"])}</span></div></div>',unsafe_allow_html=True)
    elif nav=='💬 Contact Faculty' or nav=='🏛️ Contact HOD':
        target_type='faculty' if nav=='💬 Contact Faculty' else 'hod'; st.header('💬 Contact Faculty' if target_type=='faculty' else '🏛️ Contact HOD');
        if target_type=='faculty': targets=q('SELECT name,email FROM staff WHERE role="faculty" AND active=1 AND lower(department)=lower(?)',(s['department'],)); categories=['Academic clarification','Attendance','Request clarification','General support','Other']
        else: targets=q('SELECT name,email FROM staff WHERE role="hod" AND active=1 AND lower(department)=lower(?)',(s['department'],)); categories=['Faculty-related concern','Academic issue','Department issue','Request requiring HOD attention','Student support','Other']
        with st.form('support_new'):
            target=st.selectbox('Recipient',targets,format_func=lambda x:f'{x["name"]} — {x["email"]}') if targets else None; cat=st.selectbox('Category',categories); subject=st.text_input('Subject'); message=st.text_area('Message'); confidential=st.selectbox('Privacy',['Confidential — only authorized recipient(s)','Sensitive — HOD only']) if target_type=='hod' else 'Confidential — only authorized recipient(s)'; send=st.form_submit_button('Send securely',type='primary',use_container_width=True)
        if send:
            if not target or not subject.strip() or not message.strip(): st.error('Recipient, subject and message are required.')
            else:
                if target_type=='faculty' and confidential.startswith('Sensitive'): st.error('Sensitive reporting should use Contact HOD.'); st.stop()
                code=support_code(); t=now(); c=conn(); c.execute('INSERT INTO support_threads(thread_code,student_id,target_type,target_email,category,subject,confidentiality,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?)',(code,s['id'],target_type,target['email'],cat,subject,'sensitive_hod' if confidential.startswith('Sensitive') else 'confidential',t,t)); tid=c.execute('SELECT last_insert_rowid()').fetchone()[0]; c.execute('INSERT INTO support_messages(thread_id,sender_email,sender_role,message,created_at) VALUES(?,?,?,?,?)',(tid,email,'student',message,t)); c.commit(); c.close(); notify(target['email'],f'New confidential support case {code}.'); audit(email,'student','SUPPORT_CREATED',code,target_type); st.success(f'Sent securely. Reference: {code}')
        my=q('SELECT t.id,t.thread_code AS Reference,t.category AS Category,t.subject AS Subject,t.status AS Status,t.updated_at AS Updated FROM support_threads t WHERE t.student_id=? ORDER BY t.id DESC',(s['id'],)); render_table(my)
        if my:
            tid=st.selectbox('Open conversation',[x['id'] for x in my],format_func=lambda x:next(y['Reference'] for y in my if y['id']==x)); msgs=q('SELECT sender_role AS From,message AS Message,created_at AS Time FROM support_messages WHERE thread_id=? ORDER BY id',(tid,)); render_table(msgs)
    elif nav=='👤 My Profile':
        st.header('👤 My Profile');
        pic=Path(BASE/s['photo_path']) if s['photo_path'] else None
        cols=st.columns([1,3]);
        with cols[0]:
            if pic and pic.exists(): st.image(str(pic),width=110)
            else: st.markdown('<div class="avatar-placeholder">👤</div>',unsafe_allow_html=True)
        with cols[1]: st.markdown(f'**{esc(s["name"])}**  \n{esc(s["reg_no"])} • {esc(s["department"])} • Year {esc(s["year"])} • Section {esc(s["section"])}'); st.caption(f'Accommodation: {s["accommodation"]} | Official email: {s["email"]}')
        st.markdown('### Update permitted information')
        allowed=[f for f in ['phone','accommodation','photo_path'] if has_student_permission(s['id'],f)]
        if not allowed: st.info('No profile-edit permissions have been granted by your assigned faculty yet. Use the request-permission option below if needed.')
        else:
            with st.form('student_profile_edit'):
                phone=st.text_input('Phone',value=s['phone'],disabled='phone' not in allowed); acc=st.selectbox('Accommodation',['Day Scholar','Hostel'],index=0 if s['accommodation']=='Day Scholar' else 1,disabled='accommodation' not in allowed); photo=st.file_uploader('Photo',type=['png','jpg','jpeg'],disabled='photo_path' not in allowed); save=st.form_submit_button('Save permitted changes',type='primary')
            if save:
                c=conn(); changed=[]
                if 'phone' in allowed: c.execute('UPDATE students SET phone=?,updated_at=? WHERE id=?',(phone.strip(),now(),s['id'])); changed.append('phone')
                if 'accommodation' in allowed: c.execute('UPDATE students SET accommodation=?,updated_at=? WHERE id=?',(acc,now(),s['id'])); changed.append('accommodation')
                if 'photo_path' in allowed and photo:
                    try: p=save_upload(photo,s['student_id']); c.execute('UPDATE students SET photo_path=?,updated_at=? WHERE id=?',(p,now(),s['id'])); changed.append('photo')
                    except Exception as e: c.close(); st.error(str(e)); st.stop()
                c.commit(); c.close(); audit(email,'student','PROFILE_UPDATED',s['student_id'],','.join(changed)); st.success('Profile updated.'); st.rerun()
        st.markdown('### Request profile-update permission')
        requested=st.selectbox('Field',['Phone','Photo','Accommodation']);
        if st.button('Request permission'):
            notify(s['class_advisor_email'],f'Student {s["name"]} requests permission to update {requested}.'); audit(email,'student','PROFILE_PERMISSION_REQUESTED',s['student_id'],requested); st.success('Permission request sent to your assigned faculty.')
    elif nav=='🔔 Notifications':
        st.header('🔔 Notifications'); rows=q('SELECT message AS Message,created_at AS Time,is_read AS Read FROM notifications WHERE lower(email)=lower(?) ORDER BY id DESC',(email,)); render_table(rows); connx=conn(); connx.execute('UPDATE notifications SET is_read=1 WHERE lower(email)=lower(?)',(email,)); connx.commit(); connx.close()

# ---------------- Faculty ----------------
elif role=='faculty':
    f=ident; st.markdown(f'<div class="topbar"><b>Faculty Dashboard</b><br><span class="small-muted">{esc(f["name"])} • {esc(f["department"])} • {esc(f["designation"])}</span></div>',unsafe_allow_html=True)
    if nav=='🏠 Dashboard':
        a=one("SELECT COUNT(*) n FROM requests WHERE current_approver=? AND status='Pending Faculty Verification'",(email,))['n']; b=one("SELECT COUNT(*) n FROM support_threads WHERE target_type='faculty' AND target_email=? AND status='Open'",(email,))['n']; c=one('SELECT COUNT(*) n FROM notifications WHERE lower(email)=lower(?) AND is_read=0',(email,))['n']; x,y,z=st.columns(3); x.metric('Pending Verification',a); y.metric('Support Cases',b); z.metric('Unread',c)
        st.info('Verify requests, return incomplete submissions, communicate with students, and grant only the profile permissions you are authorized to grant.')
    elif nav=='📥 Verification Queue':
        st.header('📥 Verification Queue'); rows=q('''SELECT r.id,r.request_code AS "Request ID",s.name AS Student,s.reg_no AS "Reg No",r.request_type AS Type,r.title AS Title,r.event_date AS Date,r.status AS Status FROM requests r JOIN students s ON s.id=r.student_id WHERE r.current_approver=? AND r.status='Pending Faculty Verification' ORDER BY r.id DESC''',(email,)); render_table([{k:v for k,v in x.items() if k!='id'} for x in rows]);
        if rows:
            rid=st.selectbox('Open request',[x['id'] for x in rows],format_func=lambda x:next(y['Request ID'] for y in rows if y['id']==x)); r=one('SELECT r.*,s.name,s.reg_no,s.email,s.department,s.year,s.section,s.hod_email FROM requests r JOIN students s ON s.id=r.student_id WHERE r.id=? AND r.current_approver=?',(rid,email)); st.markdown(f'### {esc(r["request_code"])} — {esc(r["title"])}'); st.write(r['details']);
            with st.form('faculty_action'):
                remarks=st.text_area('Remarks'); c1,c2,c3=st.columns(3); verify=c1.form_submit_button('✅ Verify & Send to HOD'); back=c2.form_submit_button('↩️ Send Back'); reject=c3.form_submit_button('❌ Reject')
            if verify or back or reject:
                c=conn()
                if verify: new='Pending HOD Approval'; action='VERIFIED'; approver=r['hod_email'] or 'hod@demo.college.edu'; msg=f'{r["request_code"]} was verified by faculty and sent to HOD.'; notify(approver,msg); notify(r['email'],msg)
                elif back: new='Returned to Student'; action='SENT_BACK'; approver=r['email']; notify(r['email'],f'{r["request_code"]} was sent back for correction.')
                else: new='Rejected by Faculty'; action='REJECTED'; approver=''; notify(r['email'],f'{r["request_code"]} was rejected by faculty.')
                c.execute('UPDATE requests SET status=?,current_approver=?,remarks=?,updated_at=? WHERE id=? AND current_approver=?',(new,approver,remarks,now(),rid,email)); c.commit(); c.close(); add_hist(rid,email,'faculty',action,remarks); audit(email,'faculty','REQUEST_ACTION',r['request_code'],action); st.success('Action recorded.'); st.rerun()
    elif nav=='💬 Student Support':
        st.header('💬 Student Support'); rows=q('SELECT t.id,t.thread_code AS Reference,s.name AS Student,t.category AS Category,t.subject AS Subject,t.status AS Status,t.confidentiality AS Privacy FROM support_threads t JOIN students s ON s.id=t.student_id WHERE t.target_type="faculty" AND lower(t.target_email)=lower(?) ORDER BY t.id DESC',(email,)); render_table([{k:v for k,v in x.items() if k!='id'} for x in rows]);
        if rows:
            tid=st.selectbox('Open case',[x['id'] for x in rows],format_func=lambda x:next(y['Reference'] for y in rows if y['id']==x)); th=one('SELECT t.*,s.email student_email,s.name student_name,s.department FROM support_threads t JOIN students s ON s.id=t.student_id WHERE t.id=? AND lower(t.target_email)=lower(?)',(tid,email));
            if th:
                render_table(q('SELECT sender_role AS From,message AS Message,created_at AS Time FROM support_messages WHERE thread_id=? ORDER BY id',(tid,)))
                with st.form('faculty_reply'):
                    reply=st.text_area('Reply'); send=st.form_submit_button('Reply securely',type='primary'); escbtn=st.form_submit_button('Escalate to HOD')
                if send and reply.strip():
                    c=conn(); c.execute('INSERT INTO support_messages(thread_id,sender_email,sender_role,message,created_at) VALUES(?,?,?,?,?)',(tid,email,'faculty',reply.strip(),now())); c.execute('UPDATE support_threads SET updated_at=? WHERE id=?',(now(),tid)); c.commit(); c.close(); notify(th['student_email'],f'New reply on {th["thread_code"]}.'); st.rerun()
                if escbtn:
                    hod=th.get('hod_email') or one('SELECT email FROM staff WHERE role="hod" AND department=? AND active=1',(th['department'],))
                    hod_email=hod['email'] if isinstance(hod,dict) else hod
                    c=conn(); c.execute('UPDATE support_threads SET target_type="hod",target_email=?,updated_at=? WHERE id=?',(hod_email,now(),tid)); c.commit(); c.close(); notify(hod_email,f'Support case {th["thread_code"]} was escalated by faculty.'); audit(email,'faculty','SUPPORT_ESCALATED',th['thread_code']); st.success('Escalated to HOD.'); st.rerun()
    elif nav=='👤 Student Permissions':
        st.header('👤 Student Profile Permissions'); st.caption('Faculty can grant individual student permissions. HOD controls whether you have full student-profile management access.')
        full=one('''SELECT 1 FROM staff_permissions WHERE faculty_id=? AND permission='FULL_STUDENT_PROFILE_EDIT' AND active=1''',(f['id'],))
        students=q('SELECT id,name,reg_no,email,phone,accommodation FROM students WHERE active=1 AND lower(department)=lower(?) AND (lower(class_advisor_email)=lower(?) OR ?=1) ORDER BY name',(f['department'],email,1 if full else 0));
        if not students: st.info('No students in your department.')
        else:
            sid=st.selectbox('Student',[x['id'] for x in students],format_func=lambda x:next(y['name']+' — '+y['reg_no'] for y in students if y['id']==x)); field=st.selectbox('Permission',['Phone','Photo','Accommodation','FULL PROFILE'] if full else ['Phone','Photo','Accommodation']); expires=st.date_input('Permission expiry (optional)',value=None)
            if st.button('Grant permission',type='primary'):
                if field=='FULL PROFILE' and not full: st.error('Not authorized.')
                else:
                    fn={'Phone':'phone','Photo':'photo_path','Accommodation':'accommodation','FULL PROFILE':'FULL PROFILE'}[field]; exp=str(expires) if expires else ''; c=conn(); c.execute('INSERT INTO profile_permissions(target_student_id,field_name,granted_by,granted_at,expires_at,active) VALUES(?,?,?,?,?,1) ON CONFLICT(target_student_id,field_name) DO UPDATE SET granted_by=excluded.granted_by,granted_at=excluded.granted_at,expires_at=excluded.expires_at,active=1',(sid,fn,email,now(),exp)); c.commit(); c.close(); notify(next(x['email'] for x in students if x['id']==sid),f'Faculty granted permission to update {field}.'); audit(email,'faculty','PROFILE_PERMISSION_GRANTED',str(sid),field); st.success('Permission granted.')
            if st.button('Revoke selected permission'):
                fn={'Phone':'phone','Photo':'photo_path','Accommodation':'accommodation','FULL PROFILE':'FULL PROFILE'}[field]; c=conn(); c.execute('UPDATE profile_permissions SET active=0 WHERE target_student_id=? AND field_name=?',(sid,fn)); c.commit(); c.close(); audit(email,'faculty','PROFILE_PERMISSION_REVOKED',str(sid),field); st.success('Permission revoked.')
    elif nav=='🧑‍🎓 Manage Student Profile':
        st.header('🧑‍🎓 Manage Student Profile')
        full=one("SELECT 1 FROM staff_permissions WHERE faculty_id=? AND permission='FULL_STUDENT_PROFILE_EDIT' AND active=1",(f['id'],))
        students=q('SELECT id,name,reg_no,email,phone,accommodation,photo_path,department,year,section FROM students WHERE active=1 AND lower(department)=lower(?) AND (lower(class_advisor_email)=lower(?) OR ?=1) ORDER BY name',(f['department'],email,1 if full else 0))
        if not students: st.info('No students are currently assigned to you.')
        else:
            sid=st.selectbox('Student',[x['id'] for x in students],format_func=lambda x:next(y['name']+' — '+y['reg_no'] for y in students if y['id']==x))
            stu=next(x for x in students if x['id']==sid)
            allowed=[]
            if full: allowed=['phone','accommodation','photo_path']
            else:
                for fn in ['phone','accommodation','photo_path']:
                    if one('SELECT 1 FROM profile_permissions WHERE target_student_id=? AND field_name=? AND active=1',(sid,fn)): allowed.append(fn)
            if not allowed: st.warning('No field permissions are active for this student. Grant an individual permission first.')
            with st.form('faculty_profile_edit'):
                phone=st.text_input('Phone',value=stu['phone'],disabled='phone' not in allowed)
                acc=st.selectbox('Accommodation',['Day Scholar','Hostel'],index=0 if stu['accommodation']=='Day Scholar' else 1,disabled='accommodation' not in allowed)
                photo=st.file_uploader('Photo',type=['png','jpg','jpeg'],disabled='photo_path' not in allowed)
                save=st.form_submit_button('Save authorized changes',type='primary')
            if save:
                c=conn(); changed=[]
                if 'phone' in allowed: c.execute('UPDATE students SET phone=?,updated_at=? WHERE id=?',(phone.strip(),now(),sid)); changed.append('phone')
                if 'accommodation' in allowed: c.execute('UPDATE students SET accommodation=?,updated_at=? WHERE id=?',(acc,now(),sid)); changed.append('accommodation')
                if 'photo_path' in allowed and photo:
                    try: p=save_upload(photo,stu['reg_no']); c.execute('UPDATE students SET photo_path=?,updated_at=? WHERE id=?',(p,now(),sid)); changed.append('photo')
                    except Exception as e: c.close(); st.error(str(e)); st.stop()
                c.commit(); c.close(); audit(email,'faculty','STUDENT_PROFILE_UPDATED',stu['reg_no'],','.join(changed)); st.success('Authorized profile changes saved.'); st.rerun()
    elif nav=='🔔 Notifications':
        rows=q('SELECT message AS Message,created_at AS Time,is_read AS Read FROM notifications WHERE lower(email)=lower(?) ORDER BY id DESC',(email,)); render_table(rows); c=conn(); c.execute('UPDATE notifications SET is_read=1 WHERE lower(email)=lower(?)',(email,)); c.commit(); c.close()

# ---------------- HOD ----------------
elif role=='hod':
    h=ident; st.markdown(f'<div class="topbar"><b>HOD Dashboard</b><br><span class="small-muted">{esc(h["name"])} • {esc(h["department"])} • {esc(h["designation"])}</span></div>',unsafe_allow_html=True)
    if nav=='🏠 Dashboard':
        a=one("SELECT COUNT(*) n FROM requests r JOIN students s ON s.id=r.student_id WHERE r.current_approver=? AND r.status='Pending HOD Approval'",(email,))['n']; b=one("SELECT COUNT(*) n FROM support_threads WHERE target_type='hod' AND target_email=? AND status='Open'",(email,))['n']; c=one('SELECT COUNT(*) n FROM notifications WHERE lower(email)=lower(?) AND is_read=0',(email,))['n']; x,y,z=st.columns(3); x.metric('Pending HOD Approval',a); y.metric('Direct Support / Reports',b); z.metric('Unread',c)
    elif nav=='📥 Approval Queue':
        st.header('📥 Smart HOD Approval Queue'); dept=h['department']; types=['All']+[x['request_type'] for x in q('SELECT DISTINCT request_type FROM requests ORDER BY request_type')]; c1,c2=st.columns(2); ft=c1.selectbox('Request type',types); search=c2.text_input('Search student / request ID'); sql='''SELECT r.id,r.request_code AS "Request ID",s.name AS Student,s.reg_no AS "Reg No",r.request_type AS Type,r.title AS Title,r.event_date AS Date,r.status AS Status FROM requests r JOIN students s ON s.id=r.student_id WHERE s.department=? AND r.current_approver=? AND r.status='Pending HOD Approval' '''; params=[dept,email];
        if ft!='All': sql+=' AND r.request_type=?'; params.append(ft)
        if search.strip(): sql+=' AND (r.request_code LIKE ? OR s.name LIKE ? OR s.reg_no LIKE ?)'; params += [f'%{search.strip()}%']*3
        sql+=' ORDER BY r.id DESC'; rows=q(sql,tuple(params)); render_table([{k:v for k,v in x.items() if k!='id'} for x in rows]);
        if rows:
            rid=st.selectbox('Open request',[x['id'] for x in rows],format_func=lambda x:next(y['Request ID'] for y in rows if y['id']==x)); r=one('SELECT r.*,s.name,s.reg_no,s.email,s.department FROM requests r JOIN students s ON s.id=r.student_id WHERE r.id=? AND r.current_approver=? AND s.department=?',(rid,email,dept)); st.markdown(f'### {esc(r["request_code"])} — {esc(r["title"])}'); st.write(r['details']);
            with st.form('hod_action'):
                remarks=st.text_area('Remarks'); a,b,c=st.columns(3); approve=a.form_submit_button('✅ Approve'); back=b.form_submit_button('↩️ Send Back'); reject=c.form_submit_button('❌ Reject')
            if approve or back or reject:
                if approve: new='Approved'; action='APPROVED'; notify(r['email'],f'{r["request_code"]} has been approved by HOD.')
                elif back: new='Returned to Student'; action='SENT_BACK'; notify(r['email'],f'{r["request_code"]} was sent back by HOD for correction.')
                else: new='Rejected by HOD'; action='REJECTED'; notify(r['email'],f'{r["request_code"]} was rejected by HOD.')
                c=conn(); c.execute('UPDATE requests SET status=?,current_approver=?,remarks=?,updated_at=? WHERE id=? AND current_approver=?',(new,r['email'] if new!='Approved' else '',remarks,now(),rid,email)); c.commit(); c.close(); add_hist(rid,email,'hod',action,remarks); audit(email,'hod','REQUEST_ACTION',r['request_code'],action); st.success('Action recorded.'); st.rerun()
    elif nav=='🔎 Search & History':
        st.header('🔎 Search Request History'); term=st.text_input('Request ID, student name or register number');
        if term.strip(): rows=q('''SELECT r.request_code AS "Request ID",s.name AS Student,s.reg_no AS "Reg No",r.request_type AS Type,r.status AS Status,r.created_at AS Created,r.updated_at AS Updated FROM requests r JOIN students s ON s.id=r.student_id WHERE s.department=? AND (r.request_code LIKE ? OR s.name LIKE ? OR s.reg_no LIKE ?) ORDER BY r.id DESC''',(h['department'],f'%{term}%',f'%{term}%',f'%{term}%')); render_table(rows)
    elif nav=='💬 HOD Support':
        st.header('🏛️ Direct Student Support / Reports'); rows=q('SELECT t.id,t.thread_code AS Reference,s.name AS Student,t.category AS Category,t.subject AS Subject,t.confidentiality AS Privacy,t.status AS Status FROM support_threads t JOIN students s ON s.id=t.student_id WHERE t.target_type="hod" AND lower(t.target_email)=lower(?) AND s.department=? ORDER BY t.id DESC',(email,h['department'])); render_table([{k:v for k,v in x.items() if k!='id'} for x in rows]);
        if rows:
            tid=st.selectbox('Open report',[x['id'] for x in rows],format_func=lambda x:next(y['Reference'] for y in rows if y['id']==x)); th=one('SELECT t.*,s.email student_email,s.name student_name FROM support_threads t JOIN students s ON s.id=t.student_id WHERE t.id=? AND lower(t.target_email)=lower(?) AND s.department=?',(tid,email,h['department'])); render_table(q('SELECT sender_role AS From,message AS Message,created_at AS Time FROM support_messages WHERE thread_id=? ORDER BY id',(tid,))); 
            with st.form('hod_reply'): reply=st.text_area('Reply'); send=st.form_submit_button('Reply securely',type='primary'); close=st.form_submit_button('Close case')
            if send and reply.strip(): c=conn(); c.execute('INSERT INTO support_messages(thread_id,sender_email,sender_role,message,created_at) VALUES(?,?,?,?,?)',(tid,email,'hod',reply.strip(),now())); c.execute('UPDATE support_threads SET updated_at=? WHERE id=?',(now(),tid)); c.commit(); c.close(); notify(th['student_email'],f'New HOD reply on {th["thread_code"]}.'); st.rerun()
            if close: c=conn(); c.execute('UPDATE support_threads SET status="Closed",updated_at=? WHERE id=?',(now(),tid)); c.commit(); c.close(); audit(email,'hod','SUPPORT_CLOSED',th['thread_code']); st.rerun()
    elif nav=='🔐 Faculty Permissions':
        st.header('🔐 Faculty Access Management'); rows=q('SELECT id,name,email,designation FROM staff WHERE role="faculty" AND active=1 AND lower(department)=lower(?)',(h['department'],)); render_table(rows,['name','email','designation']);
        if rows:
            fid=st.selectbox('Faculty',[x['id'] for x in rows],format_func=lambda x:next(y['name']+' — '+y['email'] for y in rows if y['id']==x)); action=st.radio('Permission',['Grant Full Student Profile Access','Revoke Full Student Profile Access']);
            if st.button('Apply permission',type='primary'):
                c=conn(); active=1 if action.startswith('Grant') else 0; c.execute('INSERT INTO staff_permissions(faculty_id,permission,granted_by,granted_at,active) VALUES(?,?,?,?,?) ON CONFLICT(faculty_id,permission) DO UPDATE SET granted_by=excluded.granted_by,granted_at=excluded.granted_at,active=excluded.active',(fid,'FULL_STUDENT_PROFILE_EDIT',email,now(),active)); c.commit(); c.close(); fac=next(x['email'] for x in rows if x['id']==fid); notify(fac,f'HOD {"granted" if active else "revoked"} full student profile management access.'); audit(email,'hod','FACULTY_PERMISSION_CHANGED',fac,action); st.success('Permission updated.')
    elif nav=='🔔 Notifications':
        rows=q('SELECT message AS Message,created_at AS Time,is_read AS Read FROM notifications WHERE lower(email)=lower(?) ORDER BY id DESC',(email,)); render_table(rows); c=conn(); c.execute('UPDATE notifications SET is_read=1 WHERE lower(email)=lower(?)',(email,)); c.commit(); c.close()

# ---------------- Admin ----------------
else:
    st.markdown('<div class="topbar"><b>Admin Control Center</b><br><span class="small-muted">Institutional master-data management and security monitoring</span></div>',unsafe_allow_html=True)
    if nav=='🏠 Dashboard':
        a=one('SELECT COUNT(*) n FROM students WHERE active=1')['n']; b=one('SELECT COUNT(*) n FROM staff WHERE active=1')['n']; c=one('SELECT COUNT(*) n FROM requests')['n']; d=one('SELECT COUNT(*) n FROM security_audit')['n']; x,y,z,w=st.columns(4); x.metric('Active Students',a); y.metric('Active Staff',b); z.metric('Requests',c); w.metric('Audit Events',d); st.info('Use Student/Staff management to import official records. Do not enter real passwords into the demo.')
    elif nav=='👥 Student Management':
        st.header('👥 Student Master Database'); st.caption('The official database is the source of identity. Students cannot edit identity fields such as register number, department or role.')
        with st.expander('➕ Add one student'):
            with st.form('add_student'):
                sid=st.text_input('Student ID'); reg=st.text_input('Register No'); name=st.text_input('Name'); em=st.text_input('College Email'); phone=st.text_input('Phone'); prog=st.text_input('Programme',value='B.Tech'); dept=st.text_input('Department',value='CSE'); year=st.text_input('Year',value='III'); sem=st.text_input('Semester',value='5'); sec=st.text_input('Section',value='A'); batch=st.text_input('Batch',value='2024-2028'); acc=st.selectbox('Accommodation',['Day Scholar','Hostel']); advisor=st.text_input('Class Advisor Email'); hod=st.text_input('HOD Email'); submit=st.form_submit_button('Add student',type='primary')
            if submit:
                try:
                    c=conn(); c.execute('INSERT INTO students(student_id,reg_no,name,email,phone,programme,department,year,semester,section,batch,class_advisor_email,hod_email,accommodation,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',(sid,reg,name,em.lower(),phone,prog,dept,year,sem,sec,batch,advisor.lower(),hod.lower(),acc,now(),now())); c.commit(); c.close(); audit(email,'admin','STUDENT_CREATED',sid); st.success('Student added.');
                except Exception as e: st.error(f'Could not add student: {e}')
        with st.expander('📥 Import students from CSV'):
            st.write('Required columns: student_id, reg_no, name, email, phone, programme, department, year, semester, section, batch, class_advisor_email, hod_email, accommodation')
            up=st.file_uploader('CSV file',type=['csv'],key='student_import')
            if up and st.button('Validate & import students'):
                text=up.getvalue().decode('utf-8-sig'); reader=csv.DictReader(io.StringIO(text)); required={'student_id','reg_no','name','email','phone','programme','department','year','semester','section','batch','class_advisor_email','hod_email','accommodation'}; missing=required-set(reader.fieldnames or [])
                if missing: st.error('Missing columns: '+', '.join(sorted(missing)))
                else:
                    ok=0; errors=[]; c=conn()
                    for i,row in enumerate(reader,start=2):
                        try:
                            if row['accommodation'] not in ('Day Scholar','Hostel'): raise ValueError('Accommodation must be Day Scholar or Hostel')
                            c.execute('INSERT INTO students(student_id,reg_no,name,email,phone,programme,department,year,semester,section,batch,class_advisor_email,hod_email,accommodation,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',(row['student_id'].strip(),row['reg_no'].strip(),row['name'].strip(),row['email'].strip().lower(),row['phone'].strip(),row['programme'].strip(),row['department'].strip(),row['year'].strip(),row['semester'].strip(),row['section'].strip(),row['batch'].strip(),row['class_advisor_email'].strip().lower(),row['hod_email'].strip().lower(),row['accommodation'].strip(),now(),now())); ok+=1
                        except Exception as e: errors.append(f'Row {i}: {e}')
                    c.commit(); c.close(); st.success(f'Imported {ok} students.'); [st.error(x) for x in errors[:10]]
        render_table(q('SELECT student_id AS "Student ID",reg_no AS "Register No",name AS Name,email AS Email,department AS Department,year AS Year,section AS Section,accommodation AS Accommodation,active AS Active FROM students ORDER BY id DESC'))
    elif nav=='👨‍🏫 Faculty & HOD Management':
        st.header('👨‍🏫 Faculty & HOD Master Records');
        with st.expander('➕ Add faculty/HOD'):
            with st.form('add_staff'):
                sid=st.text_input('Staff ID'); name=st.text_input('Name'); em=st.text_input('Official Email'); phone=st.text_input('Phone'); des=st.text_input('Designation'); r=st.selectbox('Role',['faculty','hod']); dept=st.text_input('Department',value='CSE'); add=st.form_submit_button('Add staff',type='primary')
            if add:
                try:
                    c=conn(); c.execute('INSERT INTO staff(staff_id,name,email,phone,designation,role,department,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?)',(sid,name,em.lower(),phone,des,r,dept,now(),now())); c.commit(); c.close(); audit(email,'admin','STAFF_CREATED',sid); st.success('Staff record added.');
                except Exception as e: st.error(str(e))
        render_table(q('SELECT staff_id AS "Staff ID",name AS Name,email AS Email,designation AS Designation,role AS Role,department AS Department,active AS Active FROM staff ORDER BY role,name'))
    elif nav=='📋 Requests':
        st.header('📋 All Requests'); render_table(q('SELECT r.request_code AS "Request ID",s.name AS Student,s.reg_no AS "Reg No",r.request_type AS Type,r.status AS Status,r.created_at AS Created FROM requests r JOIN students s ON s.id=r.student_id ORDER BY r.id DESC'))
    elif nav=='🛡️ Security Audit':
        st.header('🛡️ Security Audit Log'); rows=q('SELECT timestamp AS Time,actor_email AS Actor,role AS Role,event AS Event,target AS Target,details AS Details FROM security_audit ORDER BY id DESC LIMIT 300'); render_table(rows); st.caption('Audit logs are read-only from the portal UI.')

st.markdown('<div class="footer">Panimalar Smart Campus Portal • Role-based access • Confidential support • Audit logging • Demo build</div>',unsafe_allow_html=True)
