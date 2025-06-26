# bot/locales.py - ADD THE NEW KEYS

translations = {
    "en": {
        "welcome": "Welcome, {name}! Please /login to get started.",
        "ask_username": "Please send your username.",
        "ask_password": "Got it. Now, please send your password.",
        "login_success": "✅ Login successful! You can now use all commands.",
        "login_fail": "❌ Login failed. Invalid username or password.",
        "lang_select": "Please select your language:",
        "lang_updated": "Language updated to English. 🇬🇧",
        "balance_header": "📊 *Your Financial Summary*",
        "owes_you": "owes you",
        "you_owe": "You owe",
        "no_debts": "Your slate is clean! No outstanding debts. ✨",
        "expense_start": "Let's add a new expense. Which group is this for?",
        "expense_ask_desc": "Great. What is the description of the expense?",
        "expense_ask_amount": "Got it. What's the total amount?",
        "expense_ask_category": "OK. Which category does this fall under?",
        "expense_ask_participants": "Who participated in this expense? (Select all that apply)",
        "expense_confirm_header": "Please confirm the details:",
        "expense_request_sent": "Your expense request has been submitted for voting. ✅",
        # --- NEW ---
        "main_menu_prompt": "Here are the main commands:",
        "btn_balance": "📊 My Balance",
        "btn_new_expense": "💸 New Expense",
        "btn_groups": "👥 My Groups",
        "btn_settings": "⚙️ Settings",

    },
    "ar": {
        "welcome": "أهلاً بك، {name}! من فضلك قم بتسجيل الدخول باستخدام /login للبدء.",
        "ask_username": "من فضلك أرسل اسم المستخدم الخاص بك.",
        "ask_password": "تمام. الآن، من فضلك أرسل كلمة المرور.",
        "login_success": "✅ تم تسجيل الدخول بنجاح! يمكنك الآن استخدام جميع الأوامر.",
        "login_fail": "❌ فشل تسجيل الدخول. اسم المستخدم أو كلمة المرور غير صحيحة.",
        "lang_select": "من فضلك اختر لغتك:",
        "lang_updated": "تم تحديث اللغة إلى العربية. 🇪🇬",
        "balance_header": "📊 *ملخصك المالي*",
        "owes_you": "مدين لك بـ",
        "you_owe": "أنت مدين لـ",
        "no_debts": "حساباتك نظيفة! لا توجد ديون معلقة. ✨",
        "expense_start": "لنقم بإضافة مصروف جديد. لأي مجموعة هذا المصروف؟",
        "expense_ask_desc": "ممتاز. ما هو وصف المصروف؟",
        "expense_ask_amount": "تمام. ما هو المبلغ الإجمالي؟",
        "expense_ask_category": "حسنًا. تحت أي تصنيف يندرج هذا المصروف؟",
        "expense_ask_participants": "من شارك في هذا المصروف؟ (اختر كل المشاركين)",
        "expense_confirm_header": "من فضلك قم بتأكيد التفاصيل:",
        "expense_request_sent": "✅ تم إرسال طلب المصروف الخاص بك للتصويت.",
        # --- NEW ---
        "main_menu_prompt": "هذه هي الأوامر الرئيسية:",
        "btn_balance": "📊 ملخصي المالي",
        "btn_new_expense": "💸 مصروف جديد",
        "btn_groups": "👥 مجموعاتي",
        "btn_settings": "⚙️ الإعدادات",
    }
}

def t(key, lang="en", **kwargs):
    # Fallback to English if a key is not found in the selected language
    return translations.get(lang, translations["en"]).get(key, key).format(**kwargs)