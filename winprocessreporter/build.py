import PyInstaller.__main__
from pathlib import Path

HERE = Path(__file__).parent.absolute()
path_to_main = str(HERE / "main.py")
path_icon = str(HERE / "icon.ico")

def install():
    PyInstaller.__main__.run([
        path_to_main,
        '--onefile',
        '--windowed',
        '--uac-admin',
        '--icon', path_icon,
        '--name', 'WinProcessReporter',
        '--add-data', f'{HERE / "icon.png"};.'
    ])
