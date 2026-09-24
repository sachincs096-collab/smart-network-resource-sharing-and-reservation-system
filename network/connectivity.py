import ipaddress
import platform
import subprocess


def ping(ip_address):
    address = ipaddress.ip_address(ip_address)
    command = ["ping", "-n", "1", "-w", "1000", str(address)] if platform.system() == "Windows" else ["ping", "-c", "1", "-W", "1", str(address)]
    result = subprocess.run(command, capture_output=True, text=True, timeout=3, check=False)
    return result.returncode == 0
