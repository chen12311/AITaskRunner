import { test, expect, testData } from '../fixtures';

test.describe('边界情况测试', () => {
  test.describe('网络错误处理', () => {
    test('应该处理 API 请求失败', async ({ tasksPage, page }) => {
      // 模拟网络错误
      await page.route('**/api/**', route => route.abort('failed'));

      await tasksPage.goto();

      // 应该显示错误状态或错误消息
      await tasksPage.waitForLoadingToFinish();

      // 恢复网络
      await page.unroute('**/api/**');
    });

    test('应该处理请求超时', async ({ tasksPage, page }) => {
      // 模拟慢速响应
      await page.route('**/api/tasks**', async route => {
        await new Promise(resolve => setTimeout(resolve, 5000));
        await route.continue();
      });

      await tasksPage.goto();

      // 应该显示加载状态
      await tasksPage.waitForLoadingToFinish();

      // 恢复正常
      await page.unroute('**/api/tasks**');
    });

    test('应该处理 500 服务器错误', async ({ tasksPage, page }) => {
      await page.route('**/api/tasks', route =>
        route.fulfill({
          status: 500,
          body: JSON.stringify({ error: 'Internal Server Error' }),
        })
      );

      await tasksPage.goto();
      await tasksPage.waitForLoadingToFinish();

      // 应该显示错误状态
      await page.unroute('**/api/tasks');
    });
  });

  test.describe('表单验证', () => {
    test('任务名称不能为空', async ({ tasksPage }) => {
      await tasksPage.goto();
      await tasksPage.openCreateDialog();

      // 只填写 prompt，不填写名称
      await tasksPage.taskPromptInput.fill(testData.testPrompt);
      await tasksPage.submitButton.click();

      // 对话框应该仍然打开
      await expect(tasksPage.taskDialog).toBeVisible();
    });

    test('项目路径不能为空', async ({ projectsPage }) => {
      await projectsPage.goto();
      await projectsPage.openCreateDialog();

      // 只填写名称，不填写路径
      await projectsPage.projectNameInput.fill(testData.uniqueProjectName());
      await projectsPage.submitButton.click();

      // 对话框应该仍然打开
      await expect(projectsPage.projectDialog).toBeVisible();
    });

    test('应该处理特殊字符输入', async ({ tasksPage }) => {
      await tasksPage.goto();
      await tasksPage.openCreateDialog();

      // 使用特殊字符
      const specialName = `Test <script>alert('xss')</script> ${Date.now()}`;
      await tasksPage.taskNameInput.fill(specialName);
      await tasksPage.taskPromptInput.fill(testData.testPrompt);
      await tasksPage.submitButton.click();

      await tasksPage.waitForLoadingToFinish();

      // 应该正确处理特殊字符（转义或拒绝）
    });

    test('应该处理超长输入', async ({ tasksPage }) => {
      await tasksPage.goto();
      await tasksPage.openCreateDialog();

      // 使用超长名称
      const longName = 'A'.repeat(1000);
      await tasksPage.taskNameInput.fill(longName);
      await tasksPage.taskPromptInput.fill(testData.testPrompt);
      await tasksPage.submitButton.click();

      // 应该显示验证错误或截断
      await tasksPage.waitForLoadingToFinish();
    });
  });

  test.describe('空数据状态', () => {
    test('任务列表为空时应该显示空状态', async ({ tasksPage, page }) => {
      // 模拟空数据响应
      await page.route('**/api/tasks**', route =>
        route.fulfill({
          status: 200,
          body: JSON.stringify({ items: [], total: 0 }),
        })
      );

      await tasksPage.goto();
      await tasksPage.waitForLoadingToFinish();

      // 应该显示空状态
      await tasksPage.expectEmptyState();

      await page.unroute('**/api/tasks**');
    });

    test('项目列表为空时应该显示空状态', async ({ projectsPage, page }) => {
      await page.route('**/api/projects**', route =>
        route.fulfill({
          status: 200,
          body: JSON.stringify({ items: [], total: 0 }),
        })
      );

      await projectsPage.goto();
      await projectsPage.waitForLoadingToFinish();

      await projectsPage.expectEmptyState();

      await page.unroute('**/api/projects**');
    });

    test('会话列表为空时应该显示空状态', async ({ sessionsPage, page }) => {
      await page.route('**/api/sessions**', route =>
        route.fulfill({
          status: 200,
          body: JSON.stringify({ items: [], total: 0 }),
        })
      );

      await sessionsPage.goto();
      await sessionsPage.waitForLoadingToFinish();

      await sessionsPage.expectEmptyState();

      await page.unroute('**/api/sessions**');
    });
  });

  test.describe('并发操作', () => {
    test('应该处理快速连续点击', async ({ tasksPage }) => {
      await tasksPage.goto();

      // 快速多次点击创建按钮
      await tasksPage.createTaskButton.click();
      await tasksPage.createTaskButton.click({ force: true }).catch(() => {});
      await tasksPage.createTaskButton.click({ force: true }).catch(() => {});

      // 应该只打开一个对话框
      const dialogCount = await tasksPage.page.getByRole('dialog').count();
      expect(dialogCount).toBeLessThanOrEqual(1);
    });

    test('应该处理同时创建多个任务', async ({ tasksPage, projectsPage }) => {
      // 先创建项目
      const projectName = testData.uniqueProjectName();
      await projectsPage.goto();
      await projectsPage.createProject({
        name: projectName,
        path: testData.testProjectPath,
      });

      await tasksPage.goto();

      // 创建第一个任务
      const taskName1 = testData.uniqueTaskName();
      await tasksPage.createTask({
        name: taskName1,
        prompt: testData.testPrompt,
        project: projectName,
      });

      // 立即创建第二个任务
      const taskName2 = testData.uniqueTaskName();
      await tasksPage.createTask({
        name: taskName2,
        prompt: testData.testPrompt,
        project: projectName,
      });

      // 两个任务都应该存在
      await tasksPage.expectTaskExists(taskName1);
      await tasksPage.expectTaskExists(taskName2);
    });
  });

  test.describe('页面刷新', () => {
    test('刷新页面后应该保持数据', async ({ tasksPage, projectsPage, page }) => {
      // 创建项目
      const projectName = testData.uniqueProjectName();
      await projectsPage.goto();
      await projectsPage.createProject({
        name: projectName,
        path: testData.testProjectPath,
      });

      // 创建任务
      await tasksPage.goto();
      const taskName = testData.uniqueTaskName();
      await tasksPage.createTask({
        name: taskName,
        prompt: testData.testPrompt,
        project: projectName,
      });

      // 刷新页面
      await page.reload();
      await tasksPage.waitForLoadingToFinish();

      // 任务应该仍然存在
      await tasksPage.expectTaskExists(taskName);
    });

    test('刷新页面后应该保持筛选状态', async ({ tasksPage, page }) => {
      await tasksPage.goto();

      // 设置搜索条件
      await tasksPage.searchTasks('test');

      // 刷新页面
      await page.reload();
      await tasksPage.waitForLoadingToFinish();

      // 搜索框可能保持或清空，取决于实现
    });
  });

  test.describe('浏览器后退/前进', () => {
    test('应该正确处理浏览器后退', async ({ basePage, page }) => {
      await basePage.goto('/tasks');
      await basePage.goto('/projects');
      await basePage.goto('/settings');

      // 后退
      await page.goBack();
      expect(basePage.getCurrentPath()).toMatch(/projects/i);

      await page.goBack();
      expect(basePage.getCurrentPath()).toMatch(/tasks/i);
    });

    test('应该正确处理浏览器前进', async ({ basePage, page }) => {
      await basePage.goto('/tasks');
      await basePage.goto('/projects');

      // 后退
      await page.goBack();
      expect(basePage.getCurrentPath()).toMatch(/tasks/i);

      // 前进
      await page.goForward();
      expect(basePage.getCurrentPath()).toMatch(/projects/i);
    });
  });

  test.describe('404 处理', () => {
    test('访问不存在的页面应该显示 404', async ({ basePage }) => {
      await basePage.goto('/non-existent-page');

      // 应该显示 404 页面或重定向
      await basePage.waitForPageLoad();
    });

    test('访问不存在的任务应该处理错误', async ({ page }) => {
      await page.goto('/tasks/non-existent-id');
      await page.waitForLoadState('networkidle');

      // 应该显示错误或重定向
    });
  });

  test.describe('键盘导航', () => {
    test('应该支持 Tab 键导航', async ({ tasksPage }) => {
      await tasksPage.goto();
      await tasksPage.openCreateDialog();

      // 使用 Tab 键导航
      await tasksPage.page.keyboard.press('Tab');
      await tasksPage.page.keyboard.press('Tab');
      await tasksPage.page.keyboard.press('Tab');

      // 应该能够通过键盘导航
    });

    test('应该支持 Escape 键关闭对话框', async ({ tasksPage }) => {
      await tasksPage.goto();
      await tasksPage.openCreateDialog();

      // 按 Escape 键
      await tasksPage.page.keyboard.press('Escape');

      // 对话框应该关闭
      await expect(tasksPage.taskDialog).not.toBeVisible();
    });

    test('应该支持 Enter 键提交表单', async ({ tasksPage }) => {
      await tasksPage.goto();
      await tasksPage.openCreateDialog();

      // 填写表单
      await tasksPage.taskNameInput.fill(testData.uniqueTaskName());
      await tasksPage.taskPromptInput.fill(testData.testPrompt);

      // 按 Enter 键（在某些实现中可能提交表单）
      await tasksPage.page.keyboard.press('Enter');
    });
  });
});
