from pathlib import Path
import struct
from pyfatfs.PyFatFS import PyFatFS

base = Path(r"C:\Users\dezen\Desktop\3d-Files\pi-image")
img = base / "PRINTBENCH-Pi-Bridge-arm64.img"

with img.open("rb") as f:
    mbr = f.read(512)
entry = mbr[446:462]
ptype = entry[4]
start_lba = struct.unpack("<I", entry[8:12])[0]
if ptype not in (0x0B, 0x0C, 0x0E):
    raise SystemExit(f"Unexpected boot partition type: {ptype:#x}")

fs = PyFatFS(str(img), offset=start_lba * 512, read_only=False)
try:
    text_files = {
        "user-data": base / "user-data",
        "network-config": base / "network-config",
        "meta-data": base / "meta-data",
        "printbench-firstboot.sh": base / "printbench-firstboot.sh",
    }
    for dest, src in text_files.items():
        if fs.exists(dest):
            fs.remove(dest)
        fs.writetext(dest, src.read_text(encoding="utf-8"), encoding="utf-8")

    archive = base / "printbench-collector.tar.gz"
    if fs.exists("printbench-collector.tar.gz"):
        fs.remove("printbench-collector.tar.gz")
    fs.writebytes("printbench-collector.tar.gz", archive.read_bytes())

    marker = (
        "PRINTBENCH Pi Bridge 1.0.0\n"
        "Base: Raspberry Pi OS Lite 64-bit 2026-10-06\n"
        "Collector: c530ffa\n"
        "Hostname: printbench-pi.local\n"
        "SSH user: printbench\n"
        "First boot requires Ethernet.\n"
    )
    if fs.exists("PRINTBENCH-IMAGE.txt"):
        fs.remove("PRINTBENCH-IMAGE.txt")
    fs.writetext("PRINTBENCH-IMAGE.txt", marker, encoding="utf-8")

    cfg = fs.readtext("config.txt")
    cfg = cfg.replace("#dtparam=i2c_arm=on", "dtparam=i2c_arm=on")
    cfg = cfg.replace("#dtparam=spi=on", "dtparam=spi=on")
    fs.remove("config.txt")
    fs.writetext("config.txt", cfg, encoding="utf-8")
finally:
    fs.close()

print(f"patched={img}")
print(f"boot_offset={start_lba * 512}")
