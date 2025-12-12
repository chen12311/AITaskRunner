import { useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { toast } from 'sonner'
import { useTranslation } from 'react-i18next'

import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Button } from '@/components/ui/button'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'

import { useTemplateStore } from '@/stores'
import type { Template } from '@/types'

const commonVariables = [
  'project_name',
  'doc_path',
  'full_doc_path',
  'task_id',
  'cli_type',
  'review_enabled',
]

const formSchema = z.object({
  name: z.string().min(1),
  name_en: z.string().optional(),
  type: z.enum(['initial_task', 'continue_task', 'resume_task', 'status_check', 'review', 'planning']),
  description: z.string().optional(),
  description_en: z.string().optional(),
  content: z.string().min(1),
  content_en: z.string().optional(),
})

type FormData = z.infer<typeof formSchema>

interface TemplateDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  template: Template | null
}

export default function TemplateDialog({ open, onOpenChange, template }: TemplateDialogProps) {
  const { t, i18n } = useTranslation()
  const { createTemplate, updateTemplate, fetchTemplates } = useTemplateStore()
  const isEnglish = i18n.language === 'en'

  const form = useForm<FormData>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      name: '',
      name_en: '',
      type: 'initial_task',
      description: '',
      description_en: '',
      content: '',
      content_en: '',
    },
  })

  useEffect(() => {
    if (template) {
      form.reset({
        name: template.name,
        name_en: template.name_en || '',
        type: template.type,
        description: template.description || '',
        description_en: template.description_en || '',
        content: template.content,
        content_en: template.content_en || '',
      })
    } else {
      form.reset({
        name: '',
        name_en: '',
        type: 'initial_task',
        description: '',
        description_en: '',
        content: '',
        content_en: '',
      })
    }
  }, [template, form])

  const onSubmit = async (data: FormData) => {
    // 根据当前语言验证必填字段
    if (isEnglish) {
      if (!data.name_en?.trim()) {
        form.setError('name_en', { message: t('templates.dialog.form.nameRequired') })
        return
      }
      if (!data.content_en?.trim()) {
        form.setError('content_en', { message: t('templates.dialog.form.contentRequired') })
        return
      }
      // 英文模式下新建模板时，用英文值作为中文字段的回退值
      if (!template) {
        if (!data.name?.trim()) data.name = data.name_en || ''
        if (!data.content?.trim()) data.content = data.content_en || ''
        if (!data.description?.trim() && data.description_en?.trim()) {
          data.description = data.description_en
        }
      }
    } else {
      if (!data.name.trim()) {
        form.setError('name', { message: t('templates.dialog.form.nameRequired') })
        return
      }
      if (!data.content.trim()) {
        form.setError('content', { message: t('templates.dialog.form.contentRequired') })
        return
      }
      // 中文模式下新建模板时，用中文值作为英文字段的回退值
      if (!template) {
        if (!data.name_en?.trim()) data.name_en = data.name
        if (!data.content_en?.trim()) data.content_en = data.content
        if (!data.description_en?.trim() && data.description?.trim()) {
          data.description_en = data.description
        }
      }
    }

    try {
      if (template) {
        await updateTemplate(template.id, data)
        toast.success(t('templates.updateSuccess'))
      } else {
        await createTemplate(data)
        toast.success(t('templates.createSuccess'))
      }
      await fetchTemplates()
      onOpenChange(false)
    } catch {
      toast.error(template ? t('templates.updateFailed') : t('templates.createFailed'))
    }
  }

  const insertVariable = (variable: string) => {
    const field = isEnglish ? 'content_en' : 'content'
    const current = form.getValues(field) || ''
    const snippet = `{{${variable}}}`
    const nextContent = current ? `${current} ${snippet}` : snippet
    form.setValue(field, nextContent)
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[800px] max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>
            {template ? t('templates.dialog.title.edit') : t('templates.dialog.title.create')}
          </DialogTitle>
        </DialogHeader>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <FormField
              control={form.control}
              name={isEnglish ? 'name_en' : 'name'}
              render={({ field }) => (
                <FormItem>
                  <FormLabel>{t('templates.dialog.form.name')}</FormLabel>
                  <FormControl>
                    <Input placeholder={t('templates.dialog.form.namePlaceholder')} {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="type"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>{t('templates.dialog.form.type')}</FormLabel>
                  <Select onValueChange={field.onChange} value={field.value}>
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue placeholder={t('templates.dialog.form.typePlaceholder')} />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      <SelectItem value="initial_task">{t('templates.types.initial_task')}</SelectItem>
                      <SelectItem value="continue_task">{t('templates.types.continue_task')}</SelectItem>
                      <SelectItem value="resume_task">{t('templates.types.resume_task')}</SelectItem>
                      <SelectItem value="status_check">{t('templates.types.status_check')}</SelectItem>
                      <SelectItem value="review">{t('templates.types.review')}</SelectItem>
                      <SelectItem value="planning">{t('templates.types.planning')}</SelectItem>
                    </SelectContent>
                  </Select>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name={isEnglish ? 'description_en' : 'description'}
              render={({ field }) => (
                <FormItem>
                  <FormLabel>{t('templates.dialog.form.description')}</FormLabel>
                  <FormControl>
                    <Input placeholder={t('templates.dialog.form.descriptionPlaceholder')} {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name={isEnglish ? 'content_en' : 'content'}
              render={({ field }) => (
                <FormItem>
                  <FormLabel>{t('templates.dialog.form.content')}</FormLabel>
                  <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground mb-1">
                    <span>{t('templates.dialog.form.variablesHint')}</span>
                    {commonVariables.map((variable) => (
                      <Button
                        key={variable}
                        type="button"
                        variant="secondary"
                        size="sm"
                        onClick={() => insertVariable(variable)}
                        className="h-7"
                      >
                        {'{{'}
                        {variable}
                        {'}}'}
                      </Button>
                    ))}
                  </div>
                  <FormControl>
                    <Textarea
                      placeholder={t('templates.dialog.form.contentPlaceholder')}
                      className="min-h-[200px] font-mono"
                      {...field}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <div className="flex justify-end gap-2 pt-4">
              <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
                {t('common.cancel')}
              </Button>
              <Button type="submit">{template ? t('common.save') : t('common.create')}</Button>
            </div>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  )
}
