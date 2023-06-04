import datetime
import os
import uuid


def filepath(instance, filename):  # File Path for your uploaded media
    name, extension = os.path.splitext(filename)
    filename = f"{uuid.uuid4()}{extension}"
    return os.path.join(f"{instance.get_folder_name}/{filename}")
