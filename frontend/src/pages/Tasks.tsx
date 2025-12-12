import { useEffect, useState, useMemo, useCallback, Fragment, lazy, Suspense, memo } from 'react'
import { Plus, RefreshCw, ChevronDown, ChevronRight, Play, Edit, Trash2, Search } from 'lucide-react'
import { format } from 'date-fns'
import { enUS, zhCN } from 'date-fns/locale'
import { toast } from 'sonner'
import { useTranslation } from 'react-i18next'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader } from '@/components/ui/card'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog'
import { Skeleton } from '@/components/ui/skeleton'

import { useTaskStore, useProjectStore, useSessionStore } from '@/stores'
import type { Task, TaskStatus } from '@/types'
import { logApi, initApi } from '@/api'
import { useWebSocket } from '@/hooks'

// 优化10.3: 延迟加载 TaskDialog 组件
const TaskDialog = lazy(() => import('@/components/TaskDialog'))

const statusVariants: Record<TaskStatus, 'default' | 'secondary' | 'destructive' | 'outline'> = {
  pending: 'secondary',
  in_progress: 'default',
  in_reviewing: 'outline',
  completed: 'default',
  failed: 'destructive',
}

export function Component() {
  const { t, i18n } = useTranslation()
  const { tasks, loading, fetchTasks, setTasks, deleteTask, startTask } = useTaskStore()
  const { projects, setProjects } = useProjectStore()
  const { sessions, setSessions } = useSessionStore()

  // 优化7.1-7.3: 使用 WebSocket 替代轮询
  useWebSocket({ enabled: true })

  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState<TaskStatus | 'all'>('all')
  const [currentPage, setCurrentPage] = useState(1)
  const pageSize = 20
  const [expandedRows, setExpandedRows] = useState<Set<string>>(new Set())
  const [taskLogs, setTaskLogs] = useState<Record<string, { level: string; message: string; created_at?: string; timestamp?: string }[]>>({})
  const [taskLogsTimestamp, setTaskLogsTimestamp] = useState<Record<string, number>>({}) // 日志缓存时间戳
  const [loadingLogs, setLoadingLogs] = useState<Set<string>>(new Set()) // 正在加载的任务ID
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [taskToDelete, setTaskToDelete] = useState<string | null>(null)
  const [dialogOpen, setDialogOpen] = useState(false)
  const [editingTask, setEditingTask] = useState<Task | null>(null)
  const [maxConcurrent, setMaxConcurrent] = useState<number>(3)
  const currentLocale = useMemo(() => i18n.language.startsWith('zh') ? zhCN : enUS, [i18n.language])

  // 优化1.1: 合并初始化请求为单个 /api/init 接口
  useEffect(() => {
    initApi.getInitData()
      .then((response) => {
        // 批量设置所有数据
        setTasks(response.tasks)
        setSessions(response.sessions)
        setProjects(response.projects)

        // 设置 max_concurrent_sessions
        const maxConcValue = response.settings?.settings?.max_concurrent_sessions?.value
        if (maxConcValue) {
          setMaxConcurrent(Number(maxConcValue))
        }
      })
      .catch((error) => {
        console.error('Failed to load init data:', error)
      })
    // 优化7.2: 移除轮询，改用 WebSocket 推送
  }, [setTasks, setSessions, setProjects])

  const filteredTasks = useMemo(() => {
    return tasks.filter((task) => {
      const matchesSearch = search
        ? task.project_name?.toLowerCase().includes(search.toLowerCase()) ||
          task.doc_path?.toLowerCase().includes(search.toLowerCase()) ||
          task.project_directory?.toLowerCase().includes(search.toLowerCase()) ||
          task.markdown_document_path?.toLowerCase().includes(search.toLowerCase())
        : true
      const matchesStatus = statusFilter === 'all' || task.status === statusFilter
      return matchesSearch && matchesStatus
    })
  }, [tasks, search, statusFilter])

  const totalPages = Math.ceil(filteredTasks.length / pageSize)
  const paginatedTasks = useMemo(() => {
    const start = (currentPage - 1) * pageSize
    return filteredTasks.slice(start, start + pageSize)
  }, [filteredTasks, currentPage])

  // 筛选条件变化时重置页码
  useEffect(() => {
    setCurrentPage(1)
  }, [search, statusFilter])

  const activeSessionCount = sessions.length

  // 优化8.1: 添加日志缓存时间戳，超过30秒才重新请求
  // 优化8.2: 添加loading状态，防止重复点击
  const LOG_CACHE_TTL = 30 * 1000 // 30秒缓存过期

  const toggleRow = useCallback(async (taskId: string) => {
    setExpandedRows((prev) => {
      const newExpanded = new Set(prev)
      if (newExpanded.has(taskId)) {
        newExpanded.delete(taskId)
      } else {
        newExpanded.add(taskId)

        // 检查是否正在加载
        if (loadingLogs.has(taskId)) {
          return newExpanded
        }

        // 检查缓存是否过期
        const cachedAt = taskLogsTimestamp[taskId]
        const isExpired = !cachedAt || (Date.now() - cachedAt > LOG_CACHE_TTL)

        if (!taskLogs[taskId] || isExpired) {
          // 标记为正在加载
          setLoadingLogs((p) => new Set(p).add(taskId))

          logApi.getTaskLogs(taskId, 10).then((response) => {
            if (response.logs) {
              setTaskLogs((p) => ({ ...p, [taskId]: response.logs }))
              setTaskLogsTimestamp((p) => ({ ...p, [taskId]: Date.now() }))
            }
          }).catch(console.error).finally(() => {
            // 移除加载状态
            setLoadingLogs((p) => {
              const newSet = new Set(p)
              newSet.delete(taskId)
              return newSet
            })
          })
        }
      }
      return newExpanded
    })
  }, [taskLogs, taskLogsTimestamp, loadingLogs])

  const handleDelete = useCallback(async () => {
    if (!taskToDelete) return
    try {
      await deleteTask(taskToDelete)
      toast.success(t('tasks.deleteSuccess'))
    } catch {
      toast.error(t('tasks.deleteFailed'))
    }
    setDeleteDialogOpen(false)
    setTaskToDelete(null)
  }, [taskToDelete, deleteTask, t])

  const handleStart = useCallback(async (taskId: string) => {
    try {
      await startTask(taskId)
      toast.success(t('tasks.startSuccess'))
    } catch {
      toast.error(t('tasks.startFailed'))
    }
  }, [startTask, t])

  const handleEdit = useCallback((task: Task) => {
    setEditingTask(task)
    setDialogOpen(true)
  }, [])

  const handleCreate = useCallback(() => {
    setEditingTask(null)
    setDialogOpen(true)
  }, [])

  const getCliLabel = (cliType?: string | null) => {
    if (!cliType) return '-'
    const translationKey = `settings.clis.${cliType}` as const
    const translated = t(translationKey, { defaultValue: cliType })
    return translated || cliType
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <h1 className="text-2xl font-bold">{t('tasks.title')}</h1>
          <Badge variant="outline">
            {t('tasks.runningCount', { current: activeSessionCount, max: maxConcurrent })}
          </Badge>
        </div>
        <Button onClick={handleCreate}>
          <Plus className="h-4 w-4 mr-2" />
          {t('tasks.createTask')}
        </Button>
      </div>

      <Card>
        <CardHeader className="pb-4">
          <div className="flex items-center gap-4">
            <div className="relative flex-1 max-w-sm">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder={t('tasks.searchPlaceholder')}
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-9"
              />
            </div>
            <Select value={statusFilter} onValueChange={(v) => setStatusFilter(v as TaskStatus | 'all')}>
              <SelectTrigger className="w-[140px]">
                <SelectValue placeholder={t('tasks.statusFilter')} />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">{t('tasks.status.all')}</SelectItem>
                <SelectItem value="pending">{t('tasks.status.pending')}</SelectItem>
                <SelectItem value="in_progress">{t('tasks.status.in_progress')}</SelectItem>
                <SelectItem value="in_reviewing">{t('tasks.status.in_reviewing')}</SelectItem>
                <SelectItem value="completed">{t('tasks.status.completed')}</SelectItem>
                <SelectItem value="failed">{t('tasks.status.failed')}</SelectItem>
              </SelectContent>
            </Select>
            <Button variant="outline" size="icon" onClick={() => fetchTasks()}>
              <RefreshCw className="h-4 w-4" />
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="space-y-4">
              {[1, 2, 3].map((i) => (
                <Skeleton key={i} className="h-12 w-full" />
              ))}
            </div>
          ) : (
            <div className="overflow-x-auto">
            <Table className="table-fixed w-full">
              <TableHeader>
                <TableRow>
                  <TableHead className="w-8"></TableHead>
                  <TableHead className="w-[150px]">{t('tasks.table.taskId')}</TableHead>
                  <TableHead className="w-[180px]">{t('tasks.table.projectName')}</TableHead>
                  <TableHead className="w-[200px]">{t('tasks.table.docPath')}</TableHead>
                  <TableHead className="w-[100px]">{t('tasks.table.status')}</TableHead>
                  <TableHead className="w-[100px]">{t('tasks.table.cliType')}</TableHead>
                  <TableHead className="w-[160px]">{t('tasks.table.createdAt')}</TableHead>
                  <TableHead className="w-[120px]">{t('tasks.table.actions')}</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {paginatedTasks.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={8} className="text-center text-muted-foreground py-8">
                      {t('tasks.noData')}
                    </TableCell>
                  </TableRow>
                ) : (
                  paginatedTasks.map((task) => (
                    <Fragment key={task.id}>
                      <TableRow key={task.id} className="cursor-pointer" onClick={() => toggleRow(task.id)}>
                        <TableCell>
                          {expandedRows.has(task.id) ? (
                            <ChevronDown className="h-4 w-4" />
                          ) : (
                            <ChevronRight className="h-4 w-4" />
                          )}
                        </TableCell>
                        <TableCell className="font-mono text-xs">{task.id}</TableCell>
                        <TableCell className="truncate">{task.project_name}</TableCell>
                        <TableCell className="max-w-[200px] truncate">{task.doc_path}</TableCell>
                        <TableCell>
                          <Badge
                            variant={statusVariants[task.status] || 'secondary'}
                            className={
                              task.status === 'in_progress'
                                ? 'bg-yellow-500'
                                : task.status === 'completed'
                                ? 'bg-green-500'
                                : task.status === 'in_reviewing'
                                ? 'bg-blue-500'
                                : ''
                            }
                          >
                            {t(`tasks.status.${task.status}`)}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <Badge variant="outline">{getCliLabel(task.cli_type)}</Badge>
                        </TableCell>
                        <TableCell className="text-muted-foreground text-sm">
                          {format(new Date(task.created_at), 'yyyy-MM-dd HH:mm', { locale: currentLocale })}
                        </TableCell>
                        <TableCell onClick={(e) => e.stopPropagation()}>
                          <div className="flex items-center gap-1">
                            <Button
                              variant="ghost"
                              size="icon"
                              onClick={() => handleStart(task.id)}
                            >
                              <Play className="h-4 w-4" />
                            </Button>
                            <Button variant="ghost" size="icon" onClick={() => handleEdit(task)}>
                              <Edit className="h-4 w-4" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="icon"
                              onClick={() => {
                                setTaskToDelete(task.id)
                                setDeleteDialogOpen(true)
                              }}
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                      {expandedRows.has(task.id) && (
                        <TableRow>
                          <TableCell colSpan={8} className="bg-muted/50 p-4">
                            <div className="space-y-4">
                              <div className="grid grid-cols-2 gap-4 text-sm">
                                <div>
                                  <span className="text-muted-foreground">{t('tasks.details.projectDirectory')}</span>
                                  <span className="ml-2">{task.project_directory}</span>
                                </div>
                                <div>
                                  <span className="text-muted-foreground">{t('tasks.details.documentPath')}</span>
                                  <span className="ml-2">{task.markdown_document_path || '-'}</span>
                                </div>
                              </div>
                              <div>
                                <h4 className="text-sm font-medium mb-2">{t('tasks.details.executionLogs')}</h4>
                                <div className="bg-muted rounded-md p-3 max-h-[200px] overflow-auto">
                                  {taskLogs[task.id]?.length ? (
                                    taskLogs[task.id].map((log, idx) => (
                                      <div key={idx} className="text-xs font-mono text-foreground py-1">
                                        <span
                                          className={
                                            log.level === 'ERROR'
                                              ? 'text-red-400'
                                              : log.level === 'WARNING'
                                              ? 'text-yellow-400'
                                              : 'text-muted-foreground'
                                          }
                                        >
                                          [{log.level}]
                                        </span>
                                        <span className="text-muted-foreground mx-2">
                                          {format(new Date(log.created_at || log.timestamp || new Date()), 'HH:mm:ss', { locale: currentLocale })}
                                        </span>
                                        {log.message}
                                      </div>
                                    ))
                                  ) : (
                                    <div className="text-muted-foreground text-xs">{t('tasks.details.noLogs')}</div>
                                  )}
                                </div>
                              </div>
                            </div>
                          </TableCell>
                        </TableRow>
                      )}
                    </Fragment>
                  ))
                )}
              </TableBody>
            </Table>
            </div>
          )}
          {totalPages > 1 && (
            <div className="flex items-center justify-between mt-4">
              <span className="text-sm text-muted-foreground">
                {t('common.pagination', { current: currentPage, total: totalPages, count: filteredTasks.length })}
              </span>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                  disabled={currentPage === 1}
                >
                  {t('common.prev')}
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                  disabled={currentPage === totalPages}
                >
                  {t('common.next')}
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>{t('tasks.dialog.deleteTitle')}</AlertDialogTitle>
            <AlertDialogDescription>{t('tasks.dialog.deleteDescription')}</AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>{t('common.cancel')}</AlertDialogCancel>
            <AlertDialogAction onClick={handleDelete}>{t('tasks.dialog.confirmDelete')}</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* 优化10.3: 延迟加载 TaskDialog */}
      <Suspense fallback={null}>
        <TaskDialog
          open={dialogOpen}
          onOpenChange={setDialogOpen}
          task={editingTask}
          projects={projects}
        />
      </Suspense>
    </div>
  )
}

Component.displayName = 'Tasks'
