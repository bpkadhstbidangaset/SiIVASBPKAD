import os, io, csv
from flask import Flask, render_template, request, redirect, session, url_for, flash, send_from_directory, Response
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from models import db, User, Kendaraan
from uploader import upload_file, is_cloudinary_configured
import pandas as pd

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'rahasia-sementara')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///data.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

UPLOAD_FOLDER = os.path.join('static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

ALLOWED_EXT = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXT

db.init_app(app)
with app.app_context():
    db.create_all()

# -------------------------
# AUTH
# -------------------------
@app.route('/', methods=['GET','POST'])
@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['role'] = user.role
            session['nama_skpd'] = user.nama_skpd
            flash('Login berhasil', 'success')
            if user.role == 'admin':
                return redirect('/admin')
            return redirect('/skpd')
        flash('Username atau password salah', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

# -------------------------
# ADMIN
# -------------------------
@app.route('/admin')
def admin_dashboard():
    if session.get('role') != 'admin':
        return redirect('/login')
    total_kendaraan = Kendaraan.query.count()
    total_skpd = User.query.filter_by(role='skpd').count()
    return render_template('admin/dashboard.html', total_kendaraan=total_kendaraan, total_skpd=total_skpd)

@app.route('/admin/skpd', methods=['GET','POST'])
def admin_skpd_list():
    if session.get('role') != 'admin':
        return redirect('/login')
    if request.method == 'POST':
        nama = request.form.get('nama_skpd')
        username = request.form.get('username')
        password = request.form.get('password')
        if not (nama and username and password):
            flash('Lengkapi semua field', 'danger')
            return redirect('/admin/skpd')
        if User.query.filter_by(username=username).first():
            flash('Username sudah ada', 'danger')
            return redirect('/admin/skpd')
        u = User(nama_skpd=nama, username=username, role='skpd')
        u.set_password(password)
        db.session.add(u)
        db.session.commit()
        flash('SKPD berhasil ditambahkan', 'success')
        return redirect('/admin/skpd')
    users = User.query.filter_by(role='skpd').all()
    return render_template('admin/skpd_list.html', users=users)

@app.route('/admin/skpd/delete/<int:id>', methods=['POST'])
def admin_skpd_delete(id):
    if session.get('role') != 'admin':
        return redirect('/login')
    u = User.query.get_or_404(id)
    # do not delete admin
    if u.role == 'admin':
        flash('Tidak dapat menghapus admin', 'danger')
        return redirect('/admin/skpd')
    # delete related kendaraan and files
    for k in u.kendaraan:
        for f in [k.foto_depan, k.foto_belakang, k.foto_bpkb, k.foto_stnk]:
            try:
                if f and not is_cloudinary_configured() and os.path.exists(f):
                    os.remove(f)
            except:
                pass
    db.session.delete(u)
    db.session.commit()
    flash('SKPD dihapus', 'success')
    return redirect('/admin/skpd')

@app.route('/admin/kendaraan')
def admin_kendaraan_list():
    if session.get('role') != 'admin':
        return redirect('/login')
    data = Kendaraan.query.all()
    return render_template('admin/kendaraan_list.html', data=data)

@app.route('/admin/export_csv')
def admin_export_csv():
    if session.get('role') != 'admin':
        return redirect('/login')
    data = Kendaraan.query.join(User, Kendaraan.skpd_id==User.id).add_columns(
        Kendaraan.id, User.nama_skpd, Kendaraan.nomor_polisi, Kendaraan.merek,
        Kendaraan.model, Kendaraan.tahun, Kendaraan.pengguna, Kendaraan.warna, Kendaraan.cc, Kendaraan.kode_barang
    ).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['id','skpd','nomor_polisi','merek','model','tahun','pengguna','warna','cc','kode_barang'])
    for row in data:
        writer.writerow([row.id, row.nama_skpd, row.nomor_polisi, row.merek, row.model, row.tahun, row.pengguna, row.warna, row.cc, row.kode_barang])
    output.seek(0)
    return Response(output, mimetype='text/csv', headers={"Content-Disposition":"attachment;filename=kendaraan_all.csv"})

# -------------------------
# SKPD
# -------------------------
@app.route('/skpd')
def skpd_dashboard():
    if session.get('role') != 'skpd':
        return redirect('/login')
    data = Kendaraan.query.filter_by(skpd_id=session['user_id']).all()
    return render_template('skpd/dashboard.html', data=data)

@app.route('/skpd/tambah', methods=['GET','POST'])
def skpd_tambah():
    if session.get('role') != 'skpd':
        return redirect('/login')
    if request.method == 'POST':
        def save_field(name):
            f = request.files.get(name)
            if not f or f.filename=='':
                return None
            if not allowed_file(f.filename):
                return None
            return upload_file(f, app.config['UPLOAD_FOLDER'], prefix=str(session['user_id'])+'_')
        k = Kendaraan(
            skpd_id=session['user_id'],
            nomor_polisi=request.form.get('nomor_polisi'),
            merek=request.form.get('merek'),
            model=request.form.get('model'),
            tahun=int(request.form.get('tahun')) if request.form.get('tahun') else None,
            pengguna=request.form.get('pengguna'),
            warna=request.form.get('warna'),
            cc=int(request.form.get('cc')) if request.form.get('cc') else None,
            kode_barang=request.form.get('kode_barang'),
            foto_depan=save_field('foto_depan'),
            foto_belakang=save_field('foto_belakang'),
            foto_bpkb=save_field('foto_bpkb'),
            foto_stnk=save_field('foto_stnk')
        )
        db.session.add(k)
        db.session.commit()
        flash('Data kendaraan ditambahkan', 'success')
        return redirect('/skpd')
    return render_template('skpd/form_kendaraan.html', k=None)

@app.route('/skpd/edit/<int:id>', methods=['GET','POST'])
def skpd_edit(id):
    if session.get('role') not in ('skpd','admin'):
        return redirect('/login')
    k = Kendaraan.query.get_or_404(id)
    if session.get('role')=='skpd' and k.skpd_id != session['user_id']:
        flash('Tidak memiliki izin', 'danger')
        return redirect('/skpd')
    if request.method == 'POST':
        def save_field(name, old):
            f = request.files.get(name)
            if not f or f.filename=='':
                return old
            if not allowed_file(f.filename):
                return old
            newpath = upload_file(f, app.config['UPLOAD_FOLDER'], prefix=str(session['user_id'])+'_')
            # remove old if local
            try:
                if old and not is_cloudinary_configured() and os.path.exists(old):
                    os.remove(old)
            except:
                pass
            return newpath
        k.nomor_polisi = request.form.get('nomor_polisi')
        k.merek = request.form.get('merek')
        k.model = request.form.get('model')
        k.tahun = int(request.form.get('tahun')) if request.form.get('tahun') else None
        k.pengguna = request.form.get('pengguna')
        k.warna = request.form.get('warna')
        k.cc = int(request.form.get('cc')) if request.form.get('cc') else None
        k.kode_barang = request.form.get('kode_barang')
        k.foto_depan = save_field('foto_depan', k.foto_depan)
        k.foto_belakang = save_field('foto_belakang', k.foto_belakang)
        k.foto_bpkb = save_field('foto_bpkb', k.foto_bpkb)
        k.foto_stnk = save_field('foto_stnk', k.foto_stnk)
        db.session.commit()
        flash('Data kendaraan diupdate', 'success')
        if session.get('role')=='admin':
            return redirect('/admin/kendaraan')
        return redirect('/skpd')
    return render_template('skpd/form_kendaraan.html', k=k)

@app.route('/skpd/delete/<int:id>', methods=['POST'])
def skpd_delete(id):
    if session.get('role') not in ('skpd','admin'):
        return redirect('/login')
    k = Kendaraan.query.get_or_404(id)
    if session.get('role')=='skpd' and k.skpd_id != session['user_id']:
        flash('Tidak memiliki izin', 'danger')
        return redirect('/skpd')
    for f in [k.foto_depan, k.foto_belakang, k.foto_bpkb, k.foto_stnk]:
        try:
            if f and not is_cloudinary_configured() and os.path.exists(f):
                os.remove(f)
        except:
            pass
    db.session.delete(k)
    db.session.commit()
    flash('Data kendaraan dihapus', 'success')
    if session.get('role')=='admin':
        return redirect('/admin/kendaraan')
    return redirect('/skpd')

# serve uploads
@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=10000)
