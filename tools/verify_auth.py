#!/usr/bin/env python3
"""
离线验证 A1 鉴权算法:token == AES-128-CBC(deviceSecret[:16], iv=key, random) ?

算法已通过两组真实抓包 (random, token) 配对反推确认(见 FINDINGS.md 第 9 节):
    token = AES-128-CBC(key=deviceSecret[:16] ascii, iv=key, pt=random ascii).hex()

本脚本不内置任何真实密钥/抓包数据 —— 那些是设备特定的敏感信息,存在本地的
extract/verify_pairs.json(已被 .gitignore 排除)。示例格式见 verify_pairs.example.json。

用法:
    python verify_auth.py [pairs_json_path]   # 默认读 extract/verify_pairs.json
"""
import sys
import os
import json
from Crypto.Cipher import AES


def compute_token(device_secret: str, random_hex: str) -> str:
    key = device_secret[:16].encode()
    iv = key
    pt = random_hex.encode()
    return AES.new(key, AES.MODE_CBC, iv).encrypt(pt).hex()


def main():
    default_path = os.path.join(os.path.dirname(__file__), "..", "extract", "verify_pairs.json")
    path = sys.argv[1] if len(sys.argv) > 1 else default_path

    if not os.path.exists(path):
        print(f"!! 找不到凭据文件: {path}")
        print("   参考 tools/verify_pairs.example.json 的格式自行创建"
              "(内容为设备特定敏感信息,不应提交到仓库)")
        return 1

    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    secret = data["deviceSecret"]
    pairs = data["pairs"]

    print(f"deviceSecret 长度 = {len(secret)} 字符\n")
    all_ok = True
    for i, pair in enumerate(pairs):
        got = compute_token(secret, pair["random"])
        ok = got == pair["token"].lower()
        all_ok &= ok
        print(f"配对{i}: {'MATCH' if ok else 'FAIL'}")
        if not ok:
            print(f"   期望 {pair['token']}")
            print(f"   计算 {got}")

    print()
    print("全部匹配 -> 离线鉴权算法验证通过" if all_ok else "存在不匹配,算法或数据有误")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
