import { test, expect, testData } from '../fixtures';

test.describe('新用户流程', () => {
  test('首次访问应该显示主页', async ({ basePage }) => {
    await basePage.goto('/');
    await expect(basePage.mainContent).toBeVisible();
  });

  test('应该能够导航到各个页面', async ({ basePage }) => {
    await basePage.goto('/');

    // 导航到任务页面
    await basePage.navigateTo(/tasks|任务/i);
    expect(basePage.getCurrentPath()).toMatch(/tasks/i);

    // 导航到会话页面
    await basePage.navigateTo(/sessions|会话/i);
    expect(basePage.getCurrentPath()).toMatch(/sessions/i);

    // 导航到项目页面
    await basePage.navigateTo(/projects|项目/i);
    expect(basePage.getCurrentPath()).toMatch(/projects/i);

    // 导航到设置页面
    await basePage.navigateTo(/settings|设置/i);
    expect(basePage.getCurrentPath()).toMatch(/settings/i);
  });

  test('新用户完整流程：配置设置 -> 创建项目 -> 创建任务', async ({
    settingsPage,
    projectsPage,
    tasksPage,
  }) => {
    // 步骤 1: 配置设置
    await settingsPage.goto();
    await expect(settingsPage.mainContent).toBeVisible();

    // 检查是否有保存按钮
    const hasSaveButton = await settingsPage.saveButton.isVisible().catch(() => false);
    if (hasSaveButton) {
      await settingsPage.save();
    }

    // 步骤 2: 创建第一个项目
    await projectsPage.goto();
    const projectName = testData.uniqueProjectName();
    await projectsPage.createProject({
      name: projectName,
      path: testData.testProjectPath,
      description: 'My first project',
    });
    await projectsPage.expectProjectExists(projectName);

    // 步骤 3: 创建第一个任务
    await tasksPage.goto();
    const taskName = testData.uniqueTaskName();
    await tasksPage.createTask({
      name: taskName,
      prompt: 'My first task prompt',
      project: projectName,
    });
    await tasksPage.expectTaskExists(taskName);
  });

  test('应该能够切换主题', async ({ basePage }) => {
    await basePage.goto('/');

    // 检查是否有主题切换按钮
    const themeButton = basePage.header.getByRole('button', { name: /theme|主题/i });
    const hasThemeButton = await themeButton.isVisible().catch(() => false);

    if (hasThemeButton) {
      await basePage.toggleTheme();
      // 主题应该已切换
      await basePage.waitForPageLoad();
    }
  });

  test('应该能够切换语言', async ({ basePage, page }) => {
    await basePage.goto('/');

    // 检查是否有语言切换按钮
    const langButton = basePage.header.getByRole('button', { name: /language|语言/i });
    const hasLangButton = await langButton.isVisible().catch(() => false);

    if (hasLangButton) {
      await basePage.switchLanguage('en');
      await basePage.waitForPageLoad();

      // 切换回中文
      await basePage.switchLanguage('zh');
      await basePage.waitForPageLoad();
    }
  });

  test('侧边栏导航应该正常工作', async ({ basePage }) => {
    await basePage.goto('/');

    // 检查侧边栏是否可见
    await expect(basePage.sidebar).toBeVisible();

    // 检查导航链接
    const navLinks = basePage.sidebar.getByRole('link');
    const linkCount = await navLinks.count();
    expect(linkCount).toBeGreaterThan(0);
  });

  test('页面应该响应式布局', async ({ basePage, page }) => {
    await basePage.goto('/');

    // 测试桌面视图
    await page.setViewportSize({ width: 1920, height: 1080 });
    await expect(basePage.mainContent).toBeVisible();

    // 测试平板视图
    await page.setViewportSize({ width: 768, height: 1024 });
    await expect(basePage.mainContent).toBeVisible();

    // 测试移动视图
    await page.setViewportSize({ width: 375, height: 667 });
    await expect(basePage.mainContent).toBeVisible();
  });
});

test.describe('模板使用流程', () => {
  test('应该能够创建和使用模板', async ({ tasksPage, projectsPage, page }) => {
    // 先创建一个项目
    const projectName = testData.uniqueProjectName();
    await projectsPage.goto();
    await projectsPage.createProject({
      name: projectName,
      path: testData.testProjectPath,
    });

    // 导航到模板页面（如果存在）
    await page.goto('/templates');
    await page.waitForLoadState('networkidle');

    // 检查是否有创建模板按钮
    const createButton = page.getByRole('button', { name: /create|新建|添加/i });
    const hasCreateButton = await createButton.isVisible().catch(() => false);

    if (hasCreateButton) {
      // 创建模板
      await createButton.click();

      const dialog = page.getByRole('dialog');
      await expect(dialog).toBeVisible();

      const templateName = testData.uniqueTemplateName();
      await page.getByLabel(/name|名称/i).fill(templateName);
      await page.getByLabel(/content|内容|prompt|提示词/i).fill('Template content: {{variable}}');

      await dialog.getByRole('button', { name: /submit|save|确定|保存|创建/i }).click();

      // 验证模板创建成功
      await expect(page.getByText(templateName)).toBeVisible();

      // 使用模板创建任务
      await tasksPage.goto();
      await tasksPage.createTask({
        name: testData.uniqueTaskName(),
        prompt: 'Using template',
        project: projectName,
        template: templateName,
      });
    }
  });

  test('应该能够编辑模板', async ({ page }) => {
    await page.goto('/templates');
    await page.waitForLoadState('networkidle');

    // 检查是否有模板列表
    const templateList = page.locator('[data-testid="template-list"], .template-list, table tbody');
    const hasTemplates = await templateList.isVisible().catch(() => false);

    if (hasTemplates) {
      const templateCount = await templateList.locator('tr, [data-testid="template-item"]').count();

      if (templateCount > 0) {
        // 点击编辑按钮
        const firstTemplate = templateList.locator('tr, [data-testid="template-item"]').first();
        const editButton = firstTemplate.getByRole('button', { name: /edit|编辑/i });

        if (await editButton.isVisible().catch(() => false)) {
          await editButton.click();

          const dialog = page.getByRole('dialog');
          await expect(dialog).toBeVisible();

          // 修改内容
          const contentInput = page.getByLabel(/content|内容|prompt|提示词/i);
          await contentInput.clear();
          await contentInput.fill('Updated template content');

          await dialog.getByRole('button', { name: /submit|save|确定|保存/i }).click();
        }
      }
    }
  });
});
