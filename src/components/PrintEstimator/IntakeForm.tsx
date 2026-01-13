import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { FileText, Image, Type, Loader2 } from "lucide-react";

interface IntakeFormProps {
  onSubmit: (data: IntakeRequest) => void;
  isLoading: boolean;
}

export interface IntakeRequest {
  input_type: "text" | "pdf" | "image";
  content?: string;
  metadata?: Record<string, unknown>;
}

/**
 * IntakeForm Component
 * 
 * Provides three input methods for print job specifications:
 * - Text: Direct text description
 * - PDF: Metadata about uploaded PDF (actual upload is TODO)
 * - Image: Metadata about uploaded image (actual upload is TODO)
 * 
 * Design Decision: Using tabs for clear separation of input types
 */
export function IntakeForm({ onSubmit, isLoading }: IntakeFormProps) {
  const [activeTab, setActiveTab] = useState<"text" | "pdf" | "image">("text");
  const [textContent, setTextContent] = useState("");
  const [pdfFilename, setPdfFilename] = useState("");
  const [imageFilename, setImageFilename] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    const request: IntakeRequest = {
      input_type: activeTab,
    };

    switch (activeTab) {
      case "text":
        request.content = textContent;
        break;
      case "pdf":
        request.content = "Extracted text from PDF..."; // Placeholder
        request.metadata = { filename: pdfFilename, pages: 1 };
        break;
      case "image":
        request.content = "OCR text from image..."; // Placeholder
        request.metadata = { filename: imageFilename };
        break;
    }

    onSubmit(request);
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <FileText className="h-5 w-5" />
          Print Job Intake
        </CardTitle>
        <CardDescription>
          Describe your print job and we'll extract specifications and provide an estimate
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-6">
          <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as typeof activeTab)}>
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="text" className="flex items-center gap-2">
                <Type className="h-4 w-4" />
                Text
              </TabsTrigger>
              <TabsTrigger value="pdf" className="flex items-center gap-2">
                <FileText className="h-4 w-4" />
                PDF
              </TabsTrigger>
              <TabsTrigger value="image" className="flex items-center gap-2">
                <Image className="h-4 w-4" />
                Image
              </TabsTrigger>
            </TabsList>

            <TabsContent value="text" className="space-y-4 pt-4">
              <div className="space-y-2">
                <Label htmlFor="text-content">Print Job Description</Label>
                <Textarea
                  id="text-content"
                  placeholder="e.g., 500 business cards, double-sided printing, matte finish with rounded corners on 14pt cardstock"
                  value={textContent}
                  onChange={(e) => setTextContent(e.target.value)}
                  className="min-h-[120px] resize-none"
                />
                <p className="text-sm text-muted-foreground">
                  Include quantity, product type, paper specs, finishes, and any special requirements
                </p>
              </div>
            </TabsContent>

            <TabsContent value="pdf" className="space-y-4 pt-4">
              <div className="space-y-2">
                <Label htmlFor="pdf-file">PDF Specification Document</Label>
                <Input
                  id="pdf-file"
                  type="text"
                  placeholder="specs.pdf"
                  value={pdfFilename}
                  onChange={(e) => setPdfFilename(e.target.value)}
                />
                <p className="text-sm text-muted-foreground">
                  TODO: Actual file upload. Currently accepts filename metadata only.
                </p>
              </div>
            </TabsContent>

            <TabsContent value="image" className="space-y-4 pt-4">
              <div className="space-y-2">
                <Label htmlFor="image-file">Image with Specifications</Label>
                <Input
                  id="image-file"
                  type="text"
                  placeholder="quote-request.jpg"
                  value={imageFilename}
                  onChange={(e) => setImageFilename(e.target.value)}
                />
                <p className="text-sm text-muted-foreground">
                  TODO: Actual OCR extraction. Currently accepts filename metadata only.
                </p>
              </div>
            </TabsContent>
          </Tabs>

          <Button type="submit" className="w-full" disabled={isLoading}>
            {isLoading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Processing...
              </>
            ) : (
              "Get Estimate"
            )}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
