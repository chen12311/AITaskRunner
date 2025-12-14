import { test as base } from '@playwright/test';
import { BasePage } from './base-page';
import { TasksPage } from './tasks-page';
import { SessionsPage } from './sessions-page';
import { ProjectsPage } from './projects-page';
import { SettingsPage } from './settings-page';

// 导出所有页面对象
export { BasePage, TasksPage, SessionsPage, ProjectsPage, SettingsPage };

// 定义 fixtures 类型
type Fixtures = {
  basePage: BasePage;
  tasksPage: TasksPage;
  sessionsPage: SessionsPage;
  projectsPage: ProjectsPage;
  settingsPage: SettingsPage;
};

/**
 * 扩展 Playwright test，添加页面对象 fixtures
 */
export const test = base.extend<Fixtures>({
  basePage: async ({ page }, use) => {
    await use(new BasePage(page));
  },

  tasksPage: async ({ page }, use) => {
    await use(new TasksPage(page));
  },

  sessionsPage: async ({ page }, use) => {
    await use(new SessionsPage(page));
  },

  projectsPage: async ({ page }, use) => {
    await use(new ProjectsPage(page));
  },

  settingsPage: async ({ page }, use) => {
    await use(new SettingsPage(page));
  },
});

export { expect } from '@playwright/test';

/**
 * 测试数据工厂
 */
export const testData = {
  /**
   * 生成唯一的任务名称
   */
  uniqueTaskName: () => `Test Task ${Date.now()}`,

  /**
   * 生成唯一的项目名称
   */
  uniqueProjectName: () => `Test Project ${Date.now()}`,

  /**
   * 生成唯一的模板名称
   */
  uniqueTemplateName: () => `Test Template ${Date.now()}`,

  /**
   * 测试项目路径
   */
  testProjectPath: '/tmp/test-project',

  /**
   * 测试提示词
   */
  testPrompt: 'This is a test prompt for E2E testing',

  /**
   * 测试描述
   */
  testDescription: 'This is a test description for E2E testing',
};

/**
 * 等待指定毫秒数
 */
export const wait = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

/**
 * 重试函数
 */
export async function retry<T>(
  fn: () => Promise<T>,
  options: { retries?: number; delay?: number } = {}
): Promise<T> {
  const { retries = 3, delay = 1000 } = options;
  let lastError: Error | undefined;

  for (let i = 0; i < retries; i++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error as Error;
      if (i < retries - 1) {
        await wait(delay);
      }
    }
  }

  throw lastError;
}
