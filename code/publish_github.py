#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将本项目发布到 GitHub —— 无需本机 git 二进制。

使用 GitHub REST API v3 + Personal Access Token（scope: repo）。
适合本机未安装 git、或 WorkBuddy 内置 GitHub 连接器仅有只读权限（403）的场景。

用法（PowerShell）：
    $env:GITHUB_TOKEN = "ghp_xxxxxxxxxxxx"
    python code/publish_github.py

说明：
    - 自动跳过体积过大且可由 run_all.py 再生的大文件：
        data/raw/raw_corpus.jsonl（约 8.6MB）
        data/interim/tokens.jsonl（约 10.9MB）
      这两个文件在克隆仓库后运行 `python code/run_all.py` 会自动重新生成。
    - 其余文件（代码、论文 docx、结果表 xlsx、图表、说明文档）一次性推送为一个 commit。
    - 默认仓库名 thesis-digital-transformation-nlp，owner 从环境变量 GITHUB_OWNER 读取（默认 Sherry-at625）。
"""
import os
import sys
import json
import base64
import argparse
import urllib.request
import urllib.parse
import urllib.error
import ssl

API = "https://api.github.com"
# 绕过证书校验（部分企业网络环境需要）
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE


def api(method, path, token, body=None):
    url = API + path
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    # Bearer 对 classic(ghp_) 与 fine-grained(github_pat_) 两种 PAT 都通用
    req.add_header("Authorization", "Bearer " + token)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "workbuddy-publisher")
    if data is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=90) as r:
            txt = r.read().decode("utf-8")
            return r.status, (json.loads(txt) if txt else {})
    except urllib.error.HTTPError as e:
        txt = e.read().decode("utf-8", "ignore")
        try:
            err = json.loads(txt)
        except Exception:
            err = {"message": txt}
        return e.code, err


# 跳过：过大且可复现的中间文件
EXCLUDE = {
    "data/raw/raw_corpus.jsonl",
    "data/interim/tokens.jsonl",
}
SKIP_DIRS = {".git", "__pycache__", ".workbuddy"}


def collect_files(root):
    out = []
    for dp, dns, fns in os.walk(root):
        dns[:] = [d for d in dns if d not in SKIP_DIRS]
        for fn in fns:
            full = os.path.join(dp, fn)
            rel = os.path.relpath(full, root).replace(os.sep, "/")
            if rel in EXCLUDE:
                print("  [跳过大文件]", rel)
                continue
            out.append((rel, full))
    return sorted(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default="thesis-digital-transformation-nlp")
    ap.add_argument("--owner", default=None, help="不填则自动取当前登录账号")
    ap.add_argument("--public", action="store_true", default=True)
    ap.add_argument("--private", dest="public", action="store_false")
    args = ap.parse_args()

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("ERROR: 请先设置环境变量 GITHUB_TOKEN（GitHub Personal Access Token，scope=repo）。")
        print("PowerShell 示例： $env:GITHUB_TOKEN = \"ghp_xxxx\"")
        sys.exit(1)

    # 0. 获取当前认证用户，作为仓库归属（避免 owner 填错导致推送失败）
    s0, me = api("GET", "/user", token)
    auth_login = me.get("login") if s0 == 200 else None
    owner = args.owner or auth_login or os.environ.get("GITHUB_OWNER", "Sherry-at625")
    args.owner = owner

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # 1. 创建仓库（已存在则忽略）
    status, resp = api("POST", "/user/repos", token, {
        "name": args.repo,
        "description": "基于年报文本分析的企业数字化转型测度及其对创新绩效的影响研究（本科毕业论文预演稿 + 可复现 NLP 五步流水线）",
        "private": not args.public,
        "auto_init": False,
    })
    if status == 201:
        print("✓ 仓库已创建:", resp.get("html_url"))
    elif status == 422 and "already exists" in str(resp.get("message", "")).lower():
        print("· 仓库已存在，继续推送")
    else:
        print("创建仓库返回:", status, resp.get("message", ""))
        # 即便创建报错也可能已存在，继续尝试推送

    # 2. 用 Contents API 逐文件提交（空仓库时首个 PUT 会自动初始化）
    files = collect_files(root)
    print(f"\n准备推送 {len(files)} 个文件 ...")
    ok = 0
    commit_msg = "论文材料：五步流水线代码 + 毕业论文 + 测度结果表 + 图表 + 说明"
    for rel, full in files:
        with open(full, "rb") as f:
            content = f.read()
        if len(content) > 900 * 1024:
            print(f"  [跳过>900KB] {rel} ({len(content)} bytes)")
            continue
        b64 = base64.b64encode(content).decode("ascii")
        path_enc = urllib.parse.quote(rel)
        s, r = api("PUT", f"/repos/{args.owner}/{args.repo}/contents/{path_enc}", token, {
            "message": commit_msg,
            "content": b64,
            "encoding": "base64",
        })
        if s in (200, 201):
            ok += 1
            print(f"  ✓ {rel} ({len(content)} bytes)")
        else:
            print(f"  ✗ 失败 {rel}: {s} {r.get('message', '')}")
            sys.exit(1)

    print(f"\n✓ 发布完成！共推送 {ok} 个文件。")
    print(f"  仓库地址: https://github.com/{args.owner}/{args.repo}")


if __name__ == "__main__":
    main()
