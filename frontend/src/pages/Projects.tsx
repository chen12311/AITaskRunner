import { useEffect, useState, useCallback } from 'react'
import { Plus, Edit, Trash2, Play, ChevronDown, Terminal, Zap } from 'lucide-react'
import { toast } from 'sonner'
import { useTranslation } from 'react-i18next'

import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
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
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { Switch } from '@/components/ui/switch'
import { Label } from '@/components/ui/label'
import { Skeleton } from '@/components/ui/skeleton'

import { useProjectStore } from '@/stores'
import { projectApi } from '@/api/projects'
import { settingsApi } from '@/api/settings'
import type { Project } from '@/types'
import ProjectDialog from '@/components/ProjectDialog'

export function Component() {
  const { t } = useTranslation()
  const { projects, loading, fetchProjects, deleteProject } = useProjectStore()
  const [dialogOpen, setDialogOpen] = useState(false)
  const [editingProject, setEditingProject] = useState<Project | null>(null)
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [projectToDelete, setProjectToDelete] = useState<string | null>(null)
  const [currentTerminal, setCurrentTerminal] = useState<string>('')
  const [dangerousModeEnabled, setDangerousModeEnabled] = useState(false)

  useEffect(() => {
    fetchProjects()
    // 获取当前终端设置
    settingsApi.getAvailableTerminals().then(res => {
      setCurrentTerminal(res.current)
    }).catch(() => {})
  }, [fetchProjects])

  const handleEdit = useCallback((project: Project) => {
    setEditingProject(project)
    setDialogOpen(true)
  }, [])

  // 解析启动错误消息并返回国际化文本
  const getLaunchErrorMessage = useCallback((detail: string | undefined): string => {
    if (!detail) return t('projects.launchFailed')

    if (detail === 'Project not found') {
      return t('projects.launchErrors.projectNotFound')
    }
    if (detail === 'Project directory not configured') {
      return t('projects.launchErrors.directoryNotConfigured')
    }
    if (detail.startsWith('Project directory does not exist:')) {
      const path = detail.replace('Project directory does not exist:', '').trim()
      return t('projects.launchErrors.directoryNotExist', { path })
    }
    if (detail === 'No terminal adapter available') {
      return t('projects.launchErrors.noTerminalAdapter')
    }
    if (detail === 'Failed to create terminal window') {
      return t('projects.launchErrors.createWindowFailed')
    }
    if (detail.startsWith('Failed to launch terminal:')) {
      const error = detail.replace('Failed to launch terminal:', '').trim()
      return t('projects.launchErrors.launchTerminalFailed', { error })
    }

    return t('projects.launchFailed')
  }, [t])

  // 启动项目 - 使用默认设置（快速启动，Claude Code）
  const handleQuickLaunch = useCallback(async (projectId: string) => {
    try {
      const result = await projectApi.launchProject(projectId, { mode: 'cli', dangerousMode: dangerousModeEnabled })
      if (result.success) {
        toast.success(t('projects.launchSuccess'))
      }
    } catch (error) {
      const detail = (error as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      toast.error(getLaunchErrorMessage(detail))
    }
  }, [t, dangerousModeEnabled, getLaunchErrorMessage])

  // 使用指定 CLI 启动
  const handleLaunchWithCli = useCallback(async (projectId: string, cli: string) => {
    try {
      const result = await projectApi.launchProject(projectId, { command: cli, dangerousMode: dangerousModeEnabled })
      if (result.success) {
        toast.success(t('projects.launchSuccess'))
      }
    } catch (error) {
      const detail = (error as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      toast.error(getLaunchErrorMessage(detail))
    }
  }, [t, dangerousModeEnabled, getLaunchErrorMessage])

  const handleCreate = useCallback(() => {
    setEditingProject(null)
    setDialogOpen(true)
  }, [])

  const handleDelete = useCallback(async () => {
    if (projectToDelete === null) return
    try {
      await deleteProject(projectToDelete)
      toast.success(t('projects.deleteSuccess'))
    } catch {
      toast.error(t('projects.deleteFailed'))
    }
    setDeleteDialogOpen(false)
    setProjectToDelete(null)
  }, [projectToDelete, deleteProject, t])

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">{t('projects.title')}</h1>
        <Button onClick={handleCreate}>
          <Plus className="h-4 w-4 mr-2" />
          {t('projects.createProject')}
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>{t('projects.title')}</CardTitle>
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
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>{t('projects.table.name')}</TableHead>
                  <TableHead>{t('projects.table.directory')}</TableHead>
                  <TableHead>{t('projects.table.description')}</TableHead>
                  <TableHead className="w-[200px]">{t('projects.table.actions')}</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {projects.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={4} className="text-center text-muted-foreground py-8">
                      {t('projects.noData')}
                    </TableCell>
                  </TableRow>
                ) : (
                  projects.map((project) => (
                    <TableRow key={project.id}>
                      <TableCell className="font-medium">{project.name}</TableCell>
                      <TableCell className="font-mono text-sm text-muted-foreground">
                        {project.directory_path || project.directory}
                      </TableCell>
                      <TableCell className="max-w-[300px] truncate">
                        {project.description || '-'}
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-1">
                          {/* SplitButton 启动按钮 */}
                          <div className="flex items-center">
                            <Button
                              variant="default"
                              size="sm"
                              className="rounded-r-none px-2"
                              onClick={() => handleQuickLaunch(project.id)}
                            >
                              <Play className="h-3.5 w-3.5 mr-1" />
                              {t('projects.launch')}
                            </Button>
                            <DropdownMenu>
                              <DropdownMenuTrigger asChild>
                                <Button
                                  variant="default"
                                  size="sm"
                                  className="rounded-l-none border-l border-primary-foreground/20 px-1.5"
                                >
                                  <ChevronDown className="h-3.5 w-3.5" />
                                </Button>
                              </DropdownMenuTrigger>
                              <DropdownMenuContent align="end" className="w-52">
                                <DropdownMenuLabel className="text-xs text-muted-foreground font-normal">
                                  {t('projects.launchMenu.selectCli')}
                                  {currentTerminal && (
                                    <span className="ml-1">
                                      ({t('projects.launchMenu.terminal')}: {
                                        currentTerminal === 'auto' ? t('settings.terminals.auto') :
                                        currentTerminal === 'kitty' ? t('settings.terminals.kitty') :
                                        currentTerminal === 'iterm' ? t('settings.terminals.iterm') :
                                        currentTerminal === 'windows_terminal' ? t('settings.terminals.windows_terminal') :
                                        currentTerminal
                                      })
                                    </span>
                                  )}
                                </DropdownMenuLabel>
                                <DropdownMenuItem onClick={() => handleQuickLaunch(project.id)}>
                                  <Zap className="h-4 w-4 mr-2" />
                                  Claude Code
                                  <span className="ml-auto text-xs text-muted-foreground">{t('projects.launchMenu.default')}</span>
                                </DropdownMenuItem>
                                <DropdownMenuItem onClick={() => handleLaunchWithCli(project.id, 'codex')}>
                                  <Terminal className="h-4 w-4 mr-2" />
                                  Codex CLI
                                </DropdownMenuItem>
                                <DropdownMenuItem onClick={() => handleLaunchWithCli(project.id, 'gemini')}>
                                  <Terminal className="h-4 w-4 mr-2" />
                                  Gemini CLI
                                </DropdownMenuItem>
                                <DropdownMenuSeparator />
                                <div className="px-2 py-1.5">
                                  <div className="flex items-center justify-between">
                                    <Label htmlFor={`dangerous-mode-${project.id}`} className="text-xs text-destructive cursor-pointer">
                                      {t('projects.launchMenu.dangerousMode')}
                                    </Label>
                                    <Switch
                                      id={`dangerous-mode-${project.id}`}
                                      checked={dangerousModeEnabled}
                                      onCheckedChange={setDangerousModeEnabled}
                                      className="scale-75"
                                    />
                                  </div>
                                </div>
                              </DropdownMenuContent>
                            </DropdownMenu>
                          </div>
                          <Button variant="ghost" size="icon" onClick={() => handleEdit(project)}>
                            <Edit className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => {
                              setProjectToDelete(project.id)
                              setDeleteDialogOpen(true)
                            }}
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
            </div>
          )}
        </CardContent>
      </Card>

      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>{t('projects.dialog.deleteTitle')}</AlertDialogTitle>
            <AlertDialogDescription>
              {t('projects.dialog.deleteDescription')}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>{t('common.cancel')}</AlertDialogCancel>
            <AlertDialogAction onClick={handleDelete}>
              {t('projects.dialog.confirmDelete')}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      <ProjectDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        project={editingProject}
      />
    </div>
  )
}

Component.displayName = 'Projects'
