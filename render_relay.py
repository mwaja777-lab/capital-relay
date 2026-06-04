import os
import requests
from flask import Flask, request, Response

app = Flask(__name__)

# اسم المضيف الرسمي لـ Capital.com API
BASE_URL = "https://api.capital.com/api/v1/"

# جلسة طلبات عادية
session = requests.Session()

def filter_headers(incoming):
    allowed = {"x-cap-api-key", "cst", "x-security-token", "content-type"}
    result = {}
    for k, v in incoming.items():
        if k.lower() in allowed:
            result[k] = v
    result["User-Agent"] = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    result["Accept"] = "application/json"
    return result

@app.route("/proxy/<path:endpoint>", methods=["GET", "POST"])
def proxy_request(endpoint):
    target_url = f"{BASE_URL}{endpoint}"
    headers = filter_headers(request.headers)
    json_body = None
    if request.method == "POST":
        json_body = request.get_json(force=True, silent=True)
        if json_body is None:
            return {"proxy_error": "Invalid or missing JSON body"}, 400

    try:
        if request.method == "POST":
            resp = session.post(target_url, json=json_body, headers=headers, timeout=15)
        else:
            resp = session.get(target_url, headers=headers, timeout=15)

        return Response(
            resp.content,
            status=resp.status_code,
            headers=dict(resp.headers.items()),
        )
    except requests.exceptions.SSLError as e:
        return {"proxy_error": f"SSL Error: {str(e)}"}, 502
    except requests.exceptions.ConnectionError as e:
        return {"proxy_error": f"Connection Error: {str(e)}"}, 502
    except requests.exceptions.Timeout:
        return {"proxy_error": "Upstream request timed out"}, 504
    except Exception as e:
        return {"proxy_error": f"Internal error: {str(e)}"}, 500

@app.route("/health")
def health():
    return {"status": "ok"}, 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
