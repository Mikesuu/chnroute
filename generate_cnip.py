#!/usr/bin/env python3
import urllib.request
import ipaddress
import sys
import os

URL = "https://raw.githubusercontent.com/zhiyi7/gfw-pac/master/cidrs-cn.txt"
OUTPUT_DIR = "mikrotik"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "cnip.rsc")
LIST_NAME = "CN"

def is_valid_cidr(cidr):
    try:
        ipaddress.ip_network(cidr, strict=False)
        return True
    except Exception:
        return False

def main():
    # 创建输出目录
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print(f"Fetching CIDR list from: {URL}")
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

    # 排序：IPv4 在前，IPv6 在后，各自按网络地址排序
    def sort_key(cidr):
        net = ipaddress.ip_network(cidr, strict=False)
        return (int(net.version == 6), net)

    sorted_cidrs = sorted(valid_cidrs, key=sort_key)

    # 写入文件
    try:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            for cidr in sorted_cidrs:
                f.write(f"add address={cidr} list={LIST_NAME}\n")
        print(f"✅ Successfully wrote {len(sorted_cidrs)} entries to {OUTPUT_FILE}")
    except Exception as e:
        print(f"❌ Error writing file: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
