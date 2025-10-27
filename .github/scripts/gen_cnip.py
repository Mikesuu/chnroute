import requests
from datetime import datetime

SRC_URL = "https://raw.githubusercontent.com/zhiyi7/gfw-pac/master/gfwlist/cn.txt"
OUTPUT_FILE = "mikrotik/cnip.rsc"

def main():
    print("[+] Downloading CN IP data from gfw-pac...")
    r = requests.get(SRC_URL)
    r.raise_for_status()
    lines = r.text.splitlines()

    # 过滤空行与无效行
    cn_ips = [line.strip() for line in lines if line.strip() and not line.startswith("#")]

    # 添加本地网段
    cn_ips.append("10.10.10.0/25")

    print(f"[+] Total {len(cn_ips)} CIDR blocks")

    # 生成 Mikrotik 脚本格式
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(f"# CN IP list for Mikrotik\n# Updated: {datetime.utcnow()} UTC\n\n")
        f.write("/ip firewall address-list\n")
        for cidr in cn_ips:
            f.write(f"add list=CN-IP address={cidr}\n")

    print(f"[+] Saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
