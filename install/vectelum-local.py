#!/usr/bin/env python3
"""VECTELUM Local: installer and fixed-action URI launcher."""
import argparse, json, os, secrets, shutil, subprocess, sys, time, urllib.request, webbrowser
from pathlib import Path
IMAGE = "vectelum-os:83b41cd"
REVISION = "83b41cdbfc9274c2dc9864652bdbce9387dd9feb"
COMPATIBLE_IMAGES = {IMAGE, "vectelum-os:56350b3"}
REPO = "https://github.com/cyberzone51/vectelum-os.git"
URI = "vectelum://launch"
URL = "http://127.0.0.1:8080/home"
WINDOWS = os.name == "nt"
DOCKER = ["docker", "--host", "unix:///var/run/docker.sock"]
CORE = ["nomad_mysql", "nomad_redis", "nomad_admin"]
CONFIG = (Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "VECTELUM" if WINDOWS
          else Path.home()/".local/share/vectelum/launcher")
DATA = Path.home()/".local/share/vectelum/backend"

def run(args, **kw):
    return subprocess.run(args, check=True, **kw)

def docker(*args, **kw):
    return run([*DOCKER, *args], **kw)

def inspect(name):
    p = subprocess.run([*DOCKER,"inspect","--type","container",name], capture_output=True,text=True)
    return json.loads(p.stdout)[0] if p.returncode == 0 else None

def check_docker():
    docker("info","--format","{{.ServerVersion}}")
    docker("compose","version")

def healthy():
    try:
        with urllib.request.urlopen("http://127.0.0.1:8080/api/health",timeout=3) as r:
            return r.status == 200 and json.load(r).get("status") == "ok"
    except Exception:
        return False

def wait_ready():
    for _ in range(180):
        a = inspect("nomad_admin")
        if a and a["Config"]["Image"] in COMPATIBLE_IMAGES and a["State"].get("Health",{}).get("Status") == "healthy" and healthy():
            return
        time.sleep(2)
    raise RuntimeError("Backend did not become healthy. Inspect Docker logs; no data was removed.")

def start_backend():
    check_docker()
    a = inspect("nomad_admin")
    if not a or a["Config"]["Image"] not in COMPATIBLE_IMAGES:
        raise RuntimeError("Compatible VECTELUM backend not found. Use setup --fresh on a new host or follow migration guide.")
    u = inspect("nomad_updater")
    if u and u["State"]["Running"]:
        raise RuntimeError("Upstream updater running. Follow migration guide.")
    if not all(inspect(n) for n in CORE):
        raise RuntimeError("Missing existing core container.")
    for name in CORE:
        docker("start", name)
    wait_ready()

def fresh_backend():
    check_docker()
    if any(inspect(n) for n in CORE+["nomad_updater"]) or Path("/opt/project-nomad").exists() or DATA.exists():
        raise RuntimeError("Existing installation or setup directory detected. Refusing to overwrite anything.")
    if shutil.disk_usage(Path.home()).free < 30*1024**3:
        raise RuntimeError("At least 30 GiB free Linux filesystem space required.")
    DATA.mkdir(parents=True,mode=0o700)
    root = DATA.resolve()
    src = root/"source"
    run(["git","clone",REPO,str(src)])
    run(["git","-C",str(src),"checkout","--detach",REVISION])
    docker("build","--build-arg","VERSION=1.35.1-vectelum.2","--build-arg",f"VCS_REF={REVISION}","-t",IMAGE,str(src))
    for name in ("storage","mysql","redis"):
        (root/name).mkdir(mode=0o700)
    db, rootpass, key = [secrets.token_hex(32) for _ in range(3)]
    def hc(test):
        return {"test":test,"interval":"30s","timeout":"10s","retries":10}
    c = {"name":"project-nomad","services":{
      "admin":{"image":IMAGE,"pull_policy":"never","container_name":"nomad_admin","restart":"unless-stopped",
        "ports":["127.0.0.1:8080:8080"],"extra_hosts":["host.docker.internal:host-gateway"],
        "volumes":[str(root/"storage")+":/app/storage","/var/run/docker.sock:/var/run/docker.sock","nomad-update-shared:/app/update-shared"],
        "environment":{"NODE_ENV":"production","NOMAD_STORAGE_PATH":str(root/"storage"),"PORT":"8080","LOG_LEVEL":"info",
        "APP_KEY":key,"HOST":"0.0.0.0","URL":"http://127.0.0.1:8080","DB_HOST":"mysql","DB_PORT":"3306",
        "DB_DATABASE":"nomad","DB_USER":"nomad_user","DB_PASSWORD":db,"DB_NAME":"nomad","DB_SSL":"false",
        "REDIS_HOST":"redis","REDIS_PORT":"6379","DISABLE_COMPRESSION":"false"},
        "depends_on":{"mysql":{"condition":"service_healthy"},"redis":{"condition":"service_healthy"}},
        "healthcheck":hc(["CMD","curl","-f","http://localhost:8080/api/health"])},
      "mysql":{"image":"mysql:8.0","container_name":"nomad_mysql","restart":"unless-stopped",
        "environment":{"MYSQL_ROOT_PASSWORD":rootpass,"MYSQL_DATABASE":"nomad","MYSQL_USER":"nomad_user","MYSQL_PASSWORD":db},
        "volumes":[str(root/"mysql")+":/var/lib/mysql"],"healthcheck":hc(["CMD","mysqladmin","ping","-h","localhost"])},
      "redis":{"image":"redis:7-alpine","container_name":"nomad_redis","restart":"unless-stopped",
        "volumes":[str(root/"redis")+":/data"],"healthcheck":hc(["CMD","redis-cli","ping"])}
      },"volumes":{"nomad-update-shared":{}}}
    f=root/"compose.json"
    fd=os.open(f,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    with os.fdopen(fd,"w") as out:
        json.dump(c,out,indent=2)
    docker("compose","-f",str(f),"config","--quiet")
    docker("compose","-f",str(f),"up","-d","--pull","missing")
    wait_ready()

def backend(mode,distro):
    if WINDOWS:
        wsl=str(Path(os.environ.get("SystemRoot","C:/Windows"))/"System32/wsl.exe")
        run([wsl,"-d",distro,"--","python3","-",mode],input=Path(__file__).read_text(encoding="utf-8"),text=True,encoding="utf-8")
        subprocess.Popen([wsl,"-d",distro,"--","flock","-n","/tmp/vectelum-local-keepalive.lock","sleep","infinity"],
            stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,creationflags=subprocess.CREATE_NO_WINDOW)
    else:
        {"backend-start":start_backend,"backend-fresh":fresh_backend}[mode]()

def register(distro):
    CONFIG.mkdir(parents=True,exist_ok=True)
    target=CONFIG/"launcher.py"
    if Path(__file__).resolve()!=target.resolve():
        shutil.copy2(__file__,target)
    (CONFIG/"config.json").write_text(json.dumps({"distro":distro}),encoding="utf-8")
    if WINDOWS:
        import winreg
        key=r"Software\Classes\vectelum"
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER,key) as k:
            winreg.SetValueEx(k,"",0,winreg.REG_SZ,"URL:VECTELUM Local")
            winreg.SetValueEx(k,"URL Protocol",0,winreg.REG_SZ,"")
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER,key+r"\shell\open\command") as k:
            winreg.SetValueEx(k,"",0,winreg.REG_SZ,f'"{sys.executable}" "{target}" "%1"')
        programs=Path(os.environ["APPDATA"])/"Microsoft/Windows/Start Menu/Programs"
        programs.mkdir(parents=True,exist_ok=True)
        (programs/"VECTELUM Local.cmd").write_text(f'@echo off\n"{sys.executable}" "{target}" "{URI}"\n',encoding="utf-8")
    else:
        def quote(s):
            return '"'+str(s).replace("\\","\\\\").replace('"','\\"').replace("$","\\$").replace(chr(96),"\\"+chr(96)).replace("%","%%")+'"'
        desktop=Path.home()/".local/share/applications/vectelum-local.desktop"
        desktop.parent.mkdir(parents=True,exist_ok=True)
        desktop.write_text("[Desktop Entry]\nType=Application\nName=VECTELUM Local\nTerminal=true\n"+"Exec="+quote(sys.executable)+" "+quote(target)+" %u\nMimeType=x-scheme-handler/vectelum;\nCategories=Utility;\n",encoding="utf-8")
        run(["xdg-mime","default",desktop.name,"x-scheme-handler/vectelum"])
    print("Registered vectelum://launch for this user.",flush=True)

def launch(distro):
    backend("backend-start",distro)
    if not healthy():
        raise RuntimeError("Local desktop cannot reach backend. Check localhost forwarding.")
    webbrowser.open(URL)

def main():
    if sys.argv[1:]==[URI]:
        launch(json.loads((CONFIG/"config.json").read_text(encoding="utf-8"))["distro"])
        return
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("action",choices=["setup","launch","backend-start","backend-fresh"])
    p.add_argument("--fresh",action="store_true")
    p.add_argument("--distro",default="Ubuntu-24.04")
    a=p.parse_args()
    if a.action in ("backend-start","backend-fresh"):
        if WINDOWS: raise RuntimeError("Backend requires Linux.")
        (start_backend if a.action=="backend-start" else fresh_backend)()
    elif a.action=="setup":
        print("Developer preview: use only on a trusted local computer.",flush=True)
        backend("backend-fresh" if a.fresh else "backend-start",a.distro)
        if not healthy(): raise RuntimeError("Local backend unreachable.")
        register(a.distro)
        webbrowser.open(URL)
    else:
        launch(json.loads((CONFIG/"config.json").read_text(encoding="utf-8"))["distro"])

if __name__=="__main__":
    try:
        main()
    except Exception as e:
        print("VECTELUM: "+str(e),file=sys.stderr,flush=True)
        if WINDOWS and sys.argv[1:]==[URI]:
            input("Press Enter to close.")
        sys.exit(1)
