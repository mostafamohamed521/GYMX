# ============================================================
# PythonAnywhere WSGI configuration file
#
# HOW TO USE:
# On PythonAnywhere, go to the "Web" tab → click the link under
# "Code" → "WSGI configuration file" (looks like
# /var/www/<yourusername>_pythonanywhere_com_wsgi.py).
# DELETE everything in that file and paste this in instead.
# Replace YOURUSERNAME (2 places below) with your actual
# PythonAnywhere username, then hit Reload on the Web tab.
#
# Note: this file is NOT the same as apps' config/wsgi.py in the
# project — PythonAnywhere ignores that one and uses this instead.
# ============================================================

import os
import sys

# Path to the folder that contains manage.py
path = '/home/YOURUSERNAME/gymx'
if path not in sys.path:
    sys.path.insert(0, path)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# python-decouple reads /home/YOURUSERNAME/gymx/.env automatically as long
# as the working directory is right, which PythonAnywhere sets up for you
# via the path above — no extra os.environ[...] lines needed here.

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
