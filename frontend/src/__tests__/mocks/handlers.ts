/**
 * MSW Request Handlers
 * API Mock 请求处理器
 */
import { http, HttpResponse } from 'msw'

// 使用相对路径匹配，因为测试环境中 axios baseURL 是 '/api'
const API_BASE = '/api'

// Sample mock data
const mockTasks = [
  {
    id: 'task_1',
    name: 'Test Task 1',
    description: 'First test task',
    status: 'pending',
    project_directory: '/tmp/project1',
    markdown_document_path: '/tmp/project1/TODO.md',
    cli_type: 'claude_code',
    created_at: '2025-01-01T00:00:00Z',
    updated_at: '2025-01-01T00:00:00Z'
  },
  {
    id: 'task_2',
    name: 'Test Task 2',
    description: 'Second test task',
    status: 'in_progress',
    project_directory: '/tmp/project2',
    markdown_document_path: '/tmp/project2/TODO.md',
    cli_type: 'claude_code',
    created_at: '2025-01-01T00:00:00Z',
    updated_at: '2025-01-01T00:00:00Z'
  }
]

const mockProjects = [
  {
    id: 'proj_1',
    name: 'Test Project 1',
    description: 'First test project',
    directory_path: '/tmp/project1',
    created_at: '2025-01-01T00:00:00Z',
    updated_at: '2025-01-01T00:00:00Z'
  }
]

const mockSessions = [
  {
    task_id: 'task_2',
    status: 'running',
    is_running: true,
    context_usage: 50,
    context_tokens: 50000,
    max_tokens: 100000
  }
]

const mockSettings = {
  default_cli: 'claude_code',
  terminal: 'auto',
  language: 'zh',
  api_base_url: 'http://127.0.0.1:8086'
}

const mockTemplates = [
  {
    id: 'tmpl_1',
    name: 'initial_task',
    type: 'initial_task',
    locale: 'zh',
    content: 'Initial task template content',
    is_default: true,
    created_at: '2025-01-01T00:00:00Z',
    updated_at: '2025-01-01T00:00:00Z'
  }
]

export const handlers = [
  // Init API
  http.get(`${API_BASE}/init`, () => {
    return HttpResponse.json({
      tasks: mockTasks,
      sessions: {
        sessions: mockSessions,
        count: mockSessions.length,
        max_concurrent: 5
      },
      projects: mockProjects,
      settings: { settings: mockSettings }
    })
  }),

  // Tasks API
  http.get(`${API_BASE}/tasks`, () => {
    return HttpResponse.json(mockTasks)
  }),

  http.get(`${API_BASE}/tasks/:taskId`, ({ params }) => {
    const task = mockTasks.find(t => t.id === params.taskId)
    if (!task) {
      return new HttpResponse(null, { status: 404 })
    }
    return HttpResponse.json(task)
  }),

  http.post(`${API_BASE}/tasks`, async ({ request }) => {
    const body = await request.json() as Record<string, unknown>
    const newTask = {
      id: `task_${Date.now()}`,
      ...body,
      status: 'pending',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    }
    return HttpResponse.json(newTask, { status: 201 })
  }),

  http.put(`${API_BASE}/tasks/:taskId`, async ({ params, request }) => {
    const body = await request.json() as Record<string, unknown>
    const task = mockTasks.find(t => t.id === params.taskId)
    if (!task) {
      return new HttpResponse(null, { status: 404 })
    }
    const updatedTask = { ...task, ...body, updated_at: new Date().toISOString() }
    return HttpResponse.json(updatedTask)
  }),

  http.delete(`${API_BASE}/tasks/:taskId`, ({ params }) => {
    const taskIndex = mockTasks.findIndex(t => t.id === params.taskId)
    if (taskIndex === -1) {
      return new HttpResponse(null, { status: 404 })
    }
    return HttpResponse.json({ success: true, message: `Task ${params.taskId} deleted` })
  }),

  http.post(`${API_BASE}/tasks/:taskId/start`, ({ params }) => {
    return HttpResponse.json({
      success: true,
      message: `CLI session started for task ${params.taskId}`,
      task_id: params.taskId
    })
  }),

  http.post(`${API_BASE}/tasks/:taskId/pause`, ({ params }) => {
    return HttpResponse.json({
      success: true,
      message: `Task ${params.taskId} paused`,
      task_id: params.taskId
    })
  }),

  // Sessions API
  http.get(`${API_BASE}/sessions`, () => {
    return HttpResponse.json({
      sessions: mockSessions,
      total: mockSessions.length,
      active: mockSessions.filter(s => s.is_running).length,
      max_concurrent: 5,
      available_slots: 4
    })
  }),

  http.get(`${API_BASE}/sessions/:taskId`, ({ params }) => {
    const session = mockSessions.find(s => s.task_id === params.taskId)
    if (!session) {
      return new HttpResponse(null, { status: 404 })
    }
    return HttpResponse.json(session)
  }),

  // Projects API
  http.get(`${API_BASE}/projects`, () => {
    return HttpResponse.json(mockProjects)
  }),

  http.get(`${API_BASE}/projects/:projectId`, ({ params }) => {
    const project = mockProjects.find(p => p.id === params.projectId)
    if (!project) {
      return new HttpResponse(null, { status: 404 })
    }
    return HttpResponse.json(project)
  }),

  http.post(`${API_BASE}/projects`, async ({ request }) => {
    const body = await request.json() as Record<string, unknown>
    const newProject = {
      id: `proj_${Date.now()}`,
      ...body,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    }
    return HttpResponse.json(newProject, { status: 201 })
  }),

  // Templates API
  http.get(`${API_BASE}/templates`, () => {
    return HttpResponse.json(mockTemplates)
  }),

  // Settings API
  http.get(`${API_BASE}/settings`, () => {
    return HttpResponse.json({ settings: mockSettings })
  }),

  http.put(`${API_BASE}/settings/:key`, async ({ params, request }) => {
    const body = await request.json() as { value: unknown }
    return HttpResponse.json({
      success: true,
      key: params.key,
      value: body.value
    })
  }),

  // Health check
  http.get('/health', () => {
    return HttpResponse.json({ status: 'healthy', timestamp: new Date().toISOString() })
  })
]
