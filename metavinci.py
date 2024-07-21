from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QGridLayout, QWidget, QCheckBox, QSystemTrayIcon, QSpacerItem, QSizePolicy, QMenu, QAction, QStyle, qApp
from PyQt5.QtCore import QSize
from PyQt5.QtGui import QIcon
from pathlib import Path
import subprocess
import os
import stat
from tinydb import TinyDB, Query
from gradientmessagebox import *
import click
import getpass
import shutil

HOME = os.path.expanduser('~')
FILE_PATH = Path(__file__).parent
CWD = Path.cwd()
SERVICE_RUN_DEST = CWD / '.metavinci'
SERVICE_RUN_FILE = os.path.join(HOME, '.metavinci', 'run.sh')
SERVICE_START = os.path.join(FILE_PATH, 'service', 'start.sh')
SERVICE_RUN = os.path.join(FILE_PATH, 'service', 'run.sh')
APP_ICON_FILE = os.path.join(HOME, '.metavinci', 'app_icon.png')
APP_ICON = os.path.join(FILE_PATH, 'images', 'app_icon.png')
DB_PATH = os.path.join(FILE_PATH, 'data', 'db.json')
FG_TXT_COLOR = '#98314a'

def _config_popup(popup):
      popup.fg_luminance(0.8)
      popup.bg_saturation(0.6)
      popup.bg_luminance(0.4)
      popup.custom_msg_color(FG_TXT_COLOR)

def _choice_popup(msg):
      """ Show choice popup, message based on passed msg arg."""
      popup = PresetChoiceWindow(msg)
      _config_popup(popup)
      result = popup.Ask()
      return result.response

def _ssh_install(script,  *args):
    # run your shell script using subprocess
    p = subprocess.Popen([script, *args], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate()

    output = out.decode('utf-8')
    # Split the output into lines
    lines = output.splitlines()

    # Extract the last 10 lines (you can change this to 20 if desired)
    last_line = lines[-1:]

    # Print the output of the subprocess call
    print('------------------------------------------------------')
    print(output)
    print(last_line)
    print(p.returncode)
    print('------------------------------------------------------')
    return output

def _install_runner():
    if not os.path.isfile(str(SERVICE_RUN_FILE)):
        shutil.copy(str(SERVICE_RUN), SERVICE_RUN_DEST)
        r = os.stat(SERVICE_RUN_FILE)
        os.chmod(SERVICE_RUN_FILE, r.st_mode | stat.S_IEXEC)

def _install_icon():
    if not os.path.isfile(str(APP_ICON_FILE)):
        shutil.copy(str(APP_ICON), SERVICE_RUN_DEST)
    
     
class Metavinci(QMainWindow):
    """
        Network Daemon for Heavymeta
    """
    check_box = None
    tray_icon = None
    
    # Override the class constructor
    def __init__(self):
        # Be sure to call the super class method
        QMainWindow.__init__(self)
        self.HOME = os.path.expanduser('~')
        self.HVYM = os.path.join(self.HOME, '.local', 'share', 'heavymeta-cli', 'hvym')
        self.FILE_PATH = Path(__file__).parent
        self.LOGO_IMG = os.path.join(self.FILE_PATH, 'images', 'hvym_logo_64.png')
        self.ICP_LOGO_IMG = os.path.join(self.FILE_PATH, 'images', 'icp_logo.png')
        self.icon = QIcon(self.LOGO_IMG)
        self.ic_icon = QIcon(self.ICP_LOGO_IMG)
     
        self.setMinimumSize(QSize(480, 80))             # Set sizes
        self.setWindowTitle("Metavinci")  # Set a title
        central_widget = QWidget(self)                  # Create a central widget
        self.setCentralWidget(central_widget)           # Set the central widget
     
        grid_layout = QGridLayout(self)         # Create a QGridLayout
        central_widget.setLayout(grid_layout)   # Set the layout into the central widget
        grid_layout.addWidget(QLabel("Application, which can minimize to Tray", self), 0, 0)
     
        # Add a checkbox, which will depend on the behavior of the program when the window is closed
        self.check_box = QCheckBox('Minimize to Tray')
        grid_layout.addWidget(self.check_box, 1, 0)
        grid_layout.addItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Expanding), 2, 0)
    
        # Init QSystemTrayIcon
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(self.icon)
     
        '''
            Define and add steps to work with the system tray icon
            show - show window
            hide - hide window
            exit - exit from application
        '''
        #show_action = QAction("Show", self)
        icp_new_account_action = QAction(self.ic_icon, "New Account", self)
        icp_change_account_action = QAction(self.ic_icon, "Change Account", self)
        quit_action = QAction("Exit", self)
        icp_new_account_action.triggered.connect(self.new_ic_account)
        icp_change_account_action.triggered.connect(self.change_ic_account)
        quit_action.triggered.connect(qApp.quit)
        tray_menu = QMenu()
        tray_menu.addAction(icp_new_account_action)
        tray_menu.addAction(icp_change_account_action)
        tray_menu.addAction(quit_action)
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()
        self._installation_check()
     
    # Override closeEvent, to intercept the window closing event
    # The window will be closed only if there is no check mark in the check box
    def closeEvent(self, event):
        if self.check_box.isChecked():
            event.ignore()
            self.hide()
            self.tray_icon.showMessage(
                "Tray Program",
                "Application was minimized to Tray",
                QSystemTrayIcon.Information,
                2000
            )
    def new_ic_account(self):
        return(self._subprocess(f'{self.HVYM} icp-new-account'))

    def change_ic_account(self):
        return(self._subprocess(f'{self.HVYM} icp-set-account'))

    def hvym_check(self):
        return(self._subprocess(f'{self.HVYM} check'))

    def _installation_check(self):
        if not os.path.isfile(self.HVYM):
            print('Install the cli')
        else:
            print('hvym is installed')
            if self.hvym_check().strip() == 'ONE-TWO':
                print('hvym is on path')
                self._subprocess('hvym splash')
            else:
                self._install_hvym()

    def _install_hvym(self):
        self._subprocess('curl -L https://github.com/inviti8/hvym/raw/main/install.sh | bash')
        if self.hvym_check().strip() == 'ONE-TWO':
            print('hvym is on path')
            self._subprocess('hvym splash')
        else:
            print('hvym not installed.')

    def _subprocess(self, command):
        try:
            output = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT)
            return output.decode('utf-8')
        except Exception as e:
            return "Command failed with error: "+str(e)
         

@click.command()
def up():
    import sys
    app = QApplication(sys.argv)
    mw = Metavinci()
    #mw.show()
    sys.exit(app.exec())
    click.echo("Metavinci up")

@click.command()
def start():
    self._subprocess('sudo systemctl start metavinci')

@click.command()
def stop():
    self._subprocess('sudo systemctl stop metavinci')

if __name__ == "__main__":
    if not os.path.isfile(str(APP_ICON_FILE)):
        click.echo('Metavinci needs permission to start a system service:')
        st = os.stat(SERVICE_START)
        os.chmod(SERVICE_START, st.st_mode | stat.S_IEXEC)
        _install_icon()
        STORAGE.insert({'INITIALIZED': True})
        metavinci = str(SERVICE_RUN_DEST)
        cmd = f'sudo {SERVICE_START} {getpass.getuser()} "{metavinci}"'
        output = subprocess.check_output(f'sudo {SERVICE_START} {getpass.getuser()} "{metavinci}"', shell=True, stderr=subprocess.STDOUT)
        click.echo(output.decode('utf-8'))

    up()

