/**
 * Test Utilities
 * 测试工具函数和 Wrapper
 */
import React from 'react'
import { render, RenderOptions } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { I18nextProvider } from 'react-i18next'
import i18n from 'i18next'

// 初始化简化的 i18n 实例用于测试
i18n.init({
  lng: 'zh',
  fallbackLng: 'zh',
  ns: ['translation'],
  defaultNS: 'translation',
  interpolation: {
    escapeValue: false,
  },
  resources: {
    zh: {
      translation: {
        common: {
          cancel: '取消',
          save: '保存',
          create: '创建',
          delete: '删除',
          edit: '编辑',
          confirm: '确认',
          loading: '加载中...',
          success: '操作成功',
          error: '操作失败',
        },
        tasks: {
          form: {
            title: { create: '创建任务', edit: '编辑任务' },
            project: '项目',
            projectPlaceholder: '选择项目',
            projectRequired: '请选择项目',
            docPath: '文档路径',
            docPathPlaceholder: '输入文档相对路径',
            docPathRequired: '请输入文档路径',
            cliType: 'CLI 类型',
            cliTypePlaceholder: '选择 CLI 类型',
            cliTypeDefault: '使用项目默认',
            enableReview: '启用审查',
            reviewInherit: '继承项目设置',
            reviewEnabled: '启用',
            reviewDisabled: '禁用',
            createSuccess: '任务创建成功',
            updateSuccess: '任务更新成功',
            createFailed: '任务创建失败',
            updateFailed: '任务更新失败',
          },
        },
        projects: {
          dialog: {
            title: { create: '创建项目', edit: '编辑项目' },
            form: {
              name: '项目名称',
              namePlaceholder: '输入项目名称',
              nameRequired: '请输入项目名称',
              directory: '项目目录',
              directoryPlaceholder: '输入项目目录路径',
              directoryRequired: '请输入项目目录',
              description: '描述',
              descriptionPlaceholder: '输入项目描述（可选）',
            },
          },
          createSuccess: '项目创建成功',
          updateSuccess: '项目更新成功',
          createFailed: '项目创建失败',
          updateFailed: '项目更新失败',
        },
        templates: {
          dialog: {
            title: { create: '创建模板', edit: '编辑模板' },
            form: {
              name: '模板名称',
              namePlaceholder: '输入模板名称',
              nameRequired: '请输入模板名称',
              type: '模板类型',
              typePlaceholder: '选择模板类型',
              description: '描述',
              descriptionPlaceholder: '输入模板描述（可选）',
              content: '模板内容',
              contentPlaceholder: '输入模板内容',
              contentRequired: '请输入模板内容',
              variablesHint: '可用变量:',
            },
          },
          types: {
            initial_task: '初始任务',
            continue_task: '继续任务',
            resume_task: '恢复任务',
            status_check: '状态检查',
            review: '审查',
            planning: '规划',
          },
          createSuccess: '模板创建成功',
          updateSuccess: '模板更新成功',
          createFailed: '模板创建失败',
          updateFailed: '模板更新失败',
        },
        sidebar: {
          title: 'AI Task Runner',
          subtitle: '智能任务管理',
          nav: {
            tasks: '任务',
            sessions: '会话',
            logs: '日志',
            templates: '模板',
            projects: '项目',
            settings: '设置',
          },
        },
        header: {
          toggleTheme: '切换主题',
        },
        errorBoundary: {
          title: '页面出错了',
          description: '抱歉，页面出现了错误',
          reload: '重新加载',
        },
      },
    },
    en: {
      translation: {
        common: {
          cancel: 'Cancel',
          save: 'Save',
          create: 'Create',
          delete: 'Delete',
          edit: 'Edit',
          confirm: 'Confirm',
          loading: 'Loading...',
          success: 'Success',
          error: 'Error',
        },
      },
    },
  },
})

// 测试用的 Wrapper 组件
const AllProviders = ({ children }: { children: React.ReactNode }) => {
  return (
    <BrowserRouter>
      <I18nextProvider i18n={i18n}>
        {children}
      </I18nextProvider>
    </BrowserRouter>
  )
}

// 自定义 render 函数
const customRender = (
  ui: React.ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>
) => render(ui, { wrapper: AllProviders, ...options })

// 重新导出所有 testing-library 的函数
export * from '@testing-library/react'
export { customRender as render }
export { i18n }
