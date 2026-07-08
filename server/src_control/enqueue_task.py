#!/usr/bin/env python3
"""Постановка задания в очередь (CLI оператора)."""

import argparse
import base64
import json
import sys

import requests


def main():
  p = argparse.ArgumentParser(description="Постановка задания агенту")
  p.add_argument("--server", default="http://127.0.0.1:1337")
  p.add_argument("--agent", type=int, required=True)
  p.add_argument("--task", required=True)
  p.add_argument("--user", default="admin")
  p.add_argument("--password", default="password")
  a = p.parse_args()
  auth = base64.b64encode(f"{a.user}:{a.password}".encode()).decode()
  r = requests.post(
    f"{a.server}/api/task/{a.agent}",
    headers={"Authorization": f"Basic {auth}", "Content-Type": "application/json"},
    data=json.dumps({"task": a.task}),
    timeout=15,
  )
  print(r.status_code, r.text)
  sys.exit(0 if r.ok else 1)


if __name__ == "__main__":
  main()
