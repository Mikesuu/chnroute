#!/usr/bin/env python3
import urllib.request
import ipaddress
import sys
import os

# 下载的源文件
URL = "https://raw.githubusercontent.com/zhiyi7/gfw-pac/master/cidrs-cn.txt"

# 输出目录与文件
OUTPUT_DIR = "mikrotik"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "cnip.rsc")

# Mikrotik 列表名
LIST_NAME = "CN"

def is_valid_cidr(cidr):
    """检查 CIDR 格式是否正确"""
    try:
        ipaddress.ip_network(cidr, strict=False)
        return True
    except Exception:
        return False

def main():
    # 创建输出目录
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print(f"🌐 Fetching CIDR list from: {URL}")
    try:
        with urllib.request.urlopen(URL) as response:
            lines = response.read().decode('utf-8').splitlines()
    except Exception as e:
        print(f"❌ Error fetching data: {e}", file=sys.stderr)
        sys.exit(1)

    valid_cidrs = []
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        if is_valid_cidr(line):
            valid_cidrs.append(line)
        else:
            print(f"⚠️  Skipped invalid CIDR: {line}", file=sys.stderr)

    if not valid_cidrs:
        print("❌ No valid CIDRs found!", file=sys.stderr)
        sys.exit(1)

    # 排序（IPv4 在前，IPv6 在后）
    def sort_key(cidr):
        net = ipaddress.ip_network(cidr, strict=False)
        return (int(net.version == 6), net)

    sorted_cidrs = sorted(valid_cidrs, key=sort_key)

    # 写入 Mikrotik 可导入的 .rsc 文件
    try:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            # IPv4
            f.write("/ip firewall address-list\n")
            for cidr in sorted_cidrs:
                net = ipaddress.ip_network(cidr, strict=False)
                if net.version == 4:
                    f.write(f"/ip firewall address-list add address={cidr} list={LIST_NAME}\n")
            # IPv6
            f.write("/ipv6 firewall address-list\n")
            for cidr in sorted_cidrs:
                net = ipaddress.ip_network(cidr, strict=False)
                if net.version == 6:
                    f.write(f"/ipv6 firewall address-list add address={cidr} list={LIST_NAME}\n")

        print(f"✅ Successfully wrote {len(sorted_cidrs)} entries to {OUTPUT_FILE}")
        print(f"📂 Output file: {OUTPUT_FILE}")

    except Exception as e:
        print(f"❌ Error writing file: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
