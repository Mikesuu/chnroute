#!/usr/bin/env python3
import urllib.request
import ipaddress
import sys
import os
import socket

# -------------------------- 配置 (CONFIGURATION) --------------------------
# 远程下载的 IP 地址源文件 URL
URL = "https://raw.githubusercontent.com/zhiyi7/gfw-pac/master/cidrs-cn.txt"

# 输出目录与文件
OUTPUT_DIR = "mikrotik"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "cnip.rsc")

# Mikrotik 地址列表名
LIST_NAME = "CN"

# 默认注释 (用于从 URL 下载的 IP 条目)
COMMENT_DEFAULT = "CN"

# 内网网段及其注释
LOCAL_NETS = {
    "10.10.10.0/25": "intranet",
    # 可以添加更多内网网段
}

# 需要解析的域名及其注释
DOMAINS = {
    "speedtest.net": "speedtest",
    "www.speedtest.net": "speedtest",
    "ookla.net": "speedtest",
    "www.ookla.net": "speedtest"
}
# -------------------------------------------------------------------------


def is_valid_cidr(cidr):
    """检查 CIDR 格式是否正确"""
    try:
        ipaddress.ip_network(cidr, strict=False)
        return True
    except Exception:
        return False

def resolve_domains(domains: dict):
    """解析域名，返回 IPv4/IPv6 地址及其注释的字典"""
    cidrs_with_comments = {}
    for domain, comment in domains.items():
        try:
            infos = socket.getaddrinfo(domain, None)
            for info in infos:
                addr = info[4][0]
                # IPv6 地址需要 /128
                if ":" in addr:
                    cidr = addr + "/128"
                # IPv4 地址需要 /32
                else:
                    cidr = addr + "/32"
                
                # 使用解析得到的 IP 地址作为键，原始注释作为值
                cidrs_with_comments[cidr] = comment
        except Exception as e:
            print(f"⚠️ 无法解析域名 {domain}: {e}", file=sys.stderr)
    return cidrs_with_comments

def main():
    # 创建输出目录
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # -------------------------- 1. 下载和处理 CIDR 列表 --------------------------
    print(f"🌐 正在从 {URL} 获取 CIDR 列表...")
    remote_cidrs_with_comments = {}
    try:
        with urllib.request.urlopen(URL) as response:
            lines = response.read().decode('utf-8').splitlines()
    except Exception as e:
        print(f"❌ 错误: 无法获取数据: {e}", file=sys.stderr)
        sys.exit(1)

    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        if is_valid_cidr(line):
            # 添加默认注释
            remote_cidrs_with_comments[line] = COMMENT_DEFAULT
        else:
            print(f"⚠️ 已跳过无效的 CIDR 条目: {line}", file=sys.stderr)

    # -------------------------- 2. 整合所有 IP 条目 --------------------------
    
    # 添加内网网段 (LOCAL_NETS)
    remote_cidrs_with_comments.update(LOCAL_NETS)

    # 解析域名 (DOMAINS)
    domain_cidrs_with_comments = resolve_domains(DOMAINS)
    remote_cidrs_with_comments.update(domain_cidrs_with_comments)
    
    all_cidrs = list(remote_cidrs_with_comments.keys())

    if not all_cidrs:
        print("❌ 错误: 未找到任何有效的 CIDR 条目!", file=sys.stderr)
        sys.exit(1)

    # -------------------------- 3. 排序和写入文件 --------------------------
    
    # 排序 (IPv4 在前，IPv6 在后)
    def sort_key(cidr):
        net = ipaddress.ip_network(cidr, strict=False)
        # 将 IPv6 排序键设置为 1 (靠后)，IPv4 设为 0 (靠前)
        return (int(net.version == 6), net)

    sorted_cidrs = sorted(all_cidrs, key=sort_key)

    # 写入 Mikrotik 可导入的 .rsc 文件
    try:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            
            # --- IPv4 写入 ---
            f.write(f"# -------------------- IPv4 地址列表 ({LIST_NAME}) --------------------\n")
            f.write("/ip firewall address-list\n")
            
            ipv4_count = 0
            for cidr in sorted_cidrs:
                net = ipaddress.ip_network(cidr, strict=False)
                if net.version == 4:
                    comment = remote_cidrs_with_comments.get(cidr, COMMENT_DEFAULT)
                    f.write(f"add address={cidr} list={LIST_NAME} comment=\"{comment}\"\n")
                    ipv4_count += 1
            
            # --- IPv6 写入 ---
            f.write(f"\n# -------------------- IPv6 地址列表 ({LIST_NAME}) --------------------\n")
            f.write("/ipv6 firewall address-list\n")
            
            ipv6_count = 0
            for cidr in sorted_cidrs:
                net = ipaddress.ip_network(cidr, strict=False)
                if net.version == 6:
                    comment = remote_cidrs_with_comments.get(cidr, COMMENT_DEFAULT)
                    f.write(f"add address={cidr} list={LIST_NAME} comment=\"{comment}\"\n")
                    ipv6_count += 1

        print(f"✅ 成功写入文件: {OUTPUT_FILE}")
        print(f"📊 总条目数: {ipv4_count + ipv6_count} (IPv4: {ipv4_count}, IPv6: {ipv6_count})")
        
    except Exception as e:
        print(f"❌ 错误: 写入文件失败: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
