import { Component, type ReactNode } from 'react'
import { AlertTriangle } from 'lucide-react'
import { Translation } from 'react-i18next'
import { Button } from '@/components/ui/button'

interface ErrorBoundaryProps {
  children: ReactNode
}

interface ErrorBoundaryState {
  hasError: boolean
}

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props)
    this.state = { hasError: false }
  }

  static getDerivedStateFromError() {
    return { hasError: true }
  }

  componentDidCatch(error: unknown) {
    console.error('Unhandled UI error:', error)
  }

  handleReload = () => {
    this.setState({ hasError: false })
    window.location.reload()
  }

  render() {
    if (this.state.hasError) {
      return (
        <Translation>
          {(t) => (
            <div className="min-h-screen flex flex-col items-center justify-center bg-background text-foreground gap-4">
              <AlertTriangle className="h-10 w-10 text-destructive" />
              <div className="text-center space-y-2">
                <h2 className="text-xl font-semibold">{t('errorBoundary.title')}</h2>
                <p className="text-sm text-muted-foreground">{t('errorBoundary.description')}</p>
              </div>
              <Button onClick={this.handleReload}>{t('errorBoundary.reload')}</Button>
            </div>
          )}
        </Translation>
      )
    }

    return this.props.children
  }
}
