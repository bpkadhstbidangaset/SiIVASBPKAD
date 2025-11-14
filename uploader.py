import os
from urllib.parse import urlparse
import cloudinary.uploader

def is_cloudinary_configured():
    return bool(os.getenv('CLOUDINARY_URL'))

def upload_file_local(file, upload_folder, prefix=''):
    filename = prefix + secure_filename(file.filename)
    path = os.path.join(upload_folder, filename)
    file.save(path)
    return path

def upload_file(file, upload_folder, prefix=''):
    # Decide between local or cloudinary
    if not file:
        return None
    if is_cloudinary_configured():
        # upload to cloudinary
        res = cloudinary.uploader.upload(file,
                                        folder='si_ivas',
                                        public_id=(prefix + os.path.splitext(file.filename)[0]))
        return res.get('secure_url')
    else:
        # local
        from werkzeug.utils import secure_filename
        filename = prefix + secure_filename(file.filename)
        path = os.path.join(upload_folder, filename)
        file.save(path)
        return path
