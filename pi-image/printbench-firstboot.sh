#!/bin/bash
set -euo pipefail
umask 027

IMAGE_VERSION="PRINTBENCH-Pi-Bridge 1.1.0-dev"
COLLECTOR_COMMIT="c530ffa"
COLLECTOR_SHA="0A05C2A8448B3C3EB6DB90A26EC0C0793CA09D3BC4B35BC0537D08A568EF9EF8"
BOOT_ARCHIVE="/boot/firmware/printbench-collector.tar.gz"

mkdir -p /opt/printbench /etc/printbench /var/lib/printbench /var/log/journal /etc/ssh/sshd_config.d /etc/systemd/journald.conf.d
chown root:printbench /opt/printbench
chmod 0750 /opt/printbench
for g in gpio i2c spi; do getent group "$g" >/dev/null || groupadd --system "$g"; done
usermod -aG gpio,i2c,spi,dialout printbench
chown root:printbench /etc/printbench
chmod 0750 /etc/printbench

if [ ! -f "$BOOT_ARCHIVE" ]; then
  echo "PRINTBENCH bootstrap archive missing" >&2
  exit 20
fi
ACTUAL=$(sha256sum "$BOOT_ARCHIVE" | awk '{print toupper($1)}')
if [ "$ACTUAL" != "$COLLECTOR_SHA" ]; then
  echo "PRINTBENCH bootstrap checksum mismatch" >&2
  exit 21
fi

cat >/etc/printbench/image-version <<EOF
$IMAGE_VERSION
Base: Raspberry Pi OS Lite 64-bit 2026-10-06
Collector commit: $COLLECTOR_COMMIT
Build: 2026-10-14
EOF

cat >/etc/printbench/collector.env <<'EOF'
PRINTBENCH_P2S_HOST=192.168.178.110
PRINTBENCH_BAMBU_CONFIG=/etc/printbench/bambu.json
PRINTBENCH_MEDIA_WORKER=0
PRINTBENCH_SLICER_SCAN=0
PRINTBENCH_WEB_PUSH=1
PRINTBENCH_SPOOL_SYNC=0
EOF
chown root:printbench /etc/printbench/collector.env
chmod 0640 /etc/printbench/collector.env

cat >/etc/printbench/bambu.json.example <<'EOF'
{"serial":"YOUR_P2S_SERIAL","access_code":"YOUR_LAN_ACCESS_CODE"}
EOF
chown root:printbench /etc/printbench/bambu.json.example
chmod 0640 /etc/printbench/bambu.json.example

cat >/etc/ssh/sshd_config.d/99-printbench.conf <<'EOF'
PasswordAuthentication no
KbdInteractiveAuthentication no
PermitRootLogin no
PubkeyAuthentication yes
AllowUsers printbench
X11Forwarding no
AllowAgentForwarding no
AllowTcpForwarding yes
GatewayPorts no
ClientAliveInterval 120
ClientAliveCountMax 2
MaxAuthTries 3
EOF

cat >/etc/nftables.conf <<'EOF'
#!/usr/sbin/nft -f
flush ruleset
table inet printbench_filter {
  chain input {
    type filter hook input priority 0; policy drop;
    iifname "lo" accept
    ct state established,related accept
    ip protocol icmp accept
    ip6 nexthdr ipv6-icmp accept
    udp dport { 67, 68, 5353 } accept
    ip saddr 10.0.0.0/8 tcp dport 22 accept
    ip saddr 172.16.0.0/12 tcp dport 22 accept
    ip saddr 192.168.0.0/16 tcp dport 22 accept
    ip saddr 192.168.178.0/24 tcp dport 8080 accept
    ip6 saddr fe80::/10 tcp dport 22 accept
    ip6 saddr fc00::/7 tcp dport 22 accept
  }
  chain forward { type filter hook forward priority 0; policy drop; }
  chain output { type filter hook output priority 0; policy accept; }
}
EOF
chmod 0644 /etc/nftables.conf

cat >/etc/systemd/journald.conf.d/99-printbench.conf <<'EOF'
[Journal]
Storage=persistent
SystemMaxUse=100M
MaxRetentionSec=14day
EOF

cat >/etc/systemd/system/printbench-collector.service <<'EOF'
[Unit]
Description=PRINTBENCH P2S/AMS Collector
After=network-online.target
Wants=network-online.target
ConditionPathExists=/etc/printbench/bambu.json

[Service]
Type=simple
User=printbench
Group=printbench
WorkingDirectory=/opt/printbench/repo/tools/printbench_collector
EnvironmentFile=/etc/printbench/collector.env
ExecStart=/opt/printbench/venv/bin/python /opt/printbench/repo/tools/printbench_collector/daemon.py
Restart=on-failure
RestartSec=5
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/printbench/repo/tools/printbench_collector /var/lib/printbench
ReadOnlyPaths=/etc/printbench
RestrictAddressFamilies=AF_INET AF_INET6
LockPersonality=true
RestrictSUIDSGID=true

[Install]
WantedBy=multi-user.target
EOF

cat >/etc/systemd/system/printbench-collector.path <<'EOF'
[Unit]
Description=Start PRINTBENCH collector when printer credentials exist

[Path]
PathExists=/etc/printbench/bambu.json
Unit=printbench-collector.service

[Install]
WantedBy=multi-user.target
EOF

rm -rf /opt/printbench/repo
mkdir -p /opt/printbench/repo
tar -xzf "$BOOT_ARCHIVE" -C /opt/printbench/repo
python3 -m venv --system-site-packages /opt/printbench/venv
chown -R root:printbench /opt/printbench/venv
chmod -R g+rX,o-rwx /opt/printbench/venv
/opt/printbench/venv/bin/python -m pip install --upgrade pip
if ! /opt/printbench/venv/bin/python -c "import paho.mqtt.client, requests, watchdog"; then
  /opt/printbench/venv/bin/pip install -r /opt/printbench/repo/tools/printbench_collector/requirements.txt
fi
chown -R printbench:printbench /opt/printbench/repo /var/lib/printbench
install -o root -g root -m 0644 /opt/printbench/repo/tools/printbench_collector/pi_ui/printbench-ui.service /etc/systemd/system/printbench-ui.service
install -o root -g root -m 0644 /opt/printbench/repo/tools/printbench_collector/pi_ui/printbench-camera.service /etc/systemd/system/printbench-camera.service
install -o root -g root -m 0644 /opt/printbench/repo/tools/printbench_collector/pi_ui/printbench-reader.service /etc/systemd/system/printbench-reader.service

cat >/usr/local/sbin/printbench-pair <<'EOF'
#!/bin/bash
set -euo pipefail
if [ "${EUID}" -ne 0 ]; then exec sudo "$0" "$@"; fi
read -r -p "P2S IP [192.168.178.110]: " HOST
HOST=${HOST:-192.168.178.110}
read -r -p "P2S Seriennummer: " SERIAL
if [ -z "$SERIAL" ]; then echo "Seriennummer fehlt" >&2; exit 2; fi
read -r -s -p "P2S LAN Access Code: " CODE
echo
if [ -z "$CODE" ]; then echo "Access Code fehlt" >&2; exit 3; fi
umask 077
python3 - "$SERIAL" "$CODE" <<'PY'
import json,sys
from pathlib import Path
Path('/etc/printbench/bambu.json').write_text(json.dumps({'serial':sys.argv[1],'access_code':sys.argv[2]},indent=2)+'\n',encoding='utf-8')
PY
chown root:printbench /etc/printbench/bambu.json
chmod 0640 /etc/printbench/bambu.json
sed -i "s/^PRINTBENCH_P2S_HOST=.*/PRINTBENCH_P2S_HOST=${HOST}/" /etc/printbench/collector.env
systemctl restart printbench-collector.path
systemctl restart printbench-collector.service || true
systemctl restart printbench-camera.service || true
systemctl restart printbench-ui.service || true
sleep 2
systemctl --no-pager --full status printbench-collector.service || true
EOF
chmod 0755 /usr/local/sbin/printbench-pair

cat >/usr/local/bin/printbench-status <<'EOF'
#!/bin/bash
set -u
printf 'PRINTBENCH Pi Bridge\n'
printf 'Hostname: '; hostname
printf 'Kernel: '; uname -r
printf 'IP: '; hostname -I 2>/dev/null || true
printf 'Image: '; head -n1 /etc/printbench/image-version 2>/dev/null || echo unknown
printf 'Paired: '; test -s /etc/printbench/bambu.json && echo yes || echo no
printf 'SSH: '; systemctl is-active ssh 2>/dev/null || true
printf 'mDNS: '; systemctl is-active avahi-daemon 2>/dev/null || true
printf 'Firewall: '; systemctl is-active nftables 2>/dev/null || true
printf 'Collector: '; systemctl is-active printbench-collector.service 2>/dev/null || true
printf 'UI: '; systemctl is-active printbench-ui.service 2>/dev/null || true
printf 'Camera: '; systemctl is-active printbench-camera.service 2>/dev/null || true
printf 'Reader: '; systemctl is-active printbench-reader.service 2>/dev/null || true
printf 'P2S host: '; sed -n 's/^PRINTBENCH_P2S_HOST=//p' /etc/printbench/collector.env 2>/dev/null
EOF
chmod 0755 /usr/local/bin/printbench-status

# Hardware interfaces needed for later diagnostics; serial console remains enabled for recovery.
sed -i 's/^#dtparam=i2c_arm=on/dtparam=i2c_arm=on/; s/^#dtparam=spi=on/dtparam=spi=on/' /boot/firmware/config.txt

systemctl daemon-reload
systemctl enable ssh avahi-daemon nftables printbench-collector.path printbench-ui.service printbench-camera.service
systemctl restart ssh avahi-daemon nftables
systemctl start printbench-collector.path
systemctl start printbench-ui.service
systemctl restart systemd-journald
printf '%s\n' "PRINTBENCH Pi Bridge provisioned $(date -Is)" > /var/lib/printbench/image-ready
