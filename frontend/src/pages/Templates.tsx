import { useEffect, useState, useMemo, useCallback } from 'react'
import { Plus, RefreshCw, Edit, Trash2, Star, Eye, Search } from 'lucide-react'
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
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Skeleton } from '@/components/ui/skeleton'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Label } from '@/components/ui/label'

import { useTemplateStore } from '@/stores'
import type { Template, TemplateType } from '@/types'
import TemplateDialog from '@/components/TemplateDialog'
import { templateApi } from '@/api'

const typeClassNames: Record<TemplateType, string> = {
  initial_task: 'bg-blue-500 dark:bg-blue-600',
  continue_task: 'bg-teal-500 dark:bg-teal-600',
  resume_task: 'bg-green-500 dark:bg-green-600',
  status_check: 'bg-muted dark:bg-muted',
  review: 'bg-yellow-500 dark:bg-yellow-600',
  planning: 'bg-purple-500 dark:bg-purple-600',
}

export function Component() {
  const { t, i18n } = useTranslation()
  const { templates, loading, fetchTemplates, deleteTemplate, setDefault, filterType, setFilterType } =
    useTemplateStore()

  // 根据当前语言获取模板名称
  const getTemplateName = useCallback((template: Template) => {
    if (i18n.language === 'en' && template.name_en) {
      return template.name_en
    }
    return template.name
  }, [i18n.language])

  // 根据当前语言获取模板描述
  const getTemplateDescription = useCallback((template: Template) => {
    if (i18n.language === 'en' && template.description_en) {
      return template.description_en
    }
    return template.description || '-'
  }, [i18n.language])

  const getTemplateContent = useCallback((template: Template | null) => {
    if (!template) return ''
    if (i18n.language === 'en' && template.content_en) {
      return template.content_en
    }
    return template.content
  }, [i18n.language])

  const [search, setSearch] = useState('')
  const [dialogOpen, setDialogOpen] = useState(false)
  const [editingTemplate, setEditingTemplate] = useState<Template | null>(null)
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [templateToDelete, setTemplateToDelete] = useState<string | null>(null)
  const [previewTemplate, setPreviewTemplate] = useState<Template | null>(null)
  const [detectedVariables, setDetectedVariables] = useState<string[]>([])
  const [variableInputs, setVariableInputs] = useState<Record<string, string>>({})
  const [renderedContent, setRenderedContent] = useState('')
  const [rendering, setRendering] = useState(false)
  const currentLocale = useMemo(() => i18n.language.startsWith('zh') ? zhCN : enUS, [i18n.language])

  useEffect(() => {
    fetchTemplates()
  }, [fetchTemplates])

  const extractVariables = useCallback((content: string) => {
    const regex = /\{\{\s*([\w.]+)\s*\}\}/g
    const variables = new Set<string>()
    let match: RegExpExecArray | null
    while ((match = regex.exec(content)) !== null) {
      variables.add(match[1])
    }
    return Array.from(variables)
  }, [])

  useEffect(() => {
    if (previewTemplate) {
      const previewContent = getTemplateContent(previewTemplate)
      const variables = extractVariables(previewContent)
      setDetectedVariables(variables)
      setVariableInputs((prev) => {
        const next: Record<string, string> = {}
        variables.forEach((key) => {
          next[key] = prev[key] ?? ''
        })
        return next
      })
      setRenderedContent('')
    } else {
      setDetectedVariables([])
      setVariableInputs({})
      setRenderedContent('')
    }
  }, [previewTemplate, extractVariables, getTemplateContent])

  const filteredTemplates = useMemo(() => {
    return templates.filter((template) => {
      const matchesSearch = search
        ? getTemplateName(template).toLowerCase().includes(search.toLowerCase()) ||
          getTemplateDescription(template).toLowerCase().includes(search.toLowerCase())
        : true
      const matchesType = filterType === 'all' || template.type === filterType
      return matchesSearch && matchesType
    })
  }, [templates, search, filterType, getTemplateName, getTemplateDescription])

  const handleEdit = useCallback((template: Template) => {
    setEditingTemplate(template)
    setDialogOpen(true)
  }, [])

  const handleCreate = useCallback(() => {
    setEditingTemplate(null)
    setDialogOpen(true)
  }, [])

  const handleDelete = useCallback(async () => {
    if (templateToDelete === null) return
    try {
      await deleteTemplate(templateToDelete)
      toast.success(t('templates.deleteSuccess'))
    } catch {
      toast.error(t('templates.deleteFailed'))
    }
    setDeleteDialogOpen(false)
    setTemplateToDelete(null)
  }, [templateToDelete, deleteTemplate, t])

  const handleSetDefault = useCallback(async (templateId: string) => {
    try {
      await setDefault(templateId)
      toast.success(t('templates.setDefaultSuccess'))
    } catch {
      toast.error(t('templates.setDefaultFailed'))
    }
  }, [setDefault, t])

  const handleRenderPreview = useCallback(async () => {
    if (!previewTemplate) return
    setRendering(true)
    try {
      const response = await templateApi.render({
        template_id: previewTemplate.id,
        variables: variableInputs,
      })
      // 后端直接返回 {rendered: string}
      if (response.rendered) {
        setRenderedContent(response.rendered)
        toast.success(t('templates.renderSuccess'))
      } else {
        toast.error(t('templates.renderFailed'))
      }
    } catch {
      toast.error(t('templates.renderFailed'))
    } finally {
      setRendering(false)
    }
  }, [previewTemplate, variableInputs, t])

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">{t('templates.title')}</h1>
        <Button onClick={handleCreate}>
          <Plus className="h-4 w-4 mr-2" />
          {t('templates.createTemplate')}
        </Button>
      </div>

      <Card>
        <CardHeader className="pb-4">
          <div className="flex items-center gap-4">
            <Select
              value={filterType}
              onValueChange={(v) => setFilterType(v as TemplateType | 'all')}
            >
              <SelectTrigger className="w-[140px]">
                <SelectValue placeholder={t('templates.typeFilter')} />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">{t('templates.types.all')}</SelectItem>
                <SelectItem value="initial_task">{t('templates.types.initial_task')}</SelectItem>
                <SelectItem value="continue_task">{t('templates.types.continue_task')}</SelectItem>
                <SelectItem value="resume_task">{t('templates.types.resume_task')}</SelectItem>
                <SelectItem value="status_check">{t('templates.types.status_check')}</SelectItem>
                <SelectItem value="review">{t('templates.types.review')}</SelectItem>
                <SelectItem value="planning">{t('templates.types.planning')}</SelectItem>
              </SelectContent>
            </Select>
            <div className="relative flex-1 max-w-sm">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder={t('templates.searchPlaceholder')}
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-9"
              />
            </div>
            <Button variant="outline" size="icon" onClick={() => fetchTemplates()}>
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
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>{t('templates.table.name')}</TableHead>
                  <TableHead className="w-[100px]">{t('templates.table.type')}</TableHead>
                  <TableHead>{t('templates.table.description')}</TableHead>
                  <TableHead className="w-[160px]">{t('templates.table.updatedAt')}</TableHead>
                  <TableHead className="w-[140px]">{t('templates.table.actions')}</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredTemplates.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={5} className="text-center text-muted-foreground py-8">
                      {t('templates.noData')}
                    </TableCell>
                  </TableRow>
                ) : (
                  filteredTemplates.map((template) => (
                    <TableRow key={template.id}>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <span className="font-medium">{getTemplateName(template)}</span>
                          {template.is_default && (
                            <Badge variant="secondary">
                              <Star className="h-3 w-3 mr-1" />
                              {t('common.default')}
                            </Badge>
                          )}
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge className={typeClassNames[template.type]}>
                          {t(`templates.types.${template.type}`)}
                        </Badge>
                      </TableCell>
                      <TableCell className="max-w-[300px] truncate">
                        {getTemplateDescription(template)}
                      </TableCell>
                      <TableCell className="text-muted-foreground text-sm">
                        {format(new Date(template.updated_at), 'yyyy-MM-dd HH:mm', { locale: currentLocale })}
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-1">
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => setPreviewTemplate(template)}
                          >
                            <Eye className="h-4 w-4" />
                          </Button>
                          <Button variant="ghost" size="icon" onClick={() => handleEdit(template)}>
                            <Edit className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => handleSetDefault(template.id)}
                            disabled={template.is_default}
                          >
                            <Star className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => {
                              setTemplateToDelete(template.id)
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
            <AlertDialogTitle>{t('templates.dialog.deleteTitle')}</AlertDialogTitle>
            <AlertDialogDescription>{t('templates.dialog.deleteDescription')}</AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>{t('common.cancel')}</AlertDialogCancel>
            <AlertDialogAction onClick={handleDelete}>{t('templates.dialog.confirmDelete')}</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

          <Dialog open={!!previewTemplate} onOpenChange={() => setPreviewTemplate(null)}>
            <DialogContent className="sm:max-w-[700px]">
              <DialogHeader>
                <DialogTitle>{t('templates.preview.title', { name: previewTemplate ? getTemplateName(previewTemplate) : '' })}</DialogTitle>
              </DialogHeader>
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-muted-foreground">{t('templates.preview.type')}</span>
                <Badge className={typeClassNames[previewTemplate?.type as TemplateType] || ''}>
                  {previewTemplate?.type ? t(`templates.types.${previewTemplate.type}` as const) : '-'}
                </Badge>
              </div>
                  <div>
                    <span className="text-muted-foreground">{t('templates.preview.description')}</span>
                    <span>{previewTemplate ? getTemplateDescription(previewTemplate) : '-'}</span>
                  </div>
                </div>
                <div>
                  <h4 className="text-sm font-medium mb-2">{t('templates.preview.content')}</h4>
                  <ScrollArea className="h-[400px] rounded-md border bg-muted/50 p-4">
                    <pre className="text-sm font-mono whitespace-pre-wrap">{getTemplateContent(previewTemplate)}</pre>
                  </ScrollArea>
                </div>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <h4 className="text-sm font-medium">{t('templates.preview.variables')}</h4>
                <p className="text-xs text-muted-foreground">
                  {t('templates.preview.variablesHint')}
                </p>
              </div>
              {detectedVariables.length ? (
                <div className="space-y-3">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {detectedVariables.map((variable) => (
                      <div key={variable} className="space-y-1">
                        <Label className="text-xs text-muted-foreground">{variable}</Label>
                        <Input
                          value={variableInputs[variable] ?? ''}
                          onChange={(e) =>
                            setVariableInputs((prev) => ({ ...prev, [variable]: e.target.value }))
                          }
                          placeholder={t('templates.preview.variablePlaceholder', { variable })}
                        />
                      </div>
                    ))}
                  </div>
                  <Button
                    onClick={handleRenderPreview}
                    disabled={rendering}
                    className="min-w-[120px]"
                  >
                    {rendering ? t('templates.preview.rendering') : t('templates.preview.render')}
                  </Button>
                </div>
              ) : (
                <div className="text-sm text-muted-foreground">{t('templates.preview.noVariables')}</div>
              )}
            </div>
            {renderedContent && (
              <div>
                <h4 className="text-sm font-medium mb-2">{t('templates.preview.result')}</h4>
                <ScrollArea className="h-[240px] rounded-md border bg-muted/50 p-4">
                  <pre className="text-sm font-mono whitespace-pre-wrap">{renderedContent}</pre>
                </ScrollArea>
              </div>
            )}
          </div>
        </DialogContent>
      </Dialog>

      <TemplateDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        template={editingTemplate}
      />
    </div>
  )
}

Component.displayName = 'Templates'
