   import sys
   import logging

   # Add your project directory to the sys.path
   sys.path.insert(0, '//home/saif-deshmuih/Desktop/deshmukh_lab')

   from app import app as application  # Adjust the import based on your app structure

   # Optional: Set up logging
   logging.basicConfig(stream=sys.stderr)
   sys.stderr = open('/var/log/myapp/error.log', 'a+')
