<div align="center">

# 🕌 نظام إدارة مركز تحفيظ القرآن الكريم

![Django](https://img.shields.io/badge/Django-5.2-green?style=for-the-badge&logo=django)
![Python](https://img.shields.io/badge/Python-3.10-blue?style=for-the-badge&logo=python)
![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3-purple?style=for-the-badge&logo=bootstrap)
![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)

نظام متكامل لإدارة مراكز تحفيظ القرآن الكريم — تسجيل الطلاب،
إدارة القاعات، الحضور، التقييمات، وخدمة الباص.

**[🌐 عرض مباشر](https://drmgamal.pythonanywhere.com)**

</div>

---

## ✨ المميزات

- 👤 **إدارة المستخدمين** — أدوار متعددة (مدير، مشرف، معلم، ولي أمر)
- 🎓 **إدارة الطلاب** — تسجيل، تسكين تلقائي، نقل بين القاعات
- 🏫 **إدارة القاعات** — فئات عمرية، جداول، طاقة استيعابية
- 📅 **الحضور** — تسجيل يومي للطلاب والموظفين
- 📊 **التقييمات** — متابعة يومية وتقييم الطلاب
- 📖 **القرآن الكريم** — تتبع السور المحفوظة لكل طالب
- 🚌 **خدمة الباص** — إدارة اشتراكات النقل
- 📱 **متجاوب** — يعمل على الموبايل والتابلت والكمبيوتر

---

## 🛠️ التقنيات المستخدمة

| التقنية | الإصدار | الاستخدام |
|---------|---------|-----------|
| Python | 3.10 | لغة البرمجة |
| Django | 5.2 | إطار العمل |
| Bootstrap | 5.3 RTL | واجهة المستخدم |
| SQLite | 3 | قاعدة البيانات |
| Font Awesome | 6.4 | الأيقونات |
| Tajawal | — | الخط العربي |

---

## 🚀 تشغيل المشروع محلياً

### المتطلبات
- Python 3.10+
- Git

### خطوات التثبيت

```bash
# 1. استنسخ المشروع
git clone https://github.com/sendoo-m/quraan_new_system.git
cd quraan_new_system

# 2. أنشئ بيئة افتراضية
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Linux/Mac

# 3. ثبّت المتطلبات
pip install -r requirements.txt

# 4. أنشئ قاعدة البيانات
python manage.py migrate

# 5. أنشئ حساب المدير
python manage.py createsuperuser

# 6. شغّل السيرفر
python manage.py runserver
```

افتح المتصفح على: [**http://127.0.0.1:8000**](http://127.0.0.1:8000)

---

## 📁 هيكل المشروع

```
quraan_new_system/
│
├── core/               # إعدادات المشروع
├── accounts/           # المستخدمون والصلاحيات
├── students/           # إدارة الطلاب
├── halls/              # إدارة القاعات
├── attendance/         # الحضور والغياب
├── evaluations/        # التقييمات والمتابعة
├── quran/              # سور القرآن الكريم
├── templates/          # قوالب HTML
├── static/             # CSS, JS, Images
└── manage.py
```

---

## 👥 أدوار المستخدمين

| الدور | الصلاحيات |
|-------|-----------|
| 🔴 المدير العام | كامل الصلاحيات |
| 🟠 المشرف العام | إدارة الطلاب والقاعات |
| 🟡 المشرف | إدارة قاعته فقط |
| 🟢 المعلم | تسجيل الحضور والتقييم |
| 🔵 ولي الأمر | متابعة أبنائه فقط |

---

## 🌐 النشر على PythonAnywhere

```bash
# على PythonAnywhere Bash
git clone https://github.com/sendoo-m/quraan_new_system.git
cd quraan_new_system
python3.10 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
```

---

## 🔄 تحديث المشروع

```bash
# على جهازك
git add .
git commit -m "وصف التعديل"
git push

# على PythonAnywhere
git pull
python manage.py migrate
python manage.py collectstatic --noinput
# ثم Reload في Web Tab
```

---

## 📸 لقطات الشاشة

> قريباً

---

## 📄 الرخصة

هذا المشروع مرخص تحت رخصة **MIT**

---

<div align="center">

صُنع بـ ❤️ لخدمة تحفيظ القرآن الكريم

</div>
