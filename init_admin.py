from models import db, User
from app import app

with app.app_context():
    username = 'admin'
    if not User.query.filter_by(username=username).first():
        u = User(nama_skpd='Si IVAS - Admin', username=username, role='admin')
        u.set_password('admin123')
        db.session.add(u)
        db.session.commit()
        print('Admin dibuat: username=admin password=admin123')
    else:
        print('Admin sudah ada')
