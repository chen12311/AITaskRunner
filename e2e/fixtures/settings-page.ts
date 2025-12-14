import { Page, Locator, expect } from '@playwright/test';
import { BasePage } from './base-page';

/**
 * 设置页面对象
 */
export class SettingsPage extends BasePage {
  readonly saveButton: Locator;
  readonly resetButton: Locator;
  readonly themeSelect: Locator;
  readonly languageSelect: Locator;
  readonly defaultCliSelect: Locator;
  readonly defaultTerminalSelect: Locator;
  readonly watchdogEnabledToggle: Locator;
  readonly watchdogIntervalInput: Locator;
  readonly watchdogTimeoutInput: Locator;
  readonly notificationEnabledToggle: Locator;

  constructor(page: Page) {
    super(page);
    this.saveButton = page.getByRole('button', { name: /save|保存/i });
    this.resetButton = page.getByRole('button', { name: /reset|重置/i });
    this.themeSelect = page.getByLabel(/theme|主题/i);
    this.languageSelect = page.getByLabel(/language|语言/i);
    this.defaultCliSelect = page.getByLabel(/default cli|默认 cli/i);
    this.defaultTerminalSelect = page.getByLabel(/default terminal|默认终端/i);
    this.watchdogEnabledToggle = page.getByLabel(/watchdog.*enabled|看门狗.*启用/i);
    this.watchdogIntervalInput = page.getByLabel(/watchdog.*interval|看门狗.*间隔/i);
    this.watchdogTimeoutInput = page.getByLabel(/watchdog.*timeout|看门狗.*超时/i);
    this.notificationEnabledToggle = page.getByLabel(/notification.*enabled|通知.*启用/i);
  }

  /**
   * 导航到设置页面
   */
  async goto() {
    await super.goto('/settings');
  }

  /**
   * 保存设置
   */
  async save() {
    await this.saveButton.click();
    await this.waitForLoadingToFinish();
  }

  /**
   * 重置设置
   */
  async reset() {
    await this.resetButton.click();
    await this.page.getByRole('button', { name: /confirm|确认|是/i }).click();
    await this.waitForLoadingToFinish();
  }

  /**
   * 设置主题
   */
  async setTheme(theme: 'light' | 'dark' | 'system') {
    await this.themeSelect.click();
    await this.page.getByRole('option', { name: new RegExp(theme, 'i') }).click();
  }

  /**
   * 设置语言
   */
  async setLanguage(lang: 'en' | 'zh') {
    await this.languageSelect.click();
    await this.page.getByRole('option', { name: lang === 'en' ? /english/i : /中文/i }).click();
  }

  /**
   * 设置默认 CLI
   */
  async setDefaultCli(cli: string) {
    await this.defaultCliSelect.click();
    await this.page.getByRole('option', { name: cli }).click();
  }

  /**
   * 设置默认终端
   */
  async setDefaultTerminal(terminal: string) {
    await this.defaultTerminalSelect.click();
    await this.page.getByRole('option', { name: terminal }).click();
  }

  /**
   * 切换看门狗启用状态
   */
  async toggleWatchdog() {
    await this.watchdogEnabledToggle.click();
  }

  /**
   * 设置看门狗间隔
   */
  async setWatchdogInterval(interval: number) {
    await this.watchdogIntervalInput.clear();
    await this.watchdogIntervalInput.fill(interval.toString());
  }

  /**
   * 设置看门狗超时
   */
  async setWatchdogTimeout(timeout: number) {
    await this.watchdogTimeoutInput.clear();
    await this.watchdogTimeoutInput.fill(timeout.toString());
  }

  /**
   * 切换通知启用状态
   */
  async toggleNotification() {
    await this.notificationEnabledToggle.click();
  }

  /**
   * 验证设置值
   */
  async expectSettingValue(label: string | RegExp, value: string) {
    const input = this.page.getByLabel(label);
    await expect(input).toHaveValue(value);
  }

  /**
   * 验证保存成功
   */
  async expectSaveSuccess() {
    await this.expectToast(/saved|保存成功/i);
  }
}
