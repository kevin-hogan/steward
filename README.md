# Steward

Steward is a tool for provisioning cloud-based development environments. It's a step towards a brighter future in which setting up your development environment is **always** a breeze.

## How it works

Steward programmatically integrates with cloud providers to launch a virtual machine of the desired image, size, and region (currently, Steward is restricted to launching Linux VMs a.k.a. "droplets" on Digital Ocean). It will install a desktop environment on the VM as well as a VNC server to support remote access. It will also install Visual Studio Code. Finally, Steward will clone a desired Git repository on the machine and run a project-specific setup script if one exists in the repository.

Once Steward has completed provisioning the environment, it will tunnel the VNC port to your loopback address. Users can then connect to their virtual desktop!

## Setup

1. Make sure you have Python 3 installed.
2. Run `pip3 install -r requirements.txt` to install Python dependencies.
3. Create an account on Digital Ocean (using [this referral link](https://m.do.co/c/8cc2e62053f0) to get free starter credits, if you'd like). Alternatively, you can ask a friend to take the following steps in their account.
4. Create a [personal API access token](https://www.digitalocean.com/docs/apis-clis/api/create-personal-access-token/) with read and write permissions.
5. [Add your public ssh key](https://www.digitalocean.com/docs/droplets/how-to/add-ssh-keys/to-account/) to your account.
6. Install a VNC client. [Reminna](https://remmina.org/) is great for Linux (you may need to install the VNC plugin as described [here](https://wiki.archlinux.org/index.php/Remmina)). I've heard [this](https://www.realvnc.com/en/connect/download/viewer/windows/) is a good option for other platforms, but I haven't tried it out yet.

## Running Steward

You can run Steward with the following command: `python3 initialize-droplet.py conf.json`. See `conf.json.example` for details on the configuration file.

Steward will initially prompt you with a request for your code server credentials corresponding to the username you provided in the configuration file. After you enter these credentials, it will run through the process described in "How it works". If (but not only if) the script executes successfully, you will see the following printed at the bottom of the output (expect it to take around 15 minutes):

```
Done setting up virtual desktop!
Securely tunneling VNC display :1 to 127.0.0.1
IP address: xxx.xx.xxx.xxx
Username: dev
Press enter to destroy virtual desktop...
```
At this point, you can use your chosen VNC client to connect to your virtual desktop (note you may have to specify the port with the IP address, e.g. `127.0.0.1:1` or `127.0.0.1:5901`). When you press enter, Steward will close the SSH tunnel it sets up for VNC and will destroy the virtual desktop machine.

## Disclaimers and warnings

* Steward is currently a prototype that has not been well-tested. I'm happy for folks to create issues, but I just want users to have the appropriate expectations for quality when trying out the tool.
* Note that the script does not validate the code server password (it will just fail all interactions with it). So type carefully!
* Note that the credentials you provide for the code server will be stored in clear-text on the cloud machine started by the script (because Steward clones repositories [this way](https://stackoverflow.com/a/10054470)). This may be a security concern for some users.
* If Steward fails after creating the virtual machine but before reaching the end of the script, it probably did not destroy the machine. Remember to check your [Digital Ocean dashboard](https://cloud.digitalocean.com/droplets) to make sure you're not accumulating a bunch of droplets unexpectedly!
