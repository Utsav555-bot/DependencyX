import time
import subprocess
import sys
import httpx
import os

def probe():
    print("==================================================================")
    print("PHASE 1: APPLICATION EXECUTION & SERVER PROBING")
    print("==================================================================")

    # 1. Start FastAPI backend process
    print("\n[1/4] Starting FastAPI backend on http://127.0.0.1:8000 ...")
    backend_proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.app.main:app", "--host", "127.0.0.1", "--port", "8000"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=os.getcwd()
    )

    # 2. Start Next.js frontend process (using production next start or dev)
    print("[2/4] Starting Next.js frontend on http://127.0.0.1:3000 ...")
    frontend_proc = subprocess.Popen(
        ["npm.cmd", "run", "start"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=os.path.join(os.getcwd(), "frontend"),
        shell=True
    )

    # Give servers a few seconds to bind
    time.sleep(5)

    try:
        with httpx.Client(timeout=10.0) as client:
            # 3. Check Backend API Connectivity
            print("\n[3/4] Testing Backend API Connectivity:")
            api_endpoints = [
                "/api/health",
                "/docs",
                "/api/vulnerabilities",
            ]
            for ep in api_endpoints:
                url = f"http://127.0.0.1:8000{ep}"
                try:
                    res = client.get(url)
                    status_str = f"HTTP {res.status_code} OK" if res.status_code == 200 else f"HTTP {res.status_code}"
                    print(f"  --> {ep:<30} {status_str} (Size: {len(res.content)} bytes)")
                except Exception as e:
                    print(f"  --> {ep:<30} FAILED: {e}")

            # Authenticated check
            login_res = client.post("http://127.0.0.1:8000/api/auth/login", json={"email": "admin@dependencyx.io", "password": "Password123!"})
            if login_res.status_code == 200:
                token = login_res.json()["access_token"]
                auth_headers = {"Authorization": f"Bearer {token}"}
                protected_endpoints = [
                    "/api/projects",
                    "/api/risk/organization",
                    "/api/risk/critical-dependencies",
                    "/api/analytics/dashboard",
                    "/api/activity"
                ]
                for pep in protected_endpoints:
                    try:
                        res = client.get(f"http://127.0.0.1:8000{pep}", headers=auth_headers)
                        print(f"  --> {pep:<30} HTTP {res.status_code} OK (Protected)")
                    except Exception as e:
                        print(f"  --> {pep:<30} FAILED: {e}")

            # 4. Check Frontend Web Pages
            print("\n[4/4] Testing Next.js Frontend Page Loads:")
            frontend_pages = [
                "/",
                "/projects",
                "/graph",
                "/vulnerabilities",
                "/risk",
                "/analytics",
                "/reports",
                "/settings"
            ]
            for page in frontend_pages:
                url = f"http://127.0.0.1:3000{page}"
                try:
                    res = client.get(url)
                    status_str = f"HTTP {res.status_code} OK" if res.status_code == 200 else f"HTTP {res.status_code}"
                    print(f"  --> {page:<30} {status_str} (Length: {len(res.content)} bytes)")
                except Exception as e:
                    print(f"  --> {page:<30} FAILED: {e}")

    finally:
        print("\nStopping temporary test server instances...")
        backend_proc.terminate()
        frontend_proc.terminate()
        try:
            backend_proc.wait(timeout=2)
            frontend_proc.wait(timeout=2)
        except Exception:
            backend_proc.kill()
            frontend_proc.kill()
        print("Servers stopped cleanly.")

if __name__ == "__main__":
    probe()
