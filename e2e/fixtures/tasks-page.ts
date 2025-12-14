import { Page, Locator, expect } from '@playwright/test';
import { BasePage } from './base-page';

/**
 * 任务页面对象
 */
export class TasksPage extends BasePage {
  readonly createTaskButton: Locator;
  readonly taskList: Locator;
  readonly taskDialog: Locator;
  readonly taskNameInput: Locator;
  readonly taskPromptInput: Locator;
  readonly projectSelect: Locator;
  readonly templateSelect: Locator;
  readonly submitButton: Locator;
  readonly cancelButton: Locator;
  readonly searchInput: Locator;
  readonly statusFilter: Locator;
  readonly emptyState: Locator;

  constructor(page: Page) {
    super(page);
    this.createTaskButton = page.getByRole('button', { name: /create|新建|添加/i });
    this.taskList = page.locator('[data-testid="task-list"], .task-list, table tbody');
    this.taskDialog = page.getByRole('dialog');
    this.taskNameInput = page.getByLabel(/name|名称/i);
    this.taskPromptInput = page.getByLabel(/prompt|提示词|描述/i);
    this.projectSelect = page.getByLabel(/project|项目/i);
    this.templateSelect = page.getByLabel(/template|模板/i);
    this.submitButton = this.taskDialog.getByRole('button', { name: /submit|save|确定|保存|创建/i });
    this.cancelButton = this.taskDialog.getByRole('button', { name: /cancel|取消/i });
    this.searchInput = page.getByPlaceholder(/search|搜索/i);
    this.statusFilter = page.getByLabel(/status|状态/i);
    this.emptyState = page.locator('[data-testid="empty-state"], .empty-state');
  }

  /**
   * 导航到任务页面
   */
  async goto() {
    await super.goto('/tasks');
  }

  /**
   * 打开创建任务对话框
   */
  async openCreateDialog() {
    await this.createTaskButton.click();
    await expect(this.taskDialog).toBeVisible();
  }

  /**
   * 创建新任务
   */
  async createTask(options: {
    name: string;
    prompt: string;
    project?: string;
    template?: string;
  }) {
    await this.openCreateDialog();
    await this.taskNameInput.fill(options.name);
    await this.taskPromptInput.fill(options.prompt);

    if (options.project) {
      await this.projectSelect.click();
      await this.page.getByRole('option', { name: options.project }).click();
    }

    if (options.template) {
      await this.templateSelect.click();
      await this.page.getByRole('option', { name: options.template }).click();
    }

    await this.submitButton.click();
    await this.waitForLoadingToFinish();
  }

  /**
   * 获取任务行
   */
  getTaskRow(taskName: string): Locator {
    return this.taskList.locator('tr, [data-testid="task-item"]').filter({ hasText: taskName });
  }

  /**
   * 启动任务
   */
  async startTask(taskName: string) {
    const row = this.getTaskRow(taskName);
    await row.getByRole('button', { name: /start|启动|运行/i }).click();
    await this.waitForLoadingToFinish();
  }

  /**
   * 停止任务
   */
  async stopTask(taskName: string) {
    const row = this.getTaskRow(taskName);
    await row.getByRole('button', { name: /stop|停止/i }).click();
    await this.waitForLoadingToFinish();
  }

  /**
   * 删除任务
   */
  async deleteTask(taskName: string) {
    const row = this.getTaskRow(taskName);
    await row.getByRole('button', { name: /delete|删除/i }).click();
    // 确认删除对话框
    await this.page.getByRole('button', { name: /confirm|确认|是/i }).click();
    await this.waitForLoadingToFinish();
  }

  /**
   * 编辑任务
   */
  async editTask(taskName: string, newData: { name?: string; prompt?: string }) {
    const row = this.getTaskRow(taskName);
    await row.getByRole('button', { name: /edit|编辑/i }).click();
    await expect(this.taskDialog).toBeVisible();

    if (newData.name) {
      await this.taskNameInput.clear();
      await this.taskNameInput.fill(newData.name);
    }

    if (newData.prompt) {
      await this.taskPromptInput.clear();
      await this.taskPromptInput.fill(newData.prompt);
    }

    await this.submitButton.click();
    await this.waitForLoadingToFinish();
  }

  /**
   * 搜索任务
   */
  async searchTasks(query: string) {
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
   * 验证任务存在
   */
  async expectTaskExists(taskName: string) {
    await expect(this.getTaskRow(taskName)).toBeVisible();
  }

  /**
   * 验证任务不存在
   */
  async expectTaskNotExists(taskName: string) {
    await expect(this.getTaskRow(taskName)).not.toBeVisible();
  }

  /**
   * 验证任务状态
   */
  async expectTaskStatus(taskName: string, status: string | RegExp) {
    const row = this.getTaskRow(taskName);
    await expect(row).toContainText(status);
  }

  /**
   * 获取任务数量
   */
  async getTaskCount(): Promise<number> {
    return await this.taskList.locator('tr, [data-testid="task-item"]').count();
  }

  /**
   * 验证空状态
   */
  async expectEmptyState() {
    await expect(this.emptyState).toBeVisible();
  }
}
