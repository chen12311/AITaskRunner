import { Page, Locator, expect } from '@playwright/test';
import { BasePage } from './base-page';

/**
 * 会话页面对象
 */
export class SessionsPage extends BasePage {
  readonly sessionList: Locator;
  readonly sessionDetail: Locator;
  readonly logViewer: Locator;
  readonly refreshButton: Locator;
  readonly searchInput: Locator;
  readonly statusFilter: Locator;
  readonly emptyState: Locator;
  readonly deleteButton: Locator;

  constructor(page: Page) {
    super(page);
    this.sessionList = page.locator('[data-testid="session-list"], .session-list, table tbody');
    this.sessionDetail = page.locator('[data-testid="session-detail"], .session-detail');
    this.logViewer = page.locator('[data-testid="log-viewer"], .log-viewer, pre');
    this.refreshButton = page.getByRole('button', { name: /refresh|刷新/i });
    this.searchInput = page.getByPlaceholder(/search|搜索/i);
    this.statusFilter = page.getByLabel(/status|状态/i);
    this.emptyState = page.locator('[data-testid="empty-state"], .empty-state');
    this.deleteButton = page.getByRole('button', { name: /delete|删除/i });
  }

  /**
   * 导航到会话页面
   */
  async goto() {
    await super.goto('/sessions');
  }

  /**
   * 获取会话行
   */
  getSessionRow(sessionId: string): Locator {
    return this.sessionList.locator('tr, [data-testid="session-item"]').filter({ hasText: sessionId });
  }

  /**
   * 点击会话查看详情
   */
  async viewSessionDetail(sessionId: string) {
    const row = this.getSessionRow(sessionId);
    await row.click();
    await this.waitForLoadingToFinish();
  }

  /**
   * 展开会话详情
   */
  async expandSession(sessionId: string) {
    const row = this.getSessionRow(sessionId);
    await row.getByRole('button', { name: /expand|展开|详情/i }).click();
    await expect(this.sessionDetail).toBeVisible();
  }

  /**
   * 查看会话日志
   */
  async viewSessionLogs(sessionId: string) {
    const row = this.getSessionRow(sessionId);
    await row.getByRole('button', { name: /logs|日志/i }).click();
    await expect(this.logViewer).toBeVisible();
  }

  /**
   * 删除会话
   */
  async deleteSession(sessionId: string) {
    const row = this.getSessionRow(sessionId);
    await row.getByRole('button', { name: /delete|删除/i }).click();
    // 确认删除
    await this.page.getByRole('button', { name: /confirm|确认|是/i }).click();
    await this.waitForLoadingToFinish();
  }

  /**
   * 刷新会话列表
   */
  async refresh() {
    await this.refreshButton.click();
    await this.waitForLoadingToFinish();
  }

  /**
   * 搜索会话
   */
  async searchSessions(query: string) {
    await this.searchInput.fill(query);
    await this.waitForLoadingToFinish();
  }

  /**
   * 按状态筛选
   */
  async filterByStatus(status: string) {
    await this.statusFilter.click();
    await this.page.getByRole('option', { name: status }).click();
    await this.waitForLoadingToFinish();
  }

  /**
   * 验证会话存在
   */
  async expectSessionExists(sessionId: string) {
    await expect(this.getSessionRow(sessionId)).toBeVisible();
  }

  /**
   * 验证会话不存在
   */
  async expectSessionNotExists(sessionId: string) {
    await expect(this.getSessionRow(sessionId)).not.toBeVisible();
  }

  /**
   * 验证日志内容
   */
  async expectLogContains(text: string) {
    await expect(this.logViewer).toContainText(text);
  }

  /**
   * 获取会话数量
   */
  async getSessionCount(): Promise<number> {
    return await this.sessionList.locator('tr, [data-testid="session-item"]').count();
  }

  /**
   * 验证空状态
   */
  async expectEmptyState() {
    await expect(this.emptyState).toBeVisible();
  }
}
