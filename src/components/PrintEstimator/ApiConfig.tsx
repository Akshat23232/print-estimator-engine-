import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Settings, ExternalLink, Wifi, WifiOff } from "lucide-react";
import { checkApiHealth } from "./mockService";

interface ApiConfigProps {
  apiUrl: string;
  onApiUrlChange: (url: string) => void;
  demoMode: boolean;
  onDemoModeChange: (enabled: boolean) => void;
  isApiReachable: boolean;
}

/**
 * ApiConfig Component
 * 
 * Allows users to configure the backend API URL and demo mode.
 * 
 * Features:
 * - Backend URL configuration for local Docker usage
 * - Manual demo mode toggle for assessment demonstrations
 * - Visual indicator of API connectivity status
 * 
 * Design Decision: Demo mode toggle is prominent for easy assessment access
 */
export function ApiConfig({ 
  apiUrl, 
  onApiUrlChange, 
  demoMode, 
  onDemoModeChange,
  isApiReachable 
}: ApiConfigProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [localUrl, setLocalUrl] = useState(apiUrl);

  const handleSave = () => {
    onApiUrlChange(localUrl);
    setIsExpanded(false);
  };

  // Update local URL when prop changes
  useEffect(() => {
    setLocalUrl(apiUrl);
  }, [apiUrl]);

  return (
    <Card className="border-dashed">
      <CardHeader 
        className="cursor-pointer hover:bg-muted/50 transition-colors"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2 text-sm font-medium">
            <Settings className="h-4 w-4" />
            API Configuration
          </CardTitle>
          {/* Connection status indicator */}
          <div className="flex items-center gap-2">
            {demoMode ? (
              <span className="flex items-center gap-1 text-xs text-amber-600">
                <WifiOff className="h-3 w-3" />
                Demo
              </span>
            ) : isApiReachable ? (
              <span className="flex items-center gap-1 text-xs text-green-600">
                <Wifi className="h-3 w-3" />
                Connected
              </span>
            ) : (
              <span className="flex items-center gap-1 text-xs text-muted-foreground">
                <WifiOff className="h-3 w-3" />
                Offline
              </span>
            )}
          </div>
        </div>
        {!isExpanded && (
          <CardDescription className="font-mono text-xs truncate">
            {demoMode ? "Using mock responses (demo mode)" : apiUrl}
          </CardDescription>
        )}
      </CardHeader>
      
      {isExpanded && (
        <CardContent className="space-y-4">
          {/* Demo Mode Toggle - Prominent for assessment */}
          <div className="flex items-center justify-between p-3 rounded-lg bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800">
            <div className="space-y-0.5">
              <Label htmlFor="demo-mode" className="font-medium text-amber-900 dark:text-amber-100">
                Demo Mode
              </Label>
              <p className="text-xs text-amber-700 dark:text-amber-300">
                Use mock responses without backend
              </p>
            </div>
            <Switch
              id="demo-mode"
              checked={demoMode}
              onCheckedChange={onDemoModeChange}
            />
          </div>

          {/* API URL Configuration - Only relevant when not in demo mode */}
          <div className={`space-y-2 ${demoMode ? 'opacity-50 pointer-events-none' : ''}`}>
            <Label htmlFor="api-url">Backend API URL</Label>
            <Input
              id="api-url"
              type="url"
              placeholder="http://localhost:8000"
              value={localUrl}
              onChange={(e) => setLocalUrl(e.target.value)}
              disabled={demoMode}
            />
            <p className="text-xs text-muted-foreground">
              The FastAPI backend URL. Run <code className="bg-muted px-1 rounded">docker-compose up</code> to start locally.
            </p>
          </div>
          
          <div className="flex gap-2">
            <Button onClick={handleSave} size="sm" disabled={demoMode}>
              Save
            </Button>
            <Button 
              variant="outline" 
              size="sm"
              onClick={() => window.open(`${localUrl}/docs`, "_blank")}
              disabled={demoMode}
            >
              <ExternalLink className="h-3 w-3 mr-1" />
              API Docs
            </Button>
          </div>
        </CardContent>
      )}
    </Card>
  );
}
