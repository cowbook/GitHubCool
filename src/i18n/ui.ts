export const languages = {
  zh: '简体中文',
  en: 'English',
};

export const defaultLang = 'zh';

export const ui = {
  zh: {
    'site.title': 'GitHub Cool - GitHub 开源热榜中文解读',
    'site.description': '每日精选 GitHub Trending 热门开源项目，AI 与开发者工具深度解读',
    'nav.home': '首页',
    'nav.trending': '今日热榜',
    'nav.about': '关于',
    'nav.lang': 'EN',
    'hero.title': '🔥 GitHub 开源热榜',
    'hero.subtitle': '每日精选 GitHub Trending，用中文读懂全球最火开源项目',
    'hero.cta': '查看今日热榜',
    'trending.title': '📊 今日 GitHub Trending Top 10',
    'trending.date': '2026年4月18日',
    'footer.text': '© 2026 GitHub Cool. 数据来源：GitHub Trending。',
  },
  en: {
    'site.title': 'GitHub Cool - GitHub Trending Decoded',
    'site.description': 'Daily curated GitHub Trending projects with in-depth analysis',
    'nav.home': 'Home',
    'nav.trending': 'Trending',
    'nav.about': 'About',
    'nav.lang': '中文',
    'hero.title': '🔥 GitHub Trending Decoded',
    'hero.subtitle': 'Daily curated open-source projects from GitHub Trending',
    'hero.cta': 'View Today\'s Trending',
    'trending.title': '📊 GitHub Trending Top 10 Today',
    'trending.date': 'April 18, 2026',
    'footer.text': '© 2026 GitHub Cool. Data from GitHub Trending.',
  },
} as const;

export function getLangFromUrl(url: URL) {
  const [, lang] = url.pathname.replace('/GitHubCool', '').split('/');
  if (lang in ui) return lang as keyof typeof ui;
  return defaultLang;
}

export function useTranslations(lang: keyof typeof ui) {
  return function t(key: keyof typeof ui[typeof defaultLang]) {
    return ui[lang][key] || ui[defaultLang][key];
  }
}

export function getLocalizedPath(lang: string, path: string) {
  return `/GitHubCool/${lang}${path}`;
}
