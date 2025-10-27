#!/usr/bin/env python3
import urllib.request
import ipaddress
import sys

# 数据源 URL（raw 链接）
URL = "https://raw.githubusercontent.com/zhiyi7/gfw-pac/master/cidrs-cn.txt"
OUTPUT_FILE = "mikrotik/cnip.rsc"
LIST_NAME = "CN"

def is_valid_cidr(cidr):
    """检查是否为有效的 IPv4 或 IPv6 CIDR"""
    try:
        ipaddress.ip_network(cidr, strict=False)
        return True
    except ValueError:
        return False

def main():
    try:
        print(f"Fetching CIDR list from: {URL}")
        with urllib.request.urlopen(URL) as response:
            lines = response.read().decode('utf-8').splitlines()
    except Exception as e:
        print(f"Error fetching data: {e}", file=sys.stderr)
        sys.exit(1)

    valid_cidrs = []
    for line in lines:
        line = line.strip()
        # 跳过空行和注释
        if not line or line.startswith('#'):
            continue
        if is_valid_cidr(line):
            valid_cidrs.append(line)
        else:
            print(f"Warning: invalid CIDR skipped: {line}", file=sys.stderr)

    if not valid_cidrs:
        print("No valid CIDRs found!", file=sys.stderr)
        sys.exit(1)

    # 写入 MikroTik .rsc 文件
    try:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            for cidr in sorted(valid_cidrs, key=lambda x: ipaddress.ip_network(x, strict=False)):
                f.write(f"add address={cidr} list={LIST_NAME}\n")
        print(f"✅ Successfully generated {len(valid_cidrs)} entries to {OUTPUT_FILE}")
    except Exception as e:
        print(f"Error writing file: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
