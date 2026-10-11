"""Localised generic messages for the common error codes (EN / HI / MR).

Every error body carries `code`, a stable `message_key` ("errors.<CODE>") the extension can map to its own
locale files, and `localized` (this table). Language: `X-Lang` header, else Accept-Language, else en.
[NEEDS VERIFICATION] HI/MR wording must be reviewed by a bilingual teammate before the demo.
"""
LANGS = ("en", "hi", "mr")

MESSAGES: dict[str, dict[str, str]] = {
    "UNAUTHORIZED": {
        "en": "Missing or invalid API token.",
        "hi": "API टोकन गायब है या अमान्य है।",
        "mr": "API टोकन नाही किंवा अवैध आहे.",
    },
    "FORBIDDEN": {
        "en": "You do not have access to this item.",
        "hi": "आपको इस आइटम तक पहुँच की अनुमति नहीं है।",
        "mr": "या आयटमपर्यंत पोहोचण्याची तुम्हाला परवानगी नाही.",
    },
    "VALIDATION_ERROR": {
        "en": "The request is not valid.",
        "hi": "अनुरोध मान्य नहीं है।",
        "mr": "विनंती वैध नाही.",
    },
    "RATE_LIMITED": {
        "en": "Too many requests. Please wait a moment and try again.",
        "hi": "बहुत अधिक अनुरोध। कृपया थोड़ी देर रुककर फिर से प्रयास करें।",
        "mr": "खूप विनंत्या. कृपया थोडा वेळ थांबून पुन्हा प्रयत्न करा.",
    },
    "CODE_REJECTED": {
        "en": "This code uses something the sandbox does not allow.",
        "hi": "इस कोड में ऐसी चीज़ है जिसकी सैंडबॉक्स अनुमति नहीं देता।",
        "mr": "या कोडमध्ये सँडबॉक्स परवानगी देत नाही अशी गोष्ट आहे.",
    },
    "HINT_LOCKED": {
        "en": "This hint is not unlocked yet. Keep trying, then ask again.",
        "hi": "यह संकेत अभी अनलॉक नहीं हुआ है। कोशिश जारी रखें, फिर दोबारा पूछें।",
        "mr": "हा संकेत अद्याप अनलॉक झालेला नाही. प्रयत्न सुरू ठेवा, मग पुन्हा विचारा.",
    },
    "UNSUPPORTED_PROBLEM": {
        "en": "This problem type is explanation-only for now.",
        "hi": "यह समस्या प्रकार अभी केवल व्याख्या के लिए है।",
        "mr": "हा समस्या प्रकार सध्या फक्त स्पष्टीकरणासाठी आहे.",
    },
    "UNSUPPORTED_LANGUAGE": {
        "en": "Only Python 3 can be run. Switch the editor to Python 3.",
        "hi": "केवल Python 3 चलाया जा सकता है। एडिटर को Python 3 पर बदलें।",
        "mr": "फक्त Python 3 चालवता येते. एडिटर Python 3 वर बदला.",
    },
    "CREDIT_CAP_REACHED": {
        "en": "The daily voice credit limit has been reached.",
        "hi": "दैनिक वॉइस क्रेडिट सीमा पूरी हो गई है।",
        "mr": "दैनिक व्हॉइस क्रेडिट मर्यादा संपली आहे.",
    },
    "UPSTREAM_FAILED": {
        "en": "A required service is unavailable. Please try again.",
        "hi": "एक आवश्यक सेवा उपलब्ध नहीं है। कृपया फिर से प्रयास करें।",
        "mr": "एक आवश्यक सेवा उपलब्ध नाही. कृपया पुन्हा प्रयत्न करा.",
    },
}


def pick_lang(x_lang: str | None, accept_language: str | None) -> str:
    for raw in (x_lang, (accept_language or "").split(",")[0]):
        code = (raw or "").strip().lower()[:2]
        if code in LANGS:
            return code
    return "en"


def localized(code: str, lang: str) -> str:
    return MESSAGES.get(code, {}).get(lang) or MESSAGES.get(code, {}).get("en", code)
