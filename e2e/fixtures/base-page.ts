import { Page, Locator, expect } from '@playwright/test';

/**
 * 基础页面对象类
 * 提供所有页面共享的方法和属性
 */
export class BasePage {
  readonly page: Page;
  readonly header: Locator;
  readonly sidebar: Locator;
  readonly mainContent: Locator;
  readonly loadingSpinner: Locator;
  readonly toast: Locator;

  constructor(page: Page) {
    this.page = page;
    this.header = page.locator('header');
    this.sidebar = page.locator('aside, nav[role="navigation"]');
    this.mainContent = page.locator('main');
    this.loadingSpinner = page.locator('[data-testid="loading"], .loading, [role="progressbar"]');
    this.toast = page.locator('[data-testid="toast"], .toast, [role="alert"]');
  }

  /**
   * 导航到指定路径
   */
  async goto(path: string = '/') {
    await this.page.goto(path);
    await this.waitForPageLoad();
  }

  /**
   * 等待页面加载完成
   */
  async waitForPageLoad() {
    await this.page.waitForLoadState('networkidle');
  }

  /**
   * 等待加载状态消失
   */
  async waitForLoadingToFinish() {
    await this.loadingSpinner.waitFor({ state: 'hidden', timeout: 30000 }).catch(() => {
      // 如果没有 loading spinner，忽略错误
    });
  }

  /**
   * 检查 toast 消息
   */
  async expectToast(message: string | RegExp) {
    await expect(this.toast).toContainText(message);
  }

  /**
   * 等待 toast 消息出现并消失
   */
  async waitForToastAndDismiss(message?: string | RegExp) {
    if (message) {
      await expect(this.toast).toContainText(message);
    }
    await this.toast.waitFor({ state: 'hidden', timeout: 10000 }).catch(() => {});
  }

  /**
   * 点击侧边栏导航项
   */
  async navigateTo(menuItem: string | RegExp) {
    await this.sidebar.getByRole('link', { name: menuItem }).click();
    await this.waitForPageLoad();
  }

  /**
   * 切换主题
   */
  async toggleTheme() {
    await this.header.getByRole('button', { name: /theme|主题/i }).click();
  }

  /**
   * 切换语言
   */
  async switchLanguage(lang: 'en' | 'zh') {
    await this.header.getByRole('button', { name: /language|语言/i }).click();
    await this.page.getByRole('menuitem', { name: lang === 'en' ? /english/i : /中文/i }).click();
  }

  /**
   * 获取当前 URL 路径
   */
  getCurrentPath(): string {
    return new URL(this.page.url()).pathname;
  }

  /**
   * 截图
   */
  async takeScreenshot(name: string) {
    await this.page.screenshot({ path: `test-results/screenshots/${name}.png` });
  }
}
