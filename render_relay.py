import os, requests
from flask import Flask, request, jsonify
app = Flask(__name__)
URL = "https://api-api.capital.com/api/v1/"
@app.route('/proxy/<path:ep>', methods=['GET', 'POST'])
def proxy(ep):
    t_url = f"{URL}{ep}"
    hdrs = {k: v for k, v in request.headers.items() if k.lower() in ['x-cap-api-key', 'cst', 'x-security-token', 'content-type']}
    try:
        if request.method == 'POST':
            r = requests.post(t_url, json=request.get_json(silent=True), headers=hdrs)
        else:
            r = requests.get(t_url, headers=hdrs)
        return (r.text, r.status_code, r.headers.items())
    except Exception as e:
        return jsonify({"error": str(e)}), 500
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
  
