import { useState, useEffect, useCallback } from "react";
import { IntakeForm, IntakeRequest } from "./IntakeForm";
import { EstimateResult, IntakeResponse } from "./EstimateResult";
import { ApiConfig } from "./ApiConfig";
import { generateMockResponse, checkApiHealth } from "./mockService";
import { useToast } from "@/hooks/use-toast";
import { Printer, FlaskConical } from "lucide-react";
import { Badge } from "@/components/ui/badge";

/**
 * PrintEstimator Component
 * 
 * Main container component that orchestrates:
 * - API configuration
 * - Intake form submission
 * - Result display
 * - Demo mode handling
 * 
 * Architecture Notes:
 * - Demo mode is triggered automatically when backend is unreachable
 * - User can manually toggle demo mode for assessment purposes
 * - Real API logic is preserved for Docker/production usage
 * - Mock responses are clearly marked as demo data
 */
export function PrintEstimator() {
  const [apiUrl, setApiUrl] = useState("http://localhost:8000");
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<IntakeResponse | null>(null);
  const [demoMode, setDemoMode] = useState(false);
  const [isApiReachable, setIsApiReachable] = useState(false);
  const [hasCheckedApi, setHasCheckedApi] = useState(false);
  const { toast } = useToast();

  /**
   * Check API health on mount and when URL changes
   * Automatically enables demo mode if backend is unreachable
   */
  const checkApiStatus = useCallback(async () => {
    const isHealthy = await checkApiHealth(apiUrl);
    setIsApiReachable(isHealthy);
    
    // Only auto-enable demo mode on initial load if API is unreachable
    if (!hasCheckedApi && !isHealthy) {
      setDemoMode(true);
      toast({
        title: "Demo Mode Activated",
        description: "Backend not detected. Using mock responses for demonstration.",
      });
    }
    
    setHasCheckedApi(true);
  }, [apiUrl, hasCheckedApi, toast]);

  useEffect(() => {
    checkApiStatus();
  }, [checkApiStatus]);

  /**
   * Re-check API when demo mode is manually disabled
   */
  const handleDemoModeChange = async (enabled: boolean) => {
    if (!enabled) {
      // User wants to use real API - check if it's available
      const isHealthy = await checkApiHealth(apiUrl);
      setIsApiReachable(isHealthy);
      
      if (!isHealthy) {
        toast({
          title: "Backend Not Available",
          description: "Cannot connect to API. Demo mode remains active.",
          variant: "destructive",
        });
        return; // Keep demo mode on
      }
    }
    setDemoMode(enabled);
  };

  /**
   * Handle form submission
   * Routes to mock service or real API based on demo mode
   */
  const handleSubmit = async (request: IntakeRequest) => {
    setIsLoading(true);
    setResult(null);

    try {
      let data: IntakeResponse;

      if (demoMode) {
        // ============================================
        // DEMO MODE: Use mock service
        // This provides realistic responses without backend
        // ============================================
        
        // Simulate network delay for realistic UX
        await new Promise(resolve => setTimeout(resolve, 800));
        data = generateMockResponse(request);
        
      } else {
        // ============================================
        // PRODUCTION MODE: Call real FastAPI backend
        // Requires Docker backend to be running
        // ============================================
        
        const response = await fetch(`${apiUrl}/intake`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(request),
        });

        if (!response.ok) {
          throw new Error(`API error: ${response.status} ${response.statusText}`);
        }

        data = await response.json();
      }

      setResult(data);

      // Show toast based on status
      if (data.status === "success") {
        toast({
          title: demoMode ? "Demo Estimate Ready" : "Estimate Ready",
          description: `Total: ${data.estimate?.currency} ${data.estimate?.total.toFixed(2)}`,
        });
      } else if (data.status === "validation_errors") {
        toast({
          title: "Validation Issues",
          description: "Please review the warnings and missing information.",
          variant: "destructive",
        });
      } else {
        toast({
          title: "Extraction Failed",
          description: "Could not extract specifications from input.",
          variant: "destructive",
        });
      }
    } catch (error) {
      console.error("Intake API error:", error);
      
      // If real API fails, offer to switch to demo mode
      toast({
        title: "Connection Error",
        description: "Failed to connect. Consider enabling Demo Mode.",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <div className="container max-w-4xl py-8 px-4">
        {/* Demo Mode Banner */}
        {demoMode && (
          <div className="mb-6 flex items-center justify-center gap-2 py-2 px-4 rounded-lg bg-amber-100 dark:bg-amber-950/50 border border-amber-300 dark:border-amber-800">
            <FlaskConical className="h-4 w-4 text-amber-600 dark:text-amber-400" />
            <span className="text-sm font-medium text-amber-800 dark:text-amber-200">
              Demo Mode – Backend not connected
            </span>
            <Badge variant="outline" className="ml-2 text-xs border-amber-400 text-amber-700 dark:text-amber-300">
              Mock Data
            </Badge>
          </div>
        )}

        {/* Header */}
        <header className="text-center mb-8">
          <div className="inline-flex items-center justify-center gap-3 mb-4">
            <div className="p-3 rounded-xl bg-primary/10">
              <Printer className="h-8 w-8 text-primary" />
            </div>
          </div>
          <h1 className="text-3xl font-bold tracking-tight mb-2">
            Print Estimator
          </h1>
          <p className="text-muted-foreground max-w-md mx-auto">
            AI-powered print job estimation. Describe your project and get instant specifications and pricing.
          </p>
        </header>

        {/* Main Content */}
        <div className="grid gap-6 lg:grid-cols-2">
          {/* Left Column: Config + Form */}
          <div className="space-y-4">
            <ApiConfig 
              apiUrl={apiUrl} 
              onApiUrlChange={setApiUrl}
              demoMode={demoMode}
              onDemoModeChange={handleDemoModeChange}
              isApiReachable={isApiReachable}
            />
            <IntakeForm onSubmit={handleSubmit} isLoading={isLoading} />
          </div>

          {/* Right Column: Results */}
          <div>
            {result ? (
              <EstimateResult result={result} />
            ) : (
              <div className="h-full min-h-[300px] flex items-center justify-center rounded-lg border-2 border-dashed border-muted-foreground/25">
                <div className="text-center text-muted-foreground">
                  <Printer className="h-12 w-12 mx-auto mb-3 opacity-50" />
                  <p className="text-sm">
                    {demoMode 
                      ? "Submit a print job to see demo results" 
                      : "Submit a print job to see results"
                    }
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <footer className="mt-12 pt-6 border-t text-center text-sm text-muted-foreground">
          <p>
            Technical Assessment Project • FastAPI + LLM Extraction + Rule-Based Pricing
          </p>
          {demoMode && (
            <p className="mt-1 text-xs text-amber-600 dark:text-amber-400">
              Running in demo mode with simulated responses
            </p>
          )}
        </footer>
      </div>
    </div>
  );
}

export default PrintEstimator;
