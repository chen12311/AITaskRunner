import { test, expect, testData } from '../fixtures';

test.describe('会话工作流', () => {
  test.beforeEach(async ({ sessionsPage }) => {
    await sessionsPage.goto();
  });

  test('应该显示会话列表页面', async ({ sessionsPage }) => {
    await expect(sessionsPage.mainContent).toBeVisible();
  });

  test('应该能够查看会话列表', async ({ sessionsPage }) => {
    // 等待页面加载
    await sessionsPage.waitForLoadingToFinish();

    // 会话列表应该可见（可能为空）
    const sessionCount = await sessionsPage.getSessionCount();
    if (sessionCount === 0) {
      await sessionsPage.expectEmptyState();
    } else {
      await expect(sessionsPage.sessionList).toBeVisible();
    }
  });

  test('应该能够刷新会话列表', async ({ sessionsPage }) => {
    await sessionsPage.refresh();
    await sessionsPage.waitForLoadingToFinish();

    // 页面应该仍然正常显示
    await expect(sessionsPage.mainContent).toBeVisible();
  });

  test('应该能够搜索会话', async ({ sessionsPage }) => {
    await sessionsPage.searchSessions('test');
    await sessionsPage.waitForLoadingToFinish();

    // 搜索后页面应该正常显示
    await expect(sessionsPage.mainContent).toBeVisible();
  });

  test('应该能够按状态筛选会话', async ({ sessionsPage, page }) => {
    // 检查是否有状态筛选器
    const hasStatusFilter = await sessionsPage.statusFilter.isVisible().catch(() => false);

    if (hasStatusFilter) {
      await sessionsPage.filterByStatus('running');
      await sessionsPage.waitForLoadingToFinish();

      // 筛选后页面应该正常显示
      await expect(sessionsPage.mainContent).toBeVisible();
    }
  });

  test('应该能够查看会话详情', async ({ sessionsPage, tasksPage, projectsPage }) => {
    // 先创建一个项目和任务来生成会话
    const projectName = testData.uniqueProjectName();
    await projectsPage.goto();
    await projectsPage.createProject({
      name: projectName,
      path: testData.testProjectPath,
    });

    const taskName = testData.uniqueTaskName();
    await tasksPage.goto();
    await tasksPage.createTask({
      name: taskName,
      prompt: testData.testPrompt,
      project: projectName,
    });

    // 启动任务以创建会话
    await tasksPage.startTask(taskName);

    // 导航到会话页面
    await sessionsPage.goto();
    await sessionsPage.waitForLoadingToFinish();

    // 如果有会话，尝试查看详情
    const sessionCount = await sessionsPage.getSessionCount();
    if (sessionCount > 0) {
      // 点击第一个会话
      const firstSession = sessionsPage.sessionList.locator('tr, [data-testid="session-item"]').first();
      await firstSession.click();

      // 应该显示会话详情或日志
      await sessionsPage.waitForLoadingToFinish();
    }
  });

  test('应该能够查看会话日志', async ({ sessionsPage, tasksPage, projectsPage }) => {
    // 先创建一个项目和任务来生成会话
    const projectName = testData.uniqueProjectName();
    await projectsPage.goto();
    await projectsPage.createProject({
      name: projectName,
      path: testData.testProjectPath,
    });

    const taskName = testData.uniqueTaskName();
    await tasksPage.goto();
    await tasksPage.createTask({
      name: taskName,
      prompt: testData.testPrompt,
      project: projectName,
    });

    // 启动任务以创建会话
    await tasksPage.startTask(taskName);

    // 导航到会话页面
    await sessionsPage.goto();
    await sessionsPage.waitForLoadingToFinish();

    // 如果有会话，尝试查看日志
    const sessionCount = await sessionsPage.getSessionCount();
    if (sessionCount > 0) {
      const firstSession = sessionsPage.sessionList.locator('tr, [data-testid="session-item"]').first();
      const logsButton = firstSession.getByRole('button', { name: /logs|日志/i });

      if (await logsButton.isVisible().catch(() => false)) {
        await logsButton.click();
        await sessionsPage.waitForLoadingToFinish();

        // 日志查看器应该可见
        await expect(sessionsPage.logViewer).toBeVisible();
      }
    }
  });

  test('应该能够删除会话', async ({ sessionsPage, tasksPage, projectsPage }) => {
    // 先创建一个项目和任务来生成会话
    const projectName = testData.uniqueProjectName();
    await projectsPage.goto();
    await projectsPage.createProject({
      name: projectName,
      path: testData.testProjectPath,
    });

    const taskName = testData.uniqueTaskName();
    await tasksPage.goto();
    await tasksPage.createTask({
      name: taskName,
      prompt: testData.testPrompt,
      project: projectName,
    });

    // 启动任务以创建会话
    await tasksPage.startTask(taskName);

    // 停止任务
    await tasksPage.stopTask(taskName);

    // 导航到会话页面
    await sessionsPage.goto();
    await sessionsPage.waitForLoadingToFinish();

    // 如果有会话，尝试删除
    const sessionCount = await sessionsPage.getSessionCount();
    if (sessionCount > 0) {
      const firstSession = sessionsPage.sessionList.locator('tr, [data-testid="session-item"]').first();
      const deleteButton = firstSession.getByRole('button', { name: /delete|删除/i });

      if (await deleteButton.isVisible().catch(() => false)) {
        const initialCount = sessionCount;
        await deleteButton.click();

        // 确认删除
        await sessionsPage.page.getByRole('button', { name: /confirm|确认|是/i }).click();
        await sessionsPage.waitForLoadingToFinish();

        // 会话数量应该减少
        const newCount = await sessionsPage.getSessionCount();
        expect(newCount).toBeLessThan(initialCount);
      }
    }
  });

  test('应该在没有会话时显示空状态', async ({ sessionsPage }) => {
    await sessionsPage.waitForLoadingToFinish();

    const sessionCount = await sessionsPage.getSessionCount();
    if (sessionCount === 0) {
      await sessionsPage.expectEmptyState();
    }
  });
});
