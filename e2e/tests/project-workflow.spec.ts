import { test, expect, testData } from '../fixtures';

test.describe('项目工作流', () => {
  test.beforeEach(async ({ projectsPage }) => {
    await projectsPage.goto();
  });

  test('应该显示项目列表页面', async ({ projectsPage }) => {
    await expect(projectsPage.mainContent).toBeVisible();
    await expect(projectsPage.createProjectButton).toBeVisible();
  });

  test('应该能够创建新项目', async ({ projectsPage }) => {
    const projectName = testData.uniqueProjectName();

    await projectsPage.createProject({
      name: projectName,
      path: testData.testProjectPath,
      description: testData.testDescription,
    });

    await projectsPage.expectProjectExists(projectName);
  });

  test('应该能够编辑项目', async ({ projectsPage }) => {
    // 先创建一个项目
    const originalName = testData.uniqueProjectName();
    await projectsPage.createProject({
      name: originalName,
      path: testData.testProjectPath,
    });

    // 编辑项目
    const newName = testData.uniqueProjectName();
    await projectsPage.editProject(originalName, {
      name: newName,
      description: 'Updated description',
    });

    await projectsPage.expectProjectExists(newName);
    await projectsPage.expectProjectNotExists(originalName);
  });

  test('应该能够删除项目', async ({ projectsPage }) => {
    // 先创建一个项目
    const projectName = testData.uniqueProjectName();
    await projectsPage.createProject({
      name: projectName,
      path: testData.testProjectPath,
    });

    // 确认项目存在
    await projectsPage.expectProjectExists(projectName);

    // 删除项目
    await projectsPage.deleteProject(projectName);

    // 确认项目已删除
    await projectsPage.expectProjectNotExists(projectName);
  });

  test('应该能够启动项目', async ({ projectsPage }) => {
    // 创建项目
    const projectName = testData.uniqueProjectName();
    await projectsPage.createProject({
      name: projectName,
      path: testData.testProjectPath,
    });

    // 启动项目
    await projectsPage.launchProject(projectName);

    // 应该显示成功消息或状态变化
    await projectsPage.waitForLoadingToFinish();
  });

  test('应该能够搜索项目', async ({ projectsPage }) => {
    // 创建多个项目
    const projectName1 = `Search Project ${Date.now()}`;
    const projectName2 = `Other Project ${Date.now()}`;

    await projectsPage.createProject({
      name: projectName1,
      path: testData.testProjectPath,
    });
    await projectsPage.createProject({
      name: projectName2,
      path: '/tmp/other-project',
    });

    // 搜索特定项目
    await projectsPage.searchProjects('Search Project');

    // 验证搜索结果
    await projectsPage.expectProjectExists(projectName1);
  });

  test('应该在没有项目时显示空状态', async ({ projectsPage }) => {
    await projectsPage.searchInput.clear();
    await projectsPage.waitForLoadingToFinish();

    const projectCount = await projectsPage.getProjectCount();
    if (projectCount === 0) {
      await projectsPage.expectEmptyState();
    }
  });

  test('创建项目时应该验证必填字段', async ({ projectsPage }) => {
    await projectsPage.openCreateDialog();

    // 尝试提交空表单
    await projectsPage.submitButton.click();

    // 应该显示验证错误，对话框应该仍然打开
    await expect(projectsPage.projectDialog).toBeVisible();
  });

  test('应该能够取消创建项目', async ({ projectsPage }) => {
    await projectsPage.openCreateDialog();

    // 填写一些数据
    await projectsPage.projectNameInput.fill('Test Project');

    // 取消
    await projectsPage.cancelButton.click();

    // 对话框应该关闭
    await expect(projectsPage.projectDialog).not.toBeVisible();
  });

  test('应该验证项目路径', async ({ projectsPage }) => {
    await projectsPage.openCreateDialog();

    // 填写名称但使用无效路径
    await projectsPage.projectNameInput.fill('Test Project');
    await projectsPage.projectPathInput.fill('');

    // 尝试提交
    await projectsPage.submitButton.click();

    // 应该显示验证错误
    await expect(projectsPage.projectDialog).toBeVisible();
  });

  test('应该能够选择 CLI 类型', async ({ projectsPage, page }) => {
    await projectsPage.openCreateDialog();

    // 填写基本信息
    await projectsPage.projectNameInput.fill(testData.uniqueProjectName());
    await projectsPage.projectPathInput.fill(testData.testProjectPath);

    // 检查是否有 CLI 选择器
    const hasCLISelect = await projectsPage.cliSelect.isVisible().catch(() => false);

    if (hasCLISelect) {
      await projectsPage.cliSelect.click();

      // 应该显示 CLI 选项
      const options = page.getByRole('option');
      const optionCount = await options.count();
      expect(optionCount).toBeGreaterThan(0);
    }
  });

  test('应该能够选择终端类型', async ({ projectsPage, page }) => {
    await projectsPage.openCreateDialog();

    // 填写基本信息
    await projectsPage.projectNameInput.fill(testData.uniqueProjectName());
    await projectsPage.projectPathInput.fill(testData.testProjectPath);

    // 检查是否有终端选择器
    const hasTerminalSelect = await projectsPage.terminalSelect.isVisible().catch(() => false);

    if (hasTerminalSelect) {
      await projectsPage.terminalSelect.click();

      // 应该显示终端选项
      const options = page.getByRole('option');
      const optionCount = await options.count();
      expect(optionCount).toBeGreaterThan(0);
    }
  });
});
