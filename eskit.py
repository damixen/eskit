#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
import paramiko
import getpass

DEFAULT_CONFIG = "config.json"
CACHE_ROOT = Path(".eskit")

def load_config(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def get_host(config, name):
    for h in config.get("hosts", []):
        if h["name"] == name:
            return h
    raise SystemExit(f"Host not found: {name}")

def check_host(host):
    if host is None:
        raise SystemExit("Host not found. Please specify host or set host.")
    return;

def get_current_host():
    with open(CACHE_ROOT / f".current_host", "r", encoding="utf-8") as f:
        for line in f:
           return line

def set_current_host(host):
    with open(CACHE_ROOT / f".current_host", "w", encoding="utf-8") as f:
        f.write(host)

def cache_dir(host):
    return CACHE_ROOT / host / "cache"

def ensure_cache(host):
    cache_dir(host).mkdir(parents=True, exist_ok=True)

def write_cache(host, name, data):
    ensure_cache(host)
    with open(cache_dir(host) / f"{name}.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def read_cache(host, name):
    p = cache_dir(host) / f"{name}.json"
    if not p.exists():
        print(f"No cached {name} information found. Run: eskit pull {host}")
        return None
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)

def is_agent_available():
    try:
        agent = paramiko.Agent()
        return len(agent.get_keys()) > 0
    except Exception:
        return False

def load_private_key(key_path, passphrase=None):
    try:
        return paramiko.Ed25519Key.from_private_key_file(key_path, password=passphrase)
    except paramiko.PasswordRequiredException:
        # fallback to prompt if not provided
        passphrase = getpass.getpass(f"Passphrase for {key_path}: ")
        return paramiko.Ed25519Key.from_private_key_file(key_path, password=passphrase)

class SSHConnection:
    def __init__(self, host_cfg):
        self.host_cfg = host_cfg
        self.client = None

    def connect(self):
        ssh = self.host_cfg["ssh"]
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        kwargs = {
            "hostname": self.host_cfg["ip"],
            "port": ssh.get("port", 22),
            "username": ssh["user"]
        }
       
        if ssh.get("password"):
            kwargs["allow_agent"] = False
            kwargs["password"] = ssh["password"]
        if ssh.get("identity"):
            key_filename = ssh["identity"]
            kwargs["key_filename"] = key_filename
            kwargs["look_for_keys"] = True
            allow_agent = True
            if "use_agent" in ssh and not ssh["use_agent"]:
                allow_agent=False
            elif not is_agent_available():
                allow_agent=False
            
            if not allow_agent:
                passphrase = ssh.get("passphrase")
                kwargs["pkey"]=load_private_key(key_filename, passphrase) if key_filename else None
             # Try to use agent by default unless disabled in the config

        self.client.connect(**kwargs)

    def run(self, cmd):
        _, stdout, stderr = self.client.exec_command(cmd)
        out = stdout.read().decode()
        err = stderr.read().decode()
        if err.strip():
            raise RuntimeError(err)
        return out

    def close(self):
        if self.client:
            self.client.close()

class ESClient:
    def __init__(self, transport, config):
        self.transport = transport
        self.config = config

    def request(self, method, path, body=None):
        port = 9200
        if "port" in self.config:
            port = self.config["port"]
        cmd = f"curl -s -X {method.upper()} 'http://localhost:{port}{path}'"
        if body is not None:
            payload = json.dumps(body).replace("'", "'\"'\"'")
            cmd += f" -H 'Content-Type: application/json' -d '{payload}'"
        print("elastic_config", self.config)
        if "user" in self.config:
            cmd += f" -u {self.config["user"]["name"]}:{self.config["user"]["password"]}"
            pass
        print("cmd:", cmd)
        result = self.transport.run(cmd)
        try:
            return json.loads(result)
        except Exception:
            return result

def pull_host(host_name, es):

    if host_name is None:
        host_name = get_current_host()

    if host_name is None:
        print("Please specify host or set host")
        return

    repos = es.request("GET", "/_snapshot")
    write_cache(host_name, "repos", repos)

    snapshots = {}
    if isinstance(repos, dict):
        for repo in repos.keys():
            snapshots[repo] = es.request("GET", f"/_snapshot/{repo}/_all")
    write_cache(host_name, "snapshots", snapshots)

    indices = es.request("GET", "/_cat/indices?format=json")
    write_cache(host_name, "indices", indices)
    print("Cache updated.")

def connect_es(config, host_name):

    if host_name is None:
        host_name = get_current_host()

    check_host(host_name)

    host_cfg = get_host(config, host_name)
    ssh = SSHConnection(host_cfg)
    ssh.connect()
    elastic_config = {}
    if "elastic" in host_cfg:
        elastic_config = host_cfg["elastic"]
    return ssh, ESClient(ssh, elastic_config)

def cmd_host(config):
    for h in config.get("hosts", []):
        print(h["name"])

def cmd_host_set(host):
    set_current_host(host)

def cmd_host_get():
    print(get_current_host())

def cmd_pull(config, host_name):

    if host_name is None:
        host_name = get_current_host()

    check_host(host_name)

    ssh, es = connect_es(config, host_name)
    try:
        pull_host(host_name, es)
    finally:
        ssh.close()

def cmd_cat2(kind, host_name):

    if host_name is None:
        host_name = get_current_host()

    check_host(host_name)

    data = read_cache(host_name, kind)
    out = {}
    if kind == "snapshots":
        for repo, repo_data in data.items():
            #print(f"Repo: {repo} | Value: {repo_data}")
            snapshots = repo_data.get("snapshots",{})
            list = []
            for s in snapshots:
                list.append(s["snapshot"])
            out[repo] = {}
            out[repo]["snapshots"] = list;
        pass
    elif kind == "repos":
        out = data
        pass
    elif kind == "indices":
        out = []
        for i in data:
            index = {}
            index["index"]=i["index"];
            out.append(index)
        out.sort(key=lambda x: x["index"])
        pass
    elif kind == "recovery":
        out = data
    print(json.dumps(out, indent=2))

    
def cmd_cat(kind, host_name):

    if host_name is None:
        host_name = get_current_host()

    check_host(host_name)

    data = read_cache(host_name, kind)
    if data is not None:
        print(json.dumps(data, indent=2))

def cmd_repo_show2(host_name, path):

    if host_name is None:
        host_name = get_current_host()

    check_host(host_name)
    repo, sep, snap= path.partition("/")
    if repo and snap:
        cmd_snap_show(host_name, path)
    else:
        cmd_repo_show(host_name, repo)

def cmd_repo_show(host_name, repo):

    if host_name is None:
        host_name = get_current_host()

    check_host(host_name)

    data = read_cache(host_name, "repos")
    if not data:
        return;

    out={}

    repo_data = data.get(repo, {})
    if not repo_data:
        return;

    out[repo] = repo_data

    snapshots = read_cache(host_name, "snapshots")
    
    if not snapshots:
        print(json.dumps(data.get(repo, {}), indent=2))
        return
    
    snapshots = snapshots.get(repo,{}).get("snapshots",{})
    list = []
    for s in snapshots:
        list.append(s["snapshot"])

    out[repo]["snapshots"] = list;
    print(json.dumps(out, indent=2))

def cmd_snap_show(host_name, spec):

    if host_name is None:
        host_name = get_current_host()

    check_host(host_name)

    repo, snap = spec.split("/", 1)
    data = read_cache(host_name, "snapshots")
    if not data:
        return
    for s in data.get(repo, {}).get("snapshots", []):
        if s.get("snapshot") == snap:
            print(json.dumps(s, indent=2))
            return
    print("Snapshot not found.")

def cat_recovery(config, host):
    if host is None:
        host = get_current_host()

    check_host(host)

    ssh, es = connect_es(config, host)
    try:
        out = []
        data = es.request("GET", f"/_cat/recovery?format=json")
        for r in data:
            info = {}
            info["index"] = r["index"]
            info["files_percent"] = r["files_percent"]
            out.append(info)
        out.sort(key=lambda x: x["index"])
        print(json.dumps(out, indent=2))
    finally:
        ssh.close()

def create_repo(config, host, name, repo_type, location, dry_run):

    if host is None:
        host = get_current_host()

    check_host(host)

    body = {"type": repo_type, "settings": {"location": location}}
    if dry_run:
        print(f"HOST:{host}")
        print("PUT", f"/_snapshot/{name}")
        print(json.dumps(body, indent=2))
        return
    ssh, es = connect_es(config, host)
    try:
        es.request("PUT", f"/_snapshot/{name}", body)
        pull_host(host, es)
    finally:
        ssh.close()

def delete_repo(config, host, name, dry_run):

    if host is None:
        host = get_current_host()

    check_host(host)

    if dry_run:
        print(f"HOST:{host}")
        print("DELETE", f"/_snapshot/{name}")
        return
    ssh, es = connect_es(config, host)
    try:
        es.request("DELETE", f"/_snapshot/{name}")
        pull_host(host, es)
    finally:
        ssh.close()

def create_snapshot(config, host, spec, indices, include_global_state, ignore_unavailable, dry_run):

    if host is None:
        host = get_current_host()

    check_host(host)

    repo, snap = spec.split("/", 1)
    body = {}
    if indices:
        body["indices"] = indices
    body["include_global_state"] = include_global_state
    body["ignore_unavailable"] = ignore_unavailable
    if dry_run:
        print(f"HOST:{host}")
        print("PUT", f"/_snapshot/{repo}/{snap}")
        print(json.dumps(body, indent=2))
        return
    ssh, es = connect_es(config, host)
    try:
        es.request("PUT", f"/_snapshot/{repo}/{snap}", body)
        pull_host(host, es)
    finally:
        ssh.close()

def delete_snapshot(config, host, spec, dry_run):
    repo, snap = spec.split("/", 1)
    if host is None:
        host = get_current_host()

    check_host(host)

    if dry_run:
        print(f"HOST:{host}")
        print("DELETE", f"/_snapshot/{repo}/{snap}")
        return
    ssh, es = connect_es(config, host)
    try:
        es.request("DELETE", f"/_snapshot/{repo}/{snap}")
        pull_host(host, es)
    finally:
        ssh.close()

def restore_snapshot(config, host, spec, dry_run):
    repo, snap = spec.split("/", 1)
    if host is None:
        host = get_current_host()

    check_host(host)

    body = {}
    body["indices"] = "*"
    body["include_global_state"] = False
    
    if dry_run:
        print(f"HOST:{host}")
        print("POST", f"/_snapshot/{repo}/{snap}/_restore")
        print(json.dumps(body, indent=2))
        return
    ssh, es = connect_es(config, host)
    try:
        es.request("POST", f"/_snapshot/{repo}/{snap}/_restore",body)
    finally:
        ssh.close()

def build_parser():
    p = argparse.ArgumentParser(prog="eskit")
    p.add_argument("--config", default=DEFAULT_CONFIG)
    p.add_argument("--dry-run", action="store_true")

    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("host")

    host_set = sub.add_parser("host-set")
    host_set.add_argument("host")

    sub.add_parser("host-get")

    pull = sub.add_parser("pull")
    pull.add_argument("--host")

    cat = sub.add_parser("cat")
    cat.add_argument("kind", choices=["repo", "snap", "index"])
    cat.add_argument("--host")

    repo = sub.add_parser("repo-show")
    repo.add_argument("--host")
    repo.add_argument("repo")

    repo_create = sub.add_parser("repo-create")
    repo_create.add_argument("--host")
    repo_create.add_argument("repo")
    repo_create.add_argument("--type", default="fs")
    repo_create.add_argument("--location", required=True)

    repo_delete = sub.add_parser("repo-delete")
    repo_delete.add_argument("--host")
    repo_delete.add_argument("repo")

    snap_create = sub.add_parser("snap-create")
    snap_create.add_argument("--host")
    snap_create.add_argument("snapshot")
    snap_create.add_argument("--index")
    snap_create.add_argument("--include_global-state", default=False)
    snap_create.add_argument("--ignore_unavailable", default=True)

    snap_delete = sub.add_parser("snap-delete")
    snap_delete.add_argument("--host")
    snap_delete.add_argument("snapshot")

    snap_restore = sub.add_parser("snap-restore")
    snap_restore.add_argument("--host")
    snap_restore.add_argument("snapshot")

    snap_restore_check = sub.add_parser("snap-restore-check")
    snap_restore_check.add_argument("--host")

    return p

def main():
    args = build_parser().parse_args()
    config = load_config(args.config)

    if args.cmd == "host":
        cmd_host(config)
    elif args.cmd == "host-set":
        cmd_host_set(args.host)
    elif args.cmd == "host-get":
        cmd_host_get()
    elif args.cmd == "pull":
        cmd_pull(config, args.host)
    elif args.cmd == "cat":
        mapping = {"repo":"repos","snap":"snapshots","index":"indices"}
        cmd_cat2(mapping[args.kind], args.host)
    elif args.cmd == "repo-show":
        cmd_repo_show2(args.host, args.repo)
    elif args.cmd == "repo-create":
        create_repo(config, args.host, args.repo, args.type, args.location, args.dry_run)
    elif args.cmd == "repo-delete":
        delete_repo(config, args.host, args.repo, args.dry_run)
    elif args.cmd == "snap-show":
        cmd_snap_show(args.host, args.snapshot)
    elif args.cmd == "snap-create":
        create_snapshot(config, args.host, args.snapshot, args.index, args.include_global_state,args.ignore_unavailable, args.dry_run)
    elif args.cmd == "snap-delete":
        delete_snapshot(config, args.host, args.snapshot, args.dry_run)
    elif args.cmd == "snap-restore":
        restore_snapshot(config, args.host, args.snapshot, args.dry_run)
    elif args.cmd == "snap-restore-check":
        cat_recovery(config, args.host)

if __name__ == "__main__":
    main()
