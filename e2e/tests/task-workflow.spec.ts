import { test, expect, testData } from '../fixtures';

test.describe('任务工作流', () => {
  test.beforeEach(async ({ tasksPage }) => {
    await tasksPage.goto();
  });

  test('应该显示任务列表页面', async ({ tasksPage }) => {
    await expect(tasksPage.mainContent).toBeVisible();
    await expect(tasksPage.createTaskButton).toBeVisible();
  });

  test('应该能够创建新任务', async ({ tasksPage }) => {
    const taskName = testData.uniqueTaskName();

    await tasksPage.createTask({
      name: taskName,
      prompt: testData.testPrompt,
    });

    await tasksPage.expectTaskExists(taskName);
  });

  test('应该能够编辑任务', async ({ tasksPage }) => {
    // 先创建一个任务
    const originalName = testData.uniqueTaskName();
    await tasksPage.createTask({
      name: originalName,
      prompt: testData.testPrompt,
    });

    // 编辑任务
    const newName = testData.uniqueTaskName();
    await tasksPage.editTask(originalName, {
      name: newName,
      prompt: 'Updated prompt',
    });

    await tasksPage.expectTaskExists(newName);
    await tasksPage.expectTaskNotExists(originalName);
  });

  test('应该能够删除任务', async ({ tasksPage }) => {
    // 先创建一个任务
    const taskName = testData.uniqueTaskName();
    await tasksPage.createTask({
      name: taskName,
      prompt: testData.testPrompt,
    });

    // 确认任务存在
    await tasksPage.expectTaskExists(taskName);

    // 删除任务
    await tasksPage.deleteTask(taskName);

    // 确认任务已删除
    await tasksPage.expectTaskNotExists(taskName);
  });

  test('应该能够启动任务', async ({ tasksPage, projectsPage }) => {
    // 先创建一个项目
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

    // 启动任务
    await tasksPage.startTask(taskName);

    // 验证任务状态变为运行中
    await tasksPage.expectTaskStatus(taskName, /running|运行中/i);
  });

  test('应该能够停止运行中的任务', async ({ tasksPage, projectsPage }) => {
    // 先创建一个项目
    const projectName = testData.uniqueProjectName();
    await projectsPage.goto();
    await projectsPage.createProject({
      name: projectName,
      path: testData.testProjectPath,
    });

    // 创建并启动任务
    await tasksPage.goto();
    const taskName = testData.uniqueTaskName();
    await tasksPage.createTask({
      name: taskName,
      prompt: testData.testPrompt,
      project: projectName,
    });
    await tasksPage.startTask(taskName);

    // 停止任务
    await tasksPage.stopTask(taskName);

    // 验证任务状态变为已停止
    await tasksPage.expectTaskStatus(taskName, /stopped|pending|已停止|待处理/i);
  });

  test('应该能够搜索任务', async ({ tasksPage }) => {
    // 创建多个任务
    const taskName1 = `Search Test ${Date.now()}`;
    const taskName2 = `Other Task ${Date.now()}`;

    await tasksPage.createTask({
      name: taskName1,
      prompt: testData.testPrompt,
    });
    await tasksPage.createTask({
      name: taskName2,
      prompt: testData.testPrompt,
    });

    // 搜索特定任务
    await tasksPage.searchTasks('Search Test');

    // 验证搜索结果
    await tasksPage.expectTaskExists(taskName1);
    // 其他任务可能被过滤掉
  });

  test('应该在没有任务时显示空状态', async ({ tasksPage, page }) => {
    // 清空搜索以确保显示所有任务
    await tasksPage.searchInput.clear();
    await tasksPage.waitForLoadingToFinish();

    // 如果没有任务，应该显示空状态
    const taskCount = await tasksPage.getTaskCount();
    if (taskCount === 0) {
      await tasksPage.expectEmptyState();
    }
  });

  test('创建任务时应该验证必填字段', async ({ tasksPage }) => {
    await tasksPage.openCreateDialog();

    // 尝试提交空表单
    await tasksPage.submitButton.click();

    // 应该显示验证错误
    await expect(tasksPage.taskDialog).toBeVisible();
    // 表单应该仍然打开，因为验证失败
  });

  test('应该能够取消创建任务', async ({ tasksPage }) => {
    await tasksPage.openCreateDialog();

    // 填写一些数据
    await tasksPage.taskNameInput.fill('Test Task');

    // 取消
    await tasksPage.cancelButton.click();

    // 对话框应该关闭
    await expect(tasksPage.taskDialog).not.toBeVisible();
  });
});
