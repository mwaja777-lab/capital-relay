import os, requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# الرابط الرسمي والآمن لمنصة كابيتال
URL = "https://api.capital.com/api/v1/"

@app.route('/proxy/<path:ep>', methods=['GET', 'POST'])
def proxy(ep):
    t_url = f"{URL}{ep}"
    
    # تنسيق الهيدرز وتضمين الـ User-Agent الذكي لحمايتنا من الحظر السحابي
    hdrs = {k: v for k, v in request.headers.items() if k.lower() in ['x-cap-api-key', 'cst', 'x-security-token', 'content-type']}
    hdrs['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    hdrs['Accept'] = 'application/json'
    
    try:
        if request.method == 'POST':
            r = requests.post(t_url, json=request.get_json(silent=True), headers=hdrs, verify=True)
        else:
            r = requests.get(t_url, headers=hdrs, verify=True)
        return (r.text, r.status_code, r.headers.items())
    except Exception as e:
        # التقاط الخطأ وإرجاعه كـ JSON بدون انهيار السيرفر
        return jsonify({"error": str(e)}), 500
        
