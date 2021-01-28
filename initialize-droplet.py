import digitalocean
import time
import sys
import json
from getpass import getpass
from paramiko import SSHClient, WarningPolicy
from sshtunnel import SSHTunnelForwarder

DROPLET_USERNAME = "dev"

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
    config_dict = json.load(f)

token = config_dict["digital_ocean"]["access_token"]
code_server_password = getpass(prompt="Enter password for code server (e.g., GitHub, GitLab):")
clone_url = config_dict["git"]["clone_url"]
https_prefix = "https://"
if clone_url.find(https_prefix) == 0:
    clone_url = clone_url[:len(https_prefix)] + \
        config_dict["git"]["code_server_username"] + ":" + code_server_password.replace("@", "%40") + \
        "@" + clone_url[len(https_prefix):]
else:
    print("Only https cloning supported!")
    exit()

manager = digitalocean.Manager(token=token)
keys = manager.get_all_sshkeys()
droplet = digitalocean.Droplet(token=token,
                               name=config_dict["digital_ocean"]["droplet_name"],
                               region=config_dict["digital_ocean"]["droplet_region"],
                               image=config_dict["digital_ocean"]["droplet_image"],
                               size_slug=config_dict["digital_ocean"]["droplet_size_slug"],
                               ssh_keys = keys,
                               backups=True)
droplet.create()
wait_for_action_completion()
droplet.load()
print("Droplet created successfully!")
print("Setting up dev environment...")

time.sleep(35)
transfer_file("root", droplet.ip_address, "setup-script.sh", "setup-script.sh")

command_over_ssh("root", droplet.ip_address, "export CLONE_URL=" + clone_url + \
                                             " REPO_DIR=" + config_dict["git"]["repo_dir"] + \
                                             " BRANCH=" + config_dict["git"]["branch"] + \
                                             " SETUP_SCRIPT=" + config_dict["git"]["setup_script_name"] + \
                                             " EMAIL=" + config_dict["git"]["email"] + \
                                             " NAME=" + config_dict["git"]["name"] + \
                                             " && bash setup-script.sh", force_pseudo_terminal=True)
command_over_ssh(DROPLET_USERNAME, droplet.ip_address, "vncserver -SecurityTypes None")

tunnel = SSHTunnelForwarder(
    droplet.ip_address,
    ssh_username=DROPLET_USERNAME,
    remote_bind_address=('127.0.0.1', 5901),
    local_bind_address=('127.0.0.1', 5901)
)

tunnel.start()

print("Done setting up virtual desktop!")
print("Securely tunneling VNC display :1 to 127.0.0.1")
print("IP address: " + droplet.ip_address)
print("Username: " + DROPLET_USERNAME)

input("Press enter to destroy virtual desktop...")
tunnel.stop()
droplet.destroy()
