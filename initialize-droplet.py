import digitalocean
import time
import sys
import json
from getpass import getpass
from paramiko import SSHClient, WarningPolicy
from sshtunnel import SSHTunnelForwarder
from urllib.parse import quote as urlencode

DROPLET_USERNAME = "dev"

class StewardConfig:
    def __init__(self, config_dict):
        if "headless" in config_dict.keys():
            self.headless = config_dict["headless"] == "true"
        else:
            self.headless = False

class DigitalOceanConfig:
    def __init__(self, config_dict):
        self.access_token = config_dict["access_token"]
        self.droplet_name = config_dict["droplet_name"]
        self.droplet_region = config_dict["droplet_region"]
        self.droplet_image = config_dict["droplet_image"]
        self.droplet_size_slug = config_dict["droplet_size_slug"]

class GitConfig:
    def __init__(self, config_dict):
        self.code_server_username = config_dict["code_server_username"]
        self.email = config_dict["email"]
        self.name = config_dict["name"]
        self.clone_url = config_dict["clone_url"]
        self.repo_dir = config_dict["repo_dir"]
        self.branch = config_dict["branch"]
        self.setup_script_name = config_dict["setup_script_name"]

class Config:
    def __init__(self, config_dict):
        self.steward_config = StewardConfig(config_dict["steward"]) if "steward" in config_dict.keys() else StewardConfig({})
        self.digital_ocean_config = DigitalOceanConfig(config_dict["digital_ocean"])
        self.git_config = GitConfig(config_dict["git"])
        

def wait_for_action_completion():
    action_list = droplet.get_actions()
    for action in action_list:
        action.wait()

def command_over_ssh(username, ip_address, command, force_pseudo_terminal=False):
    client = SSHClient()
    client.set_missing_host_key_policy(WarningPolicy)
    client.connect(ip_address, username=username)
    stdin, stdout, stderr = client.exec_command(command, get_pty=force_pseudo_terminal)
    for line in stdout:
        print('... ' + line.strip('\n'))
    client.close()

def transfer_file(username, ip_address, local_file_path, remote_file_path):
    client = SSHClient()
    client.set_missing_host_key_policy(WarningPolicy)
    client.connect(ip_address, username=username)
    sftp_client = client.open_sftp()
    sftp_client.put(local_file_path,remote_file_path)
    sftp_client.close()



if len(sys.argv) < 2:
    print("Need to pass config file as argument!")
    exit()
else:
    path_to_config_file = sys.argv[1]

with open(path_to_config_file) as f:
    config = Config(json.load(f))

code_server_password = getpass(prompt="Enter password for code server (e.g., GitHub, GitLab):")
clone_url = config.git_config.clone_url
https_prefix = "https://"
if clone_url.find(https_prefix) == 0:
    clone_url = clone_url[:len(https_prefix)] + \
        config.git_config.code_server_username + ":" + urlencode(code_server_password, safe="") + \
        "@" + clone_url[len(https_prefix):]
else:
    print("Only https cloning supported!")
    exit()

manager = digitalocean.Manager(token=config.digital_ocean_config.access_token)
keys = manager.get_all_sshkeys()
droplet = digitalocean.Droplet(token=config.digital_ocean_config.access_token,
                               name=config.digital_ocean_config.droplet_name,
                               region=config.digital_ocean_config.droplet_region,
                               image=config.digital_ocean_config.droplet_image,
                               size_slug=config.digital_ocean_config.droplet_size_slug,
                               ssh_keys = keys,
                               backups=True)
droplet.create()
wait_for_action_completion()
droplet.load()
print("Droplet created successfully!")
print("Setting up dev environment...")

time.sleep(35)
transfer_file("root", droplet.ip_address, "setup-script.sh", "setup-script.sh")

command_over_ssh("root", droplet.ip_address, "export HEADLESS=" + str(config.steward_config.headless) + \
                                             " CLONE_URL=" + clone_url + \
                                             " REPO_DIR=" + config.git_config.repo_dir + \
                                             " BRANCH=" + config.git_config.branch + \
                                             " SETUP_SCRIPT=" + config.git_config.setup_script_name + \
                                             " EMAIL=" + config.git_config.email + \
                                             " NAME=" + config.git_config.name + \
                                             " && bash setup-script.sh", force_pseudo_terminal=True)

print("Done setting up virtual desktop!")

if not config.steward_config.headless:
    command_over_ssh(DROPLET_USERNAME, droplet.ip_address, "vncserver -SecurityTypes None")

    tunnel = SSHTunnelForwarder(
        droplet.ip_address,
        ssh_username=DROPLET_USERNAME,
        remote_bind_address=('127.0.0.1', 5901),
        local_bind_address=('127.0.0.1', 5901)
    )
    tunnel.start()
    print("Securely tunneling VNC display :1 to 127.0.0.1")

print("IP address: " + droplet.ip_address)
print("Username: " + DROPLET_USERNAME)

input("Press enter to destroy virtual desktop...")
if not config.steward_config.headless:
    tunnel.stop()
droplet.destroy()
