#!/usr/bin/env python3
import requests
from datetime import datetime
import os

SRC_URL = "https://raw.githubusercontent.com/zhiyi7/gfw-pac/master/gfwlist/cn.txt"
OUTPUT_DIR = "mikrotik"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "cnip.rsc")

def main():
    print("[+] Downloading CN IP data from gfw-pac...")
    r = requests.get(SRC_URL, timeout=30)
    r.raise_for_status()
    lines = r.text.splitlines()

    # 过滤空行和注释
    cn_ips = [line.strip() for line in lines if line.strip() and not line.startswith("#")]

    # 添加自定义网段
    cn_ips.append("10.10.10.0/25")

    print(f"[+] Total {len(cn_ips)} CIDR blocks")

    # 确保输出目录存在
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 生成 Mikrotik 导入脚本
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(f"# Mikrotik CN IP List\n")
        f.write(f"# Generated from {SRC_URL}\n")
        f.write(f"# Updated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC\n\n")
        f.write("/ip firewall address-list\n")
        for cidr in cn_ips:
            f.write(f"add list=CN-IP address={cidr}\n")

    print(f"[+] Saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
