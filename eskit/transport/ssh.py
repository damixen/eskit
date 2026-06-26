import paramiko
import getpass

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
        self.name = "SSHConnection"

    def connect(self):
        ssh = self.host_cfg["ssh"]
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        kwargs = {
            "hostname": self.host_cfg["ip"],
            "port": ssh.get("port", 22),
            "username": ssh["user"],
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
                allow_agent = False
            elif not is_agent_available():
                allow_agent = False

            if not allow_agent:
                passphrase = ssh.get("passphrase")
                kwargs["pkey"] = (
                    load_private_key(key_filename, passphrase) if key_filename else None
                )
            # Try to use agent by default unless disabled in the config
        try:
            self.client.connect(**kwargs)
        except paramiko.SSHException as e:
            print(f"SSH failure: {e}")

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
