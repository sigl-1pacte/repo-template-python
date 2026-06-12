"""Intentionally vulnerable examples to validate CodeQL alerts.

Do not keep this file in production repositories. It exists only to confirm that
CodeQL detects dangerous data flow from user-controlled input to risky sinks.
"""

import sqlite3
import subprocess

from fastapi import APIRouter

router = APIRouter()


@router.get("/demo/search")
def search_users(username: str):
    connection = sqlite3.connect("users.db")
    cursor = connection.cursor()

    query = f"SELECT id, username FROM users WHERE username = '{username}'"
    cursor.execute(query)

    return {"users": cursor.fetchall()}


@router.get("/demo/ping")
def ping_host(host: str):
    result = subprocess.run(
        f"ping -c 1 {host}",
        shell=True,
        capture_output=True,
        text=True,
        check=False,
    )

    return {"output": result.stdout}
