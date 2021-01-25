ufw allow ssh
ufw -f enable
apt update
add-apt-repository main
add-apt-repository universe
add-apt-repository restricted
add-apt-repository multiverse 
apt install -y tasksel
tasksel install ubuntu-desktop
apt-get --purge remove -y gnome-initial-setup
apt install -y tigervnc-standalone-server tigervnc-common
snap install --classic code

adduser --disabled-password --gecos "" dev
mkdir /home/dev/.ssh
chmod 700 /home/dev/.ssh
cp /root/.ssh/authorized_keys /home/dev/.ssh/authorized_keys
chmod 600 /home/dev/.ssh/authorized_keys
chown -R dev:dev /home/dev/.ssh
usermod -aG sudo dev
echo 'dev ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers

su dev -c "git config --global user.email '$EMAIL'"
su dev -c "git config --global user.name '$NAME'"
su dev -c "cd ~ && git clone $CLONE_URL $REPO_DIR"
su dev -c "cd ~/$REPO_DIR && git checkout -b $BRANCH origin/$BRANCH"
if [[ ! -z $SETUP_SCRIPT ]]
then
  su dev -c "cd ~/$REPO_DIR && bash $SETUP_SCRIPT"
fi
