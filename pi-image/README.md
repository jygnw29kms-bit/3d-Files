# PRINTBENCH Pi Bridge Image

Custom Raspberry Pi OS Lite 64-bit image for the PRINTBENCH / DEZENDER 3D-printing project.

## Image

`PRINTBENCH-Pi-Bridge-1.0.0-arm64.img.xz`

Base: Raspberry Pi OS Lite 64-bit, image reference 2026-10-06.
Target: Raspberry Pi 3 / 4 / 5 and Zero 2-class 64-bit boards supported by the upstream image.

## First boot

1. Flash the `.img.xz` with Raspberry Pi Imager using **Use custom**.
2. Do **not** apply Raspberry Pi Imager OS customisation settings; this image already contains its own cloud-init configuration.
3. Connect Ethernet before the first boot.
4. Power on the Pi and allow roughly 5-15 minutes for the first boot. Package updates may make the first boot longer.
5. The hostname is `printbench-pi` and mDNS name is `printbench-pi.local`.
6. SSH password login and root login are disabled. The local image SSH key is required.

## Security

- SSH public-key authentication only.
- Root SSH login disabled.
- Password authentication disabled.
- nftables input firewall: established traffic, ICMP, DHCP/mDNS and SSH from private LAN ranges only.
- No Bambu serial number, LAN access code, PRINTBENCH push token or spool admin token is embedded in the image.
- The collector is not started until `/etc/printbench/bambu.json` exists.
- Camera/media worker, web push, slicer scan and private spool sync start disabled on the Pi.

## PRINTBENCH software

The boot partition contains a checksummed bootstrap archive of `tools/printbench_collector` from Git commit `c530ffa`.
The first-boot script installs it under `/opt/printbench/repo/tools/printbench_collector`, creates `/opt/printbench/venv`, installs Python requirements and registers the collector as a systemd service.

Useful commands after login:

```bash
printbench-status
sudo printbench-pair
systemctl status printbench-collector.service
journalctl -u printbench-collector.service -f
```

`printbench-pair` prompts for the P2S IP, printer serial number and LAN access code. The access code is entered silently and is written only to `/etc/printbench/bambu.json` with restricted permissions.

## Hardware preparation

I2C and SPI are enabled for later diagnostics. The serial console remains enabled as a recovery path. We will only change UART/serial settings when the AMS bus test actually requires it.

## Files kept local and not committed

- final `.img` / `.img.xz`
- SHA256 files
- generated SSH private key
- generated cloud-init `user-data`
- official Raspberry Pi base image

Do not commit secrets or runtime databases.
