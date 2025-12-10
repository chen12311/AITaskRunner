import { useEffect, useState, useMemo, useCallback } from 'react'
import { RefreshCw, Search } from 'lucide-react'
import { format } from 'date-fns'
import { enUS, zhCN } from 'date-fns/locale'
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
import { Skeleton } from '@/components/ui/skeleton'

import { useTaskStore } from '@/stores'
import { logApi } from '@/api'
import type { Log, LogLevel } from '@/types'

const LOG_ROW_HEIGHT = 34
const LOG_VIEWPORT_HEIGHT = 500
const LOG_OVERSCAN = 8

export function Component() {
  const { t, i18n } = useTranslation()
  const { tasks, fetchTasks } = useTaskStore()
  const [selectedTaskId, setSelectedTaskId] = useState<string>('')
  const [logs, setLogs] = useState<Log[]>([])
  const [loading, setLoading] = useState(false)
  const [levelFilter, setLevelFilter] = useState<LogLevel | 'all'>('all')
  const [search, setSearch] = useState('')
  const [scrollTop, setScrollTop] = useState(0)
  const currentLocale = useMemo(() => i18n.language.startsWith('zh') ? zhCN : enUS, [i18n.language])

  const loadLogs = useCallback(async (taskId: string) => {
    setLoading(true)
    try {
      const response = await logApi.getTaskLogs(taskId, 500)
      // 后端返回 {logs: [...], total: number}
      setLogs(response.logs || [])
      setScrollTop(0)
    } catch (error) {
      console.error('Failed to load logs:', error)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchTasks()
  }, [fetchTasks])

  useEffect(() => {
    if (selectedTaskId) {
      loadLogs(selectedTaskId)
    } else {
      setLogs([])
    }
  }, [selectedTaskId, loadLogs])

  const filteredLogs = useMemo(() => {
    return logs.filter((log) => {
      const matchesLevel = levelFilter === 'all' || log.level === levelFilter
      const matchesSearch = search
        ? log.message.toLowerCase().includes(search.toLowerCase())
        : true
      return matchesLevel && matchesSearch
    })
  }, [logs, levelFilter, search])

  const virtualizedLogs = useMemo(() => {
    const totalHeight = filteredLogs.length * LOG_ROW_HEIGHT
    const startIndex = Math.max(0, Math.floor(scrollTop / LOG_ROW_HEIGHT) - LOG_OVERSCAN)
    const endIndex = Math.min(
      filteredLogs.length,
      Math.ceil((scrollTop + LOG_VIEWPORT_HEIGHT) / LOG_ROW_HEIGHT) + LOG_OVERSCAN
    )

    return {
      totalHeight,
      offsetY: startIndex * LOG_ROW_HEIGHT,
      visibleLogs: filteredLogs.slice(startIndex, endIndex),
    }
  }, [filteredLogs, scrollTop])

  const handleScroll = useCallback((event: React.UIEvent<HTMLDivElement>) => {
    setScrollTop(event.currentTarget.scrollTop)
  }, [])

  const getLevelColor = useCallback((level: LogLevel) => {
    switch (level) {
      case 'ERROR':
        return 'text-red-400'
      case 'WARNING':
        return 'text-orange-400'
      case 'INFO':
        return 'text-foreground'
      case 'DEBUG':
        return 'text-muted-foreground'
      default:
        return 'text-muted-foreground'
    }
  }, [])

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">{t('logs.title')}</h1>
      </div>

      <Card>
        <CardHeader className="pb-4">
          <div className="flex items-center gap-4">
            <Select value={selectedTaskId} onValueChange={setSelectedTaskId}>
              <SelectTrigger className="w-[300px]">
                <SelectValue placeholder={t('logs.selectTask')} />
              </SelectTrigger>
              <SelectContent>
                {tasks.map((task) => (
                  <SelectItem key={task.id} value={task.id}>
                    {task.project_name} - {(task.doc_path || task.markdown_document_path || '').slice(0, 30)}...
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select
              value={levelFilter}
              onValueChange={(v) => setLevelFilter(v as LogLevel | 'all')}
            >
              <SelectTrigger className="w-[140px]">
                <SelectValue placeholder={t('logs.levelFilter')} />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">{t('logs.levels.all')}</SelectItem>
                <SelectItem value="INFO">{t('logs.levels.INFO')}</SelectItem>
                <SelectItem value="WARNING">{t('logs.levels.WARNING')}</SelectItem>
                <SelectItem value="ERROR">{t('logs.levels.ERROR')}</SelectItem>
                <SelectItem value="DEBUG">{t('logs.levels.DEBUG')}</SelectItem>
              </SelectContent>
            </Select>
            <div className="relative flex-1 max-w-sm">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder={t('logs.searchPlaceholder')}
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-9"
              />
            </div>
            <Button
              variant="outline"
              size="icon"
              onClick={() => selectedTaskId && loadLogs(selectedTaskId)}
              disabled={!selectedTaskId}
            >
              <RefreshCw className="h-4 w-4" />
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {!selectedTaskId ? (
            <div className="text-center text-muted-foreground py-12">{t('logs.selectTaskPrompt')}</div>
          ) : loading ? (
            <div className="space-y-2">
              {[1, 2, 3, 4, 5].map((i) => (
                <Skeleton key={i} className="h-6 w-full" />
              ))}
            </div>
          ) : (
            <div className="bg-muted rounded-lg">
              <div
                className="h-[500px] overflow-auto"
                onScroll={handleScroll}
                style={{ scrollbarWidth: 'thin' }}
              >
                {filteredLogs.length === 0 ? (
                  <div className="text-muted-foreground text-sm text-center py-8">{t('logs.noData')}</div>
                ) : (
                  <div
                    className="relative"
                    style={{ height: Math.max(virtualizedLogs.totalHeight, LOG_VIEWPORT_HEIGHT) }}
                  >
                    <div style={{ transform: `translateY(${virtualizedLogs.offsetY}px)` }}>
                      {virtualizedLogs.visibleLogs.map((log) => (
                        <div
                          key={log.id}
                          className="font-mono text-sm flex items-start gap-2 py-1 px-4"
                          style={{ height: LOG_ROW_HEIGHT }}
                        >
                          <span className="text-muted-foreground flex-shrink-0">
                            {format(new Date(log.timestamp || log.created_at || ''), 'HH:mm:ss', { locale: currentLocale })}
                          </span>
                          <Badge
                            variant="outline"
                            className={`${getLevelColor(log.level)} flex-shrink-0 text-xs px-1.5`}
                          >
                            {log.level}
                          </Badge>
                          <span className="text-muted-foreground flex-shrink-0">
                            [{log.task_id.slice(0, 8)}]
                          </span>
                          <span className="text-foreground break-all">{log.message}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

Component.displayName = 'Logs'
