
Cubist GUI v2 - Instructions
-----------------------------

1. Launch `cubist_gui.py` using Python 3.10+ with tkinter installed.

2. GUI Features:
   - Browse input image and output folder.
   - Set number of points and alpha clipping.
   - Auto-saves last used inputs in 'last_session_config.json'.
   - Output file includes zero-padded point count.
   - Click 'View Output' to open the image in default viewer.

3. To package as an executable:
   - Install pyinstaller: pip install pyinstaller
   - Run: pyinstaller --onefile cubist_gui.py
   - Output will be in the `dist/` directory.

