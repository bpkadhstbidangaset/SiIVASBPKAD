Si IVAS - Complete Project (Flask)

Features:
- Role: admin, skpd
- Admin: manage SKPD users, view all vehicles, delete, export CSV
- SKPD: add/edit/delete vehicles, upload photos (depan, belakang, bpkb, stnk)
- File upload: local (static/uploads) by default. If CLOUDINARY_URL set, uploads go to Cloudinary.
- Ready to deploy to Render (see instructions)

Run locally:
1. python -m venv venv
2. source venv/bin/activate   # or venv\Scripts\activate on Windows
3. pip install -r requirements.txt
4. copy .env.example to .env and set SECRET_KEY
5. python init_admin.py
6. python app.py
7. Open http://127.0.0.1:5000

Deploy to Render:
- Push repo to GitHub
- Create Web Service on Render
- Build command: pip install -r requirements.txt
- Start command: gunicorn app:app
- Add env vars: DATABASE_URL, SECRET_KEY, optionally CLOUDINARY_URL
- After deploy, run init_admin.py via Render Shell to create admin

Default admin account (local): username=admin password=admin123
