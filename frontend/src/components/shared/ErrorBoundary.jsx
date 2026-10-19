import * as React from "react";
import { AlertTriangle, RefreshCw, Home } from "lucide-react";
import { Button } from "@/components/ui/button";

/**
 * Class-based error boundary (required — React has no hook
 * equivalent for componentDidCatch as of React 18/19). Wrap around
 * route subtrees (e.g. each page in AppRouter.jsx) so a crash in
 * one page doesn't take down the whole app shell.
 *
 * Usage:
 *   <ErrorBoundary>
 *     <DashboardPage />
 *   </ErrorBoundary>
 */
export default class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    // Hook up to an error-reporting service (Sentry, etc.) here.
    console.error("ErrorBoundary caught an error:", error, errorInfo);
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null });
    this.props.onReset?.();
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback(this.state.error, this.handleReset);
      }

      return (
        <div className="flex min-h-[320px] flex-col items-center justify-center gap-3 rounded-lg border border-dashed border-border p-8 text-center">
          <div className="flex h-14 w-14 items-center justify-center rounded-full bg-red-50">
            <AlertTriangle className="h-6 w-6 text-red-600" />
          </div>
          <div>
            <p className="text-sm font-medium">Something went wrong</p>
            <p className="mt-1 max-w-sm text-xs text-muted-foreground">
              {this.props.errorMessage ||
                "An unexpected error occurred while rendering this page. Try refreshing, or head back to the dashboard."}
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={this.handleReset}>
              <RefreshCw className="h-3.5 w-3.5" />
              Try again
            </Button>
            <Button size="sm" onClick={() => (window.location.href = "/dashboard")}>
              <Home className="h-3.5 w-3.5" />
              Go to Dashboard
            </Button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}