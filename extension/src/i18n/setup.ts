// ─── i18next setup ─────────────────────────────────────────────────────────
import i18n from "i18next";
import { initReactI18next } from "react-i18next";

import en from "@locales/en/ui.json";
import hi from "@locales/hi/ui.json";
import mr from "@locales/mr/ui.json";

i18n.use(initReactI18next).init({
  resources: {
    en: { translation: en },
    hi: { translation: hi },
    mr: { translation: mr },
  },
  lng: "en",
  fallbackLng: "en",
  interpolation: { escapeValue: false },
});

export default i18n;
