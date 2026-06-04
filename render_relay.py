import os
import requests
from flask import Flask, request, Response
import urllib3
import socket
import ssl
from requests.adapters import HTTPAdapter
from urllib3.poolmanager import PoolManager

# تعطيل تحذيرات SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__)

# ----------------------------------------------------------------------
# إعدادات الاتصال المباشر بـ Capital.com
# ----------------------------------------------------------------------
API_HOST = "api.capital.com"
API_IP = "185.105.144.130"
BASE_PATH = "/api/v1/"

# ----------------------------------------------------------------------
# محول HTTP مخصص يفرض اسم المضيف في SNI ويستخدم IP للاتصال
# ----------------------------------------------------------------------
class HostHeaderSSLAdapter(HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        kwargs['ssl_context'] = context
        return super().init_poolmanager(*args, **kwargs)

    def send(self, request, **kwargs):
        # حفظ اسم المضيف الأصلي
        original_host = request.headers.get('Host', API_HOST)
        # تغيير عنوان URL إلى IP مع الاحتفاظ بالمسار
        request.url = request.url.replace(
            f"https://{original_host}", f"https://{API_IP}"
        )
        # إجبار الاتصال على IP ولكن مع إرسال اسم المضيف الصحيح
        conn = self.get_connection(request.url, proxies=kwargs.get('proxies'))
        conn.host = API_IP
        conn.sock = None  # سيعاد إنشاؤه
        # نضبط الـ Host header
        request.headers['Host'] = API_HOST
        # تعطيل التحقق من SSL تماماً
        kwargs['verify'] = False
        return super().send(request, **kwargs)

# ----------------------------------------------------------------------
# تكوين جلسة requests مع المحول المخصص
# ----------------------------------------------------------------------
session = requests.Session()
session.mount("https://", HostHeaderSSLAdapter())
session.verify = False

# ----------------------------------------------------------------------
# بناء الرابط الكامل
# ----------------------------------------------------------------------
def build_url(endpoint: str) -> str:
    return f"https://{API_HOST}{BASE_PATH}{endpoint}"

# ----------------------------------------------------------------------
# فلترة الهيدرز
# ----------------------------------------------------------------------
def filter_headers(incoming):
    allowed = {"x-cap-api-key", "cst", "x-security-token", "content-type"}
    result = {}
    for k, v in incoming.items():
        if k.lower() in allowed:
            result[k] = v
    result["Host"] = API_HOST
    result["User-Agent"] = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    result["Accept"] = "application/json"
    return result

# ----------------------------------------------------------------------
# راوت البروكسي
# ----------------------------------------------------------------------
@app.route("/proxy/<path:endpoint>", methods=["GET", "POST"])
def proxy_request(endpoint):
    target_url = build_url(endpoint)
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

        # نبني الرد مع الحفاظ على الهيدرز المهمة
        response_headers = {}
        for k, v in resp.headers.items():
            # تجنب مشاكل تكرار الهيدر
            if k.lower() not in ('transfer-encoding', 'content-encoding', 'content-length'):
                response_headers[k] = v
        return Response(
            resp.content,
            status=resp.status_code,
            headers=response_headers
        )
    except requests.exceptions.SSLError as e:
        return {"proxy_error": f"SSL Error: {str(e)}"}, 502
    except requests.exceptions.ConnectionError as e:
        return {"proxy_error": f"Connection Error: {str(e)}"}, 502
    except requests.exceptions.Timeout:
        return {"proxy_error": "Upstream request timed out"}, 504
    except Exception as e:
        return {"proxy_error": f"Proxy internal error: {str(e)}"}, 500

# ----------------------------------------------------------------------
# Health check
# ----------------------------------------------------------------------
@app.route("/health")
def health():
    return {"status": "ok"}, 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
