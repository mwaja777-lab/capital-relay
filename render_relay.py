import os, requests
from flask import Flask, request, jsonify
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
app = Flask(__name__)

# استخدام الآي بي الرقمي المباشر لـ Capital.com لتخطي مشكلة الـ DNS بالسحاب
URL = "https://185.105.144.130/api/v1/"

@app.route('/proxy/<path:ep>', methods=['GET', 'POST'])
def proxy(ep):
    t_url = f"{URL}{ep}"
    hdrs = {k: v for k, v in request.headers.items() if k.lower() in ['x-cap-api-key', 'cst', 'x-security-token', 'content-type']}
    hdrs['Host'] = 'api.capital.com'
    try:
        if request.method == 'POST':
            r = requests.post(t_url, json=request.get_json(silent=True), headers=hdrs, verify=False)
        else:
            r = requests.get(t_url, headers=hdrs, verify=False)
        return (r.text, r.status_code, r.headers.items())
    except Exception as e:
        return jsonify({"error": str(e)}), 500
        
