import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';
import zh from './locales/zh.json';
import en from './locales/en.json';
import './types';

i18n
  .use(LanguageDetector) // 浏览器语言检测
  .use(initReactI18next) // React 绑定
  .init({
    resources: {
      zh: { translation: zh },
      en: { translation: en },
    },
    fallbackLng: 'zh', // 默认语言
    debug: false, // 生产环境关闭
    interpolation: {
      escapeValue: false, // React 已经处理 XSS
    },
    detection: {
      order: ['localStorage', 'navigator'], // 优先从 localStorage 读取
      caches: ['localStorage'], // 持久化到 localStorage
    },
  });

export default i18n;
