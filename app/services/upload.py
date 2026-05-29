import os
import uuid
from werkzeug.utils import secure_filename
from flask import current_app

def save_upload(file, subfolder=''):
    """
    Saves a file to the upload directory.
    Returns the relative path (starting with /static/uploads/).
    """
    if not file or file.filename == '':
        return None
        
    filename = secure_filename(file.filename)
    unique_filename = f"{uuid.uuid4()}_{filename}"
    
    # Use config value for upload folder
    base_upload_path = current_app.config['UPLOAD_FOLDER']
    target_dir = os.path.join(base_upload_path, subfolder)
    
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)
        
    file.save(os.path.join(target_dir, unique_filename))
    
    # Return path relative to static
    rel_path = f"/static/uploads/{subfolder + '/' if subfolder else ''}{unique_filename}"
    return rel_path
