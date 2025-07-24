pr# app.py (Python Flask Backend)

from flask import Flask, request, jsonify
from flask_cors import CORS
import requests # تأكدي من تثبيت requests: pip install requests
import os # لاستخدام متغيرات البيئة (اختياري، ولكن أفضل للأمان)

app = Flask(__name__)
CORS(app) # تمكين CORS لجميع المسارات

# تخزين مؤقت للرسائل في الذاكرة (لأغراض الاختبار)
# الرسائل ستفقد عند إعادة تشغيل الخادم
messages = []

# ******** معلومات WhatsApp Cloud API (مهمة جداً) ********
# يفضل تخزينها كمتغيرات بيئة لأسباب أمنية
# يمكنكِ وضعها مباشرة هنا لأغراض الاختبار، لكن كوني حذرة جداً
# ACCESS_TOKEN = os.environ.get("WHATSAPP_ACCESS_TOKEN", "YOUR_ACCESS_TOKEN_HERE")
# PHONE_NUMBER_ID = os.environ.get("WHATSAPP_PHONE_NUMBER_ID", "YOUR_PHONE_NUMBER_ID_HERE")

# لأغراض هذا المشروع التجريبي، سنضعها مباشرة هنا:
ACCESS_TOKEN = "EAAY5oaelFCMBPGpEAZBv8zeQq5P7ZAvj31sIzu3IasVCsaOn38YH4yETZAnhcXAZCauXfZAyHgryTdl9sTkReOg6eBONVsS8RyOFM397DXV02swH5Gqxp1z2pIieIJq1YAVByhYb0UN5ZCzoOLxnLOkFhM1FEs2wQrwrM3mv9t6yxZBe88Lwpp9asuxbooI4wtJrZAtPhqSebMmNBfU6tZB9jOpnqvWRGd3MRLmr0I8hMFAESNAZDZD" # الـ Access Token الذي قدمتيه
PHONE_NUMBER_ID = "669480912922601" # <--- يجب عليكِ استبدال هذا بمعرف رقم هاتفكِ من Meta Developers

VERIFY_TOKEN = 'super_secret_whatsapp' # يجب أن يطابق هذا التوكن في إعدادات Meta

# الـ Webhook الخاص بواتساب (لاستقبال الرسائل)
@app.route('/whatsapp-webhook', methods=['GET', 'POST'])
def whatsapp_webhook():
    if request.method == 'GET':
        # التحقق من الويب هوك
        mode = request.args.get('hub.mode')
        token = request.args.get('hub.verify_token')
        challenge = request.args.get('hub.challenge')

        if mode == 'subscribe' and token == VERIFY_TOKEN:
            print("✅ Webhook verified from WhatsApp")
            return challenge, 200
        else:
            print("❌ Webhook verification failed: Invalid mode or token.")
            return 'Forbidden', 403

    elif request.method == 'POST':
        # استقبال الرسائل
        data = request.get_json()
        print("Received webhook body:", data)

        # معالجة الـ payload
        if data and data.get('object') == 'whatsapp_business_account':
            for entry in data.get('entry', []):
                for change in entry.get('changes', []):
                    value = change.get('value', {})

                    if change.get('field') == 'messages':
                        # معالجة الرسائل الواردة
                        if value.get('messages') and isinstance(value['messages'], list):
                            for message_object in value['messages']:
                                sender = message_object.get('from')
                                content = ""
                                message_type = message_object.get('type')

                                if message_type == 'text':
                                    content = message_object['text']['body']
                                elif message_type == 'image':
                                    content = "صورة"
                                elif message_type == 'video':
                                    content = "فيديو"
                                elif message_type == 'audio':
                                    content = "مقطع صوتي"
                                else:
                                    content = f"رسالة من نوع: {message_type}"
                                
                                # إضافة الرسالة إلى التخزين المؤقت
                                messages.append({
                                    "sender": sender,
                                    "content": content,
                                    "timestamp": message_object.get('timestamp'),
                                    "type": message_type
                                })
                                print(f"✨ New message from {sender}: {content}")
                        else:
                            print("Webhook payload: 'value.messages' is missing or not a list.", value)
                    elif change.get('field') == 'statuses':
                        # معالجة إشعارات الحالة (تم التسليم، تم القراءة، إلخ)
                        if value.get('statuses') and isinstance(value['statuses'], list):
                            for status_object in value['statuses']:
                                print(f"Status update for message ID {status_object.get('id')}: {status_object.get('status')} to {status_object.get('recipient_id')}")
                        else:
                            print("Webhook payload: 'value.statuses' is missing or not a list.", value)
        return jsonify({'success': True}), 200

# مسار لجلب الرسائل المخزنة (تستخدمه الواجهة الأمامية للعرض)
@app.route('/api/messages', methods=['GET'])
def get_messages():
    print(f"Serving {len(messages)} messages from Flask in-memory storage.")
    return jsonify(messages), 200

# ******** مسار جديد لإرسال الرسائل (تستخدمه الواجهة الأمامية للإرسال) ********
@app.route('/send-message', methods=['POST'])
def send_message():
    data = request.get_json()
    recipient_phone_number = data.get('to') # رقم المستلم
    message_content = data.get('message') # محتوى الرسالة

    if not recipient_phone_number or not message_content:
        return jsonify({'error': 'Recipient phone number and message content are required.'}), 400

    # نقطة نهاية WhatsApp Cloud API لإرسال الرسائل
    whatsapp_api_url = f"https://graph.facebook.com/v19.0/{669480912922601}/messages"
    
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "messaging_product": "whatsapp",
        "to": recipient_phone_number,
        "type": "text",
        "text": {
            "body": message_content
        }
    }

    try:
        response = requests.post(whatsapp_api_url, headers=headers, json=payload)
        response.raise_for_status() # ترفع استثناء لأخطاء HTTP (4xx أو 5xx)
        whatsapp_response = response.json()
        print("WhatsApp API response:", whatsapp_response)

        # يمكنكِ هنا إضافة الرسالة المرسلة إلى قائمة الرسائل في الذاكرة أيضاً
        # messages.append({
        #     "sender": "Me", # أو رقم هاتفكِ الخاص
        #     "content": message_content,
        #     "timestamp": datetime.now().isoformat(),
        #     "type": "text"
        # })

        return jsonify({'success': True, 'whatsapp_response': whatsapp_response}), 200
    except requests.exceptions.RequestException as e:
        print(f"Error sending message via WhatsApp API: {e}")
        return jsonify({'error': f'Failed to send message: {e}'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
