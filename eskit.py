#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
import paramiko
import getpass
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import uuid
import time

DEFAULT_CONFIG = ".eskit/config.json"
CACHE_ROOT = Path(".eskit")
HTTP_METHOD_DELETE = "DELETE"
HTTP_METHOD_PUT = "PUT"
HTTP_METHOD_POST = "POST"
HTTP_METHOD_GET = "GET"

## EXCEPTIONS

@dataclass
class ESKitJob:
    id: str
    name: str
    type: str              # reindex | rsync
    host: str
    status: str            # running | success | failed
    created_at: str
    updated_at: str
    payload: dict
    result: dict | None = None
    error: str | None = None

class ESKitError(Exception):
    def __init__(self, msg):
        self.msg = msg
        super().__init__(msg)

class ElasticsearchError(ESKitError):
    def __init__(self, status, response):

        self.status = status
        self.response = response
        error_type = None
        reason = None
        
        if isinstance(response, dict):
            error = response.get("error", {})

            if isinstance(error, dict):
                error_type = error.get("type")
                reason = error.get("reason")

        msg = f"HTTP {status}"
        if error_type:
            msg += f" [{error_type}]"
        if reason:
            msg += f": {reason}"

        super().__init__(msg)

class CacheError(ESKitError):
    pass

class ConfigError(ESKitError):
    pass

class HostError(ESKitError):
    pass

##
def print_host(host):
    print(f"\n=== ESKit HOST: {host} ===\n")

def print_dry_run():
    print(f"\n*Dry Run*\n")

def load_config(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def get_host(config, name):
    for h in config.get("hosts", []):
        if h["name"] == name:
            return h
    raise SystemExit(f"Host not found: {name}")

def get_rsync_config(config, name):
    for h in config.get("rsync-configs", []):
        if h["name"] == name:
            return h
    raise SystemExit(f"Host not found: {name}")

def check_host(host):
    if host is None:
        raise SystemExit("Host not found. Please specify host or set host.")
    return

def check_push_protected(config, host, dry_run, push):
    host_config = get_host(config, host)
    if "push-protected" in host_config and host_config["push-protected"] and not dry_run and not push:
        raise SystemExit("Host is push protected. Please use --push to make change or --dry-run to check command")
    return

def is_push_protected(config, host):
    host_config = get_host(config, host)
    return "push-protected" in host_config and host_config["push-protected"]

def confirm_delete(kind, name):
    print(f"About to delete {kind}: {name}\n")
    x = input("Confirm delete by typing:")
    print("\n")
    return x == name

def get_current_host():
    with open(CACHE_ROOT / ".current_host", "r", encoding="utf-8") as f:
        for line in f:
            return line

def set_current_host(host):
    with open(CACHE_ROOT / ".current_host", "w", encoding="utf-8") as f:
        f.write(host)

def cache_dir(host):
    return CACHE_ROOT / host / "cache"

def cache_age(path):
    if not path.exists():
        return None
    age_sec = time.time() - path.stat().st_mtime
    return age_sec

def cache_date(path):
    if not path.exists():
        return None
    return datetime.fromtimestamp(path.stat().st_mtime).strftime('%A, %B %d, %Y at %I:%M %p')

def job_dir(host):
    return CACHE_ROOT / host / "cache" / "jobs"

def ensure_cache(host):
    cache_dir(host).mkdir(parents=True, exist_ok=True)

def ensure_job_dir(host):
    job_dir(host).mkdir(parents=True, exist_ok=True)

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
    
def write_job(host, job: ESKitJob):
    ensure_job_dir(host)
    shot_id = job.id.split('-')[-1]
    with open(job_dir(host) / f"{job.type}-{job.name}-{shot_id}.json", "w") as f:
        json.dump(asdict(job), f, indent=2)

def read_job(host, job_id):
    path = job_dir(host) / f"{job_id}.json"
    if not path.exists():
        return None
    return json.load(open(path))

def list_jobs(host):
    if not job_dir(host).exists():
        return []

    jobs = []
    for f in job_dir(host).glob("*.json"):
        jobs.append(json.load(open(f)))

    jobs.sort(key=lambda x: x["created_at"], reverse=True)
    return jobs

def is_agent_available():
    try:
        agent = paramiko.Agent()
        return len(agent.get_keys()) > 0
    except Exception:
        return False
    
def find_index(host, index):
    index_cache = read_cache(host, "indices")
    if not index_cache:
        return False
    
    for i in index_cache:
        if index == i["index"]:
            return True
    
    return False

def find_repo(host, repo):
    repos_cache = read_cache(host, "repos")
    for repo_name, repo_data in repos_cache.items():
        return repo == repo_name
    
    return False

def find_snapshot(host, repo, snapshot):
    snapshots_cache = read_cache(host, "snapshots")
    if not "repo" in snapshots_cache:
        return False
    snap_list = snapshots_cache[repo]["snapshots"]
    for s in snap_list:
        return snapshot == s["snapshot"]
    
    return False

def get_reindex_mapping(config, host, name):
    reindex_configs = config.get("reindex-configs")
    if not reindex_configs:
        return None
    for c in reindex_configs:
        if c["name"] == name:
            return c["mappings"]
    return None

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
        if self.config and "port" in self.config:
            port = self.config["port"]

        username = None
        password = None
        if self.config and "user" in self.config:
            username = self.config["user"].get("name")
            password = self.config["user"].get("password")
        cmd ="curl "
        cmd += f"-w '\\n%{{http_code}}' "

        if username and password:
            cmd += f" -u {username}:{password}"
        
        cmd += f" -s -X {method.upper()} 'http://localhost:{port}{path}'"
        
        if body is not None:
            payload = json.dumps(body).replace("'", "'\"'\"'")
            cmd += f" -H 'Content-Type: application/json' -d '{payload}'"
            #print("elastic_config", self.config)

        safe_cmd = cmd
        if password:
            safe_cmd = safe_cmd.replace(
                password,
                "******"
        )
             
        print("cmd:", safe_cmd)
        result = self.transport.run(cmd)
        body, status = result.rsplit("\n", 1)
        status = int(status)
        body = json.loads(body)

        if status >= 400:
            raise ElasticsearchError(status, body)
        
        return body

def pull_host(host_name, es):

    if host_name is None:
        host_name = get_current_host()

    check_host(host_name)
    print_host(host_name)

    repos = es.request("GET", "/_snapshot")
    write_cache(host_name, "repos", repos)

    snapshots = {}
    if isinstance(repos, dict):
        for repo in repos.keys():
            snapshots[repo] = es.request("GET", f"/_snapshot/{repo}/_all")
    write_cache(host_name, "snapshots", snapshots)

    indices = es.request("GET", "/_cat/indices?format=json")
    write_cache(host_name, "indices", indices)
    print("\nCache updated.\n")

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

def cmd_list_job(host_name):
    if host_name is None:
        host_name = get_current_host()
    
    check_host(host_name)

    return list_jobs(host_name)

def cmd_read_job(host_name, job_id):
    if host_name is None:
        host_name = get_current_host()
    
    check_host(host_name)

    return read_job(host_name, job_id)

def cmd_status(config, host_name):
    if host_name is None:
        host_name = get_current_host()

    check_host(host_name)

    print(f"Host:")
    print(f"    Name: {host_name}")

    # push protected
    print(f"    Push Protected: {is_push_protected(config, host_name)}")

    cache_root = cache_dir(host_name)

    print("Cache Last Update:")
    for name in ["indices", "repos", "snapshots"]:
        path = cache_root / f"{name}.json"
        date = cache_date(path)

        if date is None:
            print(f"    {name}: missing")
        else:
            print(f"    {name}: {date}")

    ''' TODO
    jobs = list_jobs(host_name)

    running = sum(1 for j in jobs if j["status"] == "running")
    failed = sum(1 for j in jobs if j["status"] == "failed")
    success = sum(1 for j in jobs if j["status"] == "success")

    print("\nJobs:")
    print(f"  running: {running}")
    print(f"  success: {success}")
    print(f"  failed:  {failed}")
    '''

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
            snap_list = []
            for s in snapshots:
                snap_list.append(s["snapshot"])
            out[repo] = {}
            out[repo]["snapshots"] = snap_list
        pass
    elif kind == "repos":
        out = data
    elif kind == "indices":
        out = []
        for i in data:
            index = {}
            index["index"]=i["index"]
            out.append(index)
        out.sort(key=lambda x: x["index"])
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
        return

    out={}

    repo_data = data.get(repo, {})
    if not repo_data:
        return

    out[repo] = repo_data

    snapshots = read_cache(host_name, "snapshots")

    if not snapshots:
        print(json.dumps(data.get(repo, {}), indent=2))
        return
    snapshots = snapshots.get(repo,{}).get("snapshots",{})
    snap_list = []
    for s in snapshots:
        snap_list.append(s["snapshot"])

    out[repo]["snapshots"] = snap_list
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

def cmd_reindex_mapping(config):
    print(json.dumps(config["reindex-configs"], indent=2))

def cat_recovery(config, host):
    if host is None:
        host = get_current_host()

    check_host(host)

    ssh, es = connect_es(config, host)
    try:
        out = []
        data = es.request("GET", "/_cat/recovery?format=json")
        for r in data:
            info = {}
            info["index"] = r["index"]
            info["files_percent"] = r["files_percent"]
            out.append(info)
        out.sort(key=lambda x: x["index"])
        print(json.dumps(out, indent=2))
    finally:
        ssh.close()

def create_repo(config, host, name, repo_type, location, dry_run, push):

    if host is None:
        host = get_current_host()

    check_host(host)
    check_push_protected(config, host, dry_run, push)
    print_host(host)

    if not find_repo(host, name):
        print(f"Repo:{name} found in cache. Please pull latest.")
        return

    body = {"type": repo_type, "settings": {"location": location}}
    if dry_run:
        print_dry_run()
        print("PUT", f"/_snapshot/{name}")
        print(json.dumps(body, indent=2))
        return
    ssh, es = connect_es(config, host)
    try:
        es.request("PUT", f"/_snapshot/{name}", body)
        print(f"Repo:{name} created. Updating Cache...")
        pull_host(host, es)
    finally:
        ssh.close()

def delete_repo(config, host, name, dry_run, push, force):

    if host is None:
        host = get_current_host()

    check_host(host)
    check_push_protected(config, host, dry_run, push)
    print_host(host)

    if not find_repo(host, name):
        print(f"Repo:{name} not found in cache. Please pull latest.")
        return

    if not dry_run and not force:
        if not confirm_delete("repo", name):
            print("cancelled")
            return

    if dry_run:
        print_dry_run()
        print("DELETE", f"/_snapshot/{name}")
        return
    ssh, es = connect_es(config, host)
    try:
        es.request("DELETE", f"/_snapshot/{name}")
        print(f"Repo:{name} deleted. Updating Cache...")
        pull_host(host, es)
    finally:
        ssh.close()

def create_snapshot(config, host, spec, indices, include_global_state, ignore_unavailable, dry_run, push):

    if host is None:
        host = get_current_host()

    check_host(host)
    check_push_protected(config, host, dry_run, push)
    print_host(host)

    repo, delim, snap = spec.partition("/")
    if not repo or not snap:
        print(f"Snapshot:{spec} is not in valid format <repo>/<snapshot>")
        return
    
    if find_snapshot(host, repo, snap):
        print(f"Snapshot:{spec} found in chace. Please pull latest.")
        return

    body = {}
    if indices:
        body["indices"] = indices
    body["include_global_state"] = include_global_state
    body["ignore_unavailable"] = ignore_unavailable
    if dry_run:
        print_dry_run()
        print("PUT", f"/_snapshot/{repo}/{snap}")
        print(json.dumps(body, indent=2))
        return
    ssh, es = connect_es(config, host)
    try:
        es.request("PUT", f"/_snapshot/{repo}/{snap}", body)
        pull_host(host, es)
    finally:
        ssh.close()

def delete_snapshot(config, host, spec, dry_run, push, force):

    repo, delim, snap = spec.partition("/")
    if host is None:
        host = get_current_host()

    check_host(host)
    check_push_protected(config, host, dry_run, push)
    print_host(host)

    if not find_snapshot(host, repo, snap):
        print(f"Snapshot:{spec} not found in chace. Please pull latest.")
        return
    
    if not dry_run and not force:
        if not confirm_delete("snapshot", spec):
            print("cancelled")
            return

    if dry_run:
        print_dry_run()
        print("DELETE", f"/_snapshot/{repo}/{snap}")
        return
    ssh, es = connect_es(config, host)
    try:
        es.request("DELETE", f"/_snapshot/{repo}/{snap}")
        print(f"Snap{spec} created. Updating Cache...")
        pull_host(host, es)
    finally:
        ssh.close()

def restore_snapshot(config, host, spec, dry_run, push):
    repo, delim, snap = spec.partition("/")
    if host is None:
        host = get_current_host()

    check_host(host)
    check_push_protected(config, host, dry_run, push)
    print_host(host)

    body = {}
    body["indices"] = "*"
    body["include_global_state"] = False
    
    if dry_run:
        print_dry_run()
        print("POST", f"/_snapshot/{repo}/{snap}/_restore")
        print(json.dumps(body, indent=2))
        return
    ssh, es = connect_es(config, host)
    try:
        es.request("POST", f"/_snapshot/{repo}/{snap}/_restore",body)
        print(f"Snap:{spec} restored. Updating Cache...")
        pull_host(host, es)
    finally:
        ssh.close()

def delete_index(config, host, index, dry_run, push, force):
    if host is None:
        host = get_current_host()

    check_host(host)
    check_push_protected(config, host, dry_run, push)
    print_host(host)

    if not find_index(host, index):
        print(f"Index:{index} not found in cache. Please pull latest")
        return

    if not dry_run and not force:
        if not confirm_delete("index", index):
            print("cancelled")
            return

    url = f"/{index}"
    if dry_run:
        print_dry_run()
        print(HTTP_METHOD_DELETE, url)
        return
    ssh, es = connect_es(config, host)
    try:
        res = es.request(HTTP_METHOD_DELETE, url)
        print(res)
        print(f"Index:{index} deleted. Updating Cache...")
        pull_host(host, es)
    except Exception as e:
        print(e)
    finally:
        ssh.close()    

def create_index(config, host, index, mapping, dry_run, push):
    
    if host is None:
        host = get_current_host()

    check_host(host)
    check_push_protected(config, host, dry_run, push)
    print_host(host)

    if find_index(host, index):
        print("index already exist in cache. Please pull latest or delete the index")
        return

    body = {}
    if mapping:
        m = get_reindex_mapping(config, host, mapping)
        if m:
            body["mappings"] = m

    url = f"/{index}"
    if dry_run:
        print_dry_run()
        print(HTTP_METHOD_PUT, url)
        print(json.dumps(body, indent=2))
        return
    ssh, es = connect_es(config, host)
    try:
        res = es.request(HTTP_METHOD_PUT, url, body)
        print(res)
        print(f"Index:{index} created. Updating Cache...")
        pull_host(host, es)
    except Exception as e:
        print(e)
    finally:
        ssh.close()

def reindex(config, host, src, dst, mapping, dry_run, push):
    
    if host is None:
        host = get_current_host()

    check_host(host)
    check_push_protected(config, host, dry_run, push)
    print_host(host)

    body = {}
    m = None
    if mapping:
        m = get_reindex_mapping(config, host, mapping)
        if m:
            body["mappings"] = m
        else:
            print(f"mapping:{mapping} does not exist in the config.")
            return
    
    dst_exists = find_index(host, dst)
    if m and dst_exists:
        print("mapping specified, but index already exist in cache. Please pull latest or delete the index")
        return

    if not dst_exists:
        print(f"creating a new dst:{dst}")
        create_index(config, host, dst, mapping, dry_run, push)

    job = ESKitJob(
        id=str(uuid.uuid4()),
        name=src,
        type="reindex",
        host=host,
        status="running",
        created_at=datetime.now(timezone.utc).isoformat(),
        updated_at=datetime.now(timezone.utc).isoformat(),
        payload={"src": src, "dst": dst}
    )

    write_job(host, job)

    body={}
    body["source"] = {"index":src}
    body["dest"] = {"index":dst}

    # default: don't wait
    url = f"/_reindex?wait_for_completion=false"
    if dry_run:
        print_dry_run()
        print(HTTP_METHOD_POST, url)
        print(json.dumps(body, indent=2))
        return
    ssh, es = connect_es(config, host)
    try:
        res = es.request(HTTP_METHOD_POST, url, body)
       # print(json.dumps(res, indent=2))
       # print("check status with task-get command with the id")
    
        job.status = "running"
        job.result = {"task_id": res.get("task")}
        job.updated_at = datetime.now(timezone.utc).isoformat()

        write_job(host, job)

        print(f"[{host}] reindex job started: {job.id}")

    except Exception as e:
        job.status = "failed"
        job.error = str(e)
        write_job(host, job)
        print(e)
    finally:
        ssh.close()

def get_task(config, host, task_id):
    
    if host is None:
        host = get_current_host()

    check_host(host)
    print_host(host)

    url = f"/_tasks/{task_id}"

    ssh, es = connect_es(config, host)
    try:
        res = es.request(HTTP_METHOD_GET, url)
        print(json.dumps(res, indent=2))
    except Exception as e:
        print(e)
    finally:
        ssh.close()

def show_index(config, host, index):
    if host is None:
        host = get_current_host()

    check_host(host)
    print_host(host)

    url = f"/{index}"

    ssh, es = connect_es(config, host)
    try:
        res = es.request(HTTP_METHOD_GET, url)
        index_data = res[index]
        out = {}
        out["mappings"] = {}
        out["mappings"]["properties"] = {}
        out["mappings"]["properties"]["@timestamp"] = index_data["mappings"]["properties"]["@timestamp"]
        out["settings"] = index_data["settings"]
        print(json.dumps(out, indent=2))
    except Exception as e:
        print(e)
    finally:
        ssh.close()

def run_rsync(config, rsync_config, host, dry_run, push):
     
    rsync_src = rsync_config["src"]
    rsync_dst = rsync_config["dst"]

    print(rsync_src)
    print(rsync_dst)

    src_host = get_host(config, rsync_src["host"])
    dst_host = get_host(config, rsync_dst["host"])

    print(src_host)
    print(dst_host)

    #check_host(host)
    #check_push_protected(config, host, dry_run, push)

    job = ESKitJob(
        id=str(uuid.uuid4()),
        name=rsync_src["path"],
        type="rsync",
        host=host,
        status="running",
        created_at=datetime.now(timezone.utc).isoformat(),
        updated_at=datetime.now(timezone.utc).isoformat(),
        payload={"src": rsync_src, "dst": rsync_dst}
    )

    write_job(host, job)

    ssh_config = rsync_dst["auth"]["ssh"]

    # sudo rsync -av --progress -e "ssh -p 22 -i .ssh/example-key" demo-user@example.com:/home/demo-user/elk/snapshot elk
    cmd = f"nohup rsync -avz --info=progress2 -e \"ssh -p {ssh_config['port']} -i {ssh_config['identity']}\" {ssh_config['user']}@{src_host['ip']}:{rsync_src['path']} {rsync_dst['path']} "
    cmd += f" >/tmp/eskit_rsync_{job.id}.log 2>&1 & echo $!"
    print(cmd)

    ssh, _ = connect_es(config, rsync_dst["host"])

    try:
        output = ssh.run(cmd)

        job.status = "started"
        job.result = {"output": output}

    except Exception as e:
        job.status = "failed"
        job.error = str(e)

    finally:
        job.updated_at = datetime.now(timezone.utc).isoformat()
        write_job(host, job)
        ssh.close()

def build_parser():
    p = argparse.ArgumentParser(
        prog="eskit",
        description="a light weight Elasticsearch toolkit for managing repo, snapshots, and index.")
    p.add_argument("-c","--config", default=DEFAULT_CONFIG, help="set config file")
    p.add_argument("-dry","--dry-run", action="store_true", help="shows only request/command w/o executing it")
    p.add_argument("--push", action="store_true", help="used to confirm to execute a request/command that would modify resources on push-protected host")
    p.add_argument("--force", action="store_true", help="force to execute delete request/command")

    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("host")

    host_set = sub.add_parser("host-set", help="set as current host")
    host_set.add_argument("host")

    sub.add_parser("host-get", help="get current host")

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

    index_delete = sub.add_parser("index-delete")
    index_delete.add_argument("--host")
    index_delete.add_argument("index")

    index_create = sub.add_parser("index-create")
    index_create.add_argument("--host")
    index_create.add_argument("index")
    index_create.add_argument("-m","--mapping", help="name of mapping in the config")

    index_show = sub.add_parser("index-show")
    index_show.add_argument("--host")
    index_show.add_argument("index")

    sub.add_parser("reindex-mapping")
    
    reindex = sub.add_parser("reindex")
    reindex.add_argument("src")
    reindex.add_argument("dst")
    reindex.add_argument("--host")
    reindex.add_argument("-m","--mapping", help="name of mapping in the config")

    task_get = sub.add_parser("task-get")
    task_get.add_argument("--host")
    task_get.add_argument("task_id")

    rsync = sub.add_parser("rsync")
    rsync.add_argument("--host")
    rsync.add_argument("config_name")

    job_list = sub.add_parser("job-list")
    job_list.add_argument("--host")

    job_show = sub.add_parser("job-show")
    job_show.add_argument("--host")
    job_show.add_argument("job_id")

    status = sub.add_parser("status")
    status.add_argument("--host")

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
        create_repo(config, args.host, args.repo, args.type, args.location, args.dry_run, args.push)
    elif args.cmd == "repo-delete":
        delete_repo(config, args.host, args.repo, args.dry_run, args.push, args.force)
    elif args.cmd == "snap-show":
        cmd_snap_show(args.host, args.snapshot)
    elif args.cmd == "snap-create":
        create_snapshot(config, args.host, args.snapshot, args.index, args.include_global_state,args.ignore_unavailable, args.dry_run, args.push)
    elif args.cmd == "snap-delete":
        delete_snapshot(config, args.host, args.snapshot, args.dry_run, args.push, args.force)
    elif args.cmd == "snap-restore":
        restore_snapshot(config, args.host, args.snapshot, args.dry_run, args.push)
    elif args.cmd == "snap-restore-check":
        cat_recovery(config, args.host)
    elif args.cmd == "reindex-mapping":
        cmd_reindex_mapping(config)
    elif args.cmd == "index-delete":
        delete_index(config, args.host,args.index, args.dry_run, args.push, args.force)
    elif args.cmd == "index-create":
        create_index(config, args.host,args.index, args.mapping, args.dry_run, args.push)
    elif args.cmd == "reindex":
        reindex(config, args.host,args.src, args.dst, args.mapping, args.dry_run, args.push)
    elif args.cmd == "task-get":
        get_task(config, args.host, args.task_id)
    elif args.cmd == "index-show":
        show_index(config, args.host,args.index)
    elif args.cmd == "rsync":
        run_rsync(config, get_rsync_config(config, args.config_name), args.host, args.dry_run, args.push)
    elif args.cmd == "job-list":
        print(json.dumps(cmd_list_job(args.host), indent=2))
    elif args.cmd == "job-show":
        print(json.dumps(cmd_read_job(args.host, args.job_id), indent=2))
    elif args.cmd == "status":
        cmd_status(config, args.host)
if __name__ == "__main__":
    main()
