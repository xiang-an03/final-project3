import os
import json
import urllib.parse
import requests
from flask import Flask, render_template, request, jsonify

# 建立 Flask 應用程式實例
app = Flask(__name__, template_folder='../templates')

# =======================================================
# 🔒 從環境變數讀取最新金鑰，若讀不到則使用預設的真實金鑰
# =======================================================
API_KEY = os.getenv("GEMINI_API_KEY", "AQ.Ab8RN6KPZu63RbGtZtN4s62JCHjmqX2gCM-WOUwm_0AUGOEZiQ")

TAG_MAP = {
    "dog_style": "犬系風格長相", "cat_style": "貓系風格長相", "fox_style": "狐狸系風格長相",
    "single_eyelid": "單眼皮/內雙", "double_eyelid": "雙眼皮", "has_tearbags": "有臥蠶",
    "mbti_i": "MBTI 的 I 人 (內向型)", "mbti_e": "MBTI 的 E 人 (外向型)",
    "has_dimple": "有酒窩/梨渦", "baby_face": "圓臉/娃娃臉", "v_shape_face": "尖下巴/V臉", "high_cheekbones": "高顴骨",
    "tall": "身材高挑長腿", "petite": "身材嬌小", "fit": "身材精壯/有肌肉",
    "gentle": "溫柔內斂的個性", "humorous": "幽默風趣的個性", "cool": "高冷話少的個性", "cute": "可愛呆萌的個性",
    "singer": "歌手身分", "actor": "演員身分", "idol": "舞台偶像身分", "compose": "會音樂創作"
}

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/match', methods=['POST'])
def match_ideal_type():
    user_data = request.json
    gender_pref = "男性 (Male)" if user_data.get('q1') == 'male' else "女性 (Female)"
    raw_features = user_data.get('features', [])
    
    chinese_features = [TAG_MAP.get(f, f) for f in raw_features]
    features_str = "、".join(chinese_features) if chinese_features else "未特別指定"

    prompt = f"""
    你是全球娛樂圈的大數據專家。請根據使用者的理想型條件，從【亞洲地區】（包含台灣、韓國、日本、中國大陸、香港）挑選出一位最完美符合的真實知名藝人明星。

    使用者期望條件：
    - 性別偏好：{gender_pref} 的亞洲明星
    - 必須具備特徵：{features_str}

    請挑選出一位最符合以上所有特徵的真實亞洲明星。
    必須嚴格遵守以下 JSON 格式回傳，不要包含任何額外的 Markdown 標記（如 ```json）：
    {{
        "name": "明星姓名",
        "score": "契合度百分比(例如95%)",
        "summary": "一段100字左右的客製化推薦語，說明為什麼這位明星完美符合他挑選的特徵。"
    }}
    """

    # 🌐 絕對純淨的 API 請求路徑（已徹底洗白）
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}"
    # 📝 宣告標頭（確保絕對定義，修復 name 'headers' is not defined 錯誤）
    headers = {"Content-Type": "application/json"}
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }

    try:
        # 發送 POST 請求
        response = requests.post(url, headers=headers, json=payload)
        response_data = response.json()
        
        # 🛡️ 安全防禦機制 1：如果 Google 伺服器回傳明確錯誤（例如金鑰未授權、配額上限）
        if 'error' in response_data:
            return jsonify({"message": f"Google Gemini 拒絕了請求。原因: {response_data['error'].get('message', '未知錯誤')}"}), 400
            
        # 🛡️ 安全防禦機制 2：如果回傳結構怪異，缺少關鍵的 candidates
        if 'candidates' not in response_data or not response_data['candidates']:
            return jsonify({"message": f"Gemini 沒有正常回應內容。完整回應日誌: {json.dumps(response_data)}"}), 500
            
        # 正常解析流程
        raw_text = response_data['candidates'][0]['content']['parts'][0]['text']
        clean_text = raw_text.replace("```json", "").replace("```", "").strip()
        result_data = json.loads(clean_text)
        
        # 動態產生該明星的社群與搜尋連結
        encoded_name = urllib.parse.quote(result_data['name'])
        result_data['instagram_url'] = f"[https://www.instagram.com/explore/tags/](https://www.instagram.com/explore/tags/){encoded_name}/"
        result_data['photo_url'] = f"[https://www.google.com/search?tbm=isch&q=](https://www.google.com/search?tbm=isch&q=){encoded_name}"
        result_data['wikipedia_url'] = f"[https://zh.wikipedia.org/wiki/](https://zh.wikipedia.org/wiki/){encoded_name}"
        
        return jsonify(result_data)

    except Exception as e:
        return jsonify({"message": f"系統內部處理發生錯誤，請稍後再試！(詳細原因: {str(e)})"}), 500

# 🔒 Vercel 雲端平台必備的進入點映射
handler = app
application = app

if __name__ == '__main__':
    app.run(debug=True, port=5000)