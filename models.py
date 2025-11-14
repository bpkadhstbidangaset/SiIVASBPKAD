from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nama_skpd = db.Column(db.String(200), nullable=False)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='skpd')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Kendaraan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    skpd_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    nomor_polisi = db.Column(db.String(50), nullable=False)
    merek = db.Column(db.String(100))
    model = db.Column(db.String(100))
    tahun = db.Column(db.Integer)
    pengguna = db.Column(db.String(150))
    warna = db.Column(db.String(50))
    cc = db.Column(db.Integer)
    kode_barang = db.Column(db.String(100))

    foto_depan = db.Column(db.String(500))
    foto_belakang = db.Column(db.String(500))
    foto_bpkb = db.Column(db.String(500))
    foto_stnk = db.Column(db.String(500))

    owner = db.relationship('User', backref='kendaraan')
