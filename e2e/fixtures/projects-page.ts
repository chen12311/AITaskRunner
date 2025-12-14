import { Page, Locator, expect } from '@playwright/test';
import { BasePage } from './base-page';

/**
 * 项目页面对象
 */
export class ProjectsPage extends BasePage {
  readonly createProjectButton: Locator;
  readonly projectList: Locator;
  readonly projectDialog: Locator;
  readonly projectNameInput: Locator;
  readonly projectPathInput: Locator;
  readonly projectDescriptionInput: Locator;
  readonly cliSelect: Locator;
  readonly terminalSelect: Locator;
  readonly submitButton: Locator;
  readonly cancelButton: Locator;
  readonly searchInput: Locator;
  readonly emptyState: Locator;

  constructor(page: Page) {
    super(page);
    this.createProjectButton = page.getByRole('button', { name: /create|新建|添加/i });
    this.projectList = page.locator('[data-testid="project-list"], .project-list, table tbody');
    this.projectDialog = page.getByRole('dialog');
    this.projectNameInput = page.getByLabel(/name|名称/i);
    this.projectPathInput = page.getByLabel(/path|路径/i);
    this.projectDescriptionInput = page.getByLabel(/description|描述/i);
    this.cliSelect = page.getByLabel(/cli|命令行/i);
    this.terminalSelect = page.getByLabel(/terminal|终端/i);
    this.submitButton = this.projectDialog.getByRole('button', { name: /submit|save|确定|保存|创建/i });
    this.cancelButton = this.projectDialog.getByRole('button', { name: /cancel|取消/i });
    this.searchInput = page.getByPlaceholder(/search|搜索/i);
    this.emptyState = page.locator('[data-testid="empty-state"], .empty-state');
  }

  /**
   * 导航到项目页面
   */
  async goto() {
    await super.goto('/projects');
  }

  /**
   * 打开创建项目对话框
   */
  async openCreateDialog() {
    await this.createProjectButton.click();
    await expect(this.projectDialog).toBeVisible();
  }

  /**
   * 创建新项目
   */
  async createProject(options: {
    name: string;
    path: string;
    description?: string;
    cli?: string;
    terminal?: string;
  }) {
    await this.openCreateDialog();
    await this.projectNameInput.fill(options.name);
    await this.projectPathInput.fill(options.path);

    if (options.description) {
      await this.projectDescriptionInput.fill(options.description);
    }

    if (options.cli) {
      await this.cliSelect.click();
      await this.page.getByRole('option', { name: options.cli }).click();
    }

    if (options.terminal) {
      await this.terminalSelect.click();
      await this.page.getByRole('option', { name: options.terminal }).click();
    }

    await this.submitButton.click();
    await this.waitForLoadingToFinish();
  }

  /**
   * 获取项目行
   */
  getProjectRow(projectName: string): Locator {
    return this.projectList.locator('tr, [data-testid="project-item"]').filter({ hasText: projectName });
  }

  /**
   * 启动项目
   */
  async launchProject(projectName: string) {
    const row = this.getProjectRow(projectName);
    await row.getByRole('button', { name: /launch|启动/i }).click();
    await this.waitForLoadingToFinish();
  }

  /**
   * 编辑项目
   */
  async editProject(projectName: string, newData: {
    name?: string;
    path?: string;
    description?: string;
  }) {
    const row = this.getProjectRow(projectName);
    await row.getByRole('button', { name: /edit|编辑/i }).click();
    await expect(this.projectDialog).toBeVisible();

    if (newData.name) {
      await this.projectNameInput.clear();
      await this.projectNameInput.fill(newData.name);
    }

    if (newData.path) {
      await this.projectPathInput.clear();
      await this.projectPathInput.fill(newData.path);
    }

    if (newData.description) {
      await this.projectDescriptionInput.clear();
      await this.projectDescriptionInput.fill(newData.description);
    }

    await this.submitButton.click();
    await this.waitForLoadingToFinish();
  }

  /**
   * 删除项目
   */
  async deleteProject(projectName: string) {
    const row = this.getProjectRow(projectName);
    await row.getByRole('button', { name: /delete|删除/i }).click();
    // 确认删除
    await this.page.getByRole('button', { name: /confirm|确认|是/i }).click();
    await this.waitForLoadingToFinish();
  }

  /**
   * 搜索项目
   */
  async searchProjects(query: string) {
    await this.searchInput.fill(query);
    await this.waitForLoadingToFinish();
  }

  /**
   * 验证项目存在
   */
  async expectProjectExists(projectName: string) {
    await expect(this.getProjectRow(projectName)).toBeVisible();
  }

  /**
   * 验证项目不存在
   */
  async expectProjectNotExists(projectName: string) {
    await expect(this.getProjectRow(projectName)).not.toBeVisible();
  }

  /**
   * 获取项目数量
   */
  async getProjectCount(): Promise<number> {
    return await this.projectList.locator('tr, [data-testid="project-item"]').count();
  }

  /**
   * 验证空状态
   */
  async expectEmptyState() {
    await expect(this.emptyState).toBeVisible();
  }
}
