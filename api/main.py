import os
import json
import urllib.parse
import requests
from flask import Flask, render_template, request, jsonify

app = Flask(__name__, template_folder='../templates')

# =======================================================
# 🔒 讀取你們最新的 AQ. 開頭金鑰
# =======================================================
API_KEY = os.getenv("GEMINI_API_KEY", "AQ.Ab8RN6KPZu63RbGtZtN4s62JCHjmqX2gCM-WOUwm_0AUGOEZiQ")

TAG_MAP = {
    "dog_style": "犬系風格長相", "cat_style": "貓系風格長相", "fox_style": "狐狸系風格長相",
    "single_eyelid": "單眼皮/內雙", "double_eyelid": "雙眼皮", "has_tearbags": "有臥蠶",
    "mbti_i": "MBTI 的 I 人 (內向型)", "mbti_e": "MBTI 的 E 人 (外向型)",
    "has_dimple": "有酒窩/梨渦", "baby_face": "圓臉/娃娃結構", "v_shape_face": "尖下巴/V臉", "high_cheekbones": "高顴骨",
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
    你是全球娛樂圈的大數據專家。請根據使用者的理想型條件，從【亞洲地區】挑選出一位最完美符合的真實知名藝人明星。

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

    # 🌐 使用純網址 HTTP 請求，完全繞過 SDK 衝突
    # 🌐 乾乾淨淨的網址，不帶任何中括號或奇怪的符號
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}"
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        response_data = response.json()
        
        # 解析 Gemini 回傳的原始文字
        raw_text = response_data['candidates'][0]['content']['parts'][0]['text']
        
        # 清理可能夾雜的 markdown 語法
        clean_text = raw_text.replace("```json", "").replace("```", "").strip()
        result_data = json.loads(clean_text)
        
        # 加上超連結資訊
        encoded_name = urllib.parse.quote(result_data['name'])
        result_data['instagram_url'] = f"[https://www.instagram.com/explore/tags/](https://www.instagram.com/explore/tags/){encoded_name}/"
        result_data['photo_url'] = f"[https://www.google.com/search?tbm=isch&q=](https://www.google.com/search?tbm=isch&q=){encoded_name}"
        result_data['wikipedia_url'] = f"[https://zh.wikipedia.org/wiki/](https://zh.wikipedia.org/wiki/){encoded_name}"
        
        return jsonify(result_data)

    except Exception as e:
        return jsonify({"message": f"系統運算發生錯誤，請稍後再試！(詳細原因: {str(e)})"}), 500

handler = app

if __name__ == '__main__':
    app.run(debug=True, port=5000)