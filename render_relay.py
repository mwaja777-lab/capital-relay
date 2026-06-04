URL = "https://185.105.144.131/api/v1/"
@app.route('/proxy/path:ep', methods=['GET', 'POST'])
def proxy(ep):
t_url = f"{URL}{ep}"
hdrs = {k: v for k, v in request.headers.items() if k.lower() in ['x-cap-api-key', 'cst', 'x-security-token', 'content-type']}
# تمرير الـ Host الأساسي لإعلام خادم كابيتال بوجهتنا
hdrs['Host'] = 'api.capital.com'
try:
if request.method == 'POST':
# إضافة verify=False لمنع الـ Crash بسبب شهادة الـ IP
r = requests.post(t_url, json=request.get_json(silent=True), headers=hdrs, verify=False)
else:
r = requests.get(t_url, headers=hdrs, verify=False)
return (r.text, r.status_code, r.headers.items())
except Exception as e:
return jsonify({"error": str(e)}), 500
if name == 'main':
port = int(os.environ.get("PORT", 5000))
app.run(host="0.0.0.0", port=port)
