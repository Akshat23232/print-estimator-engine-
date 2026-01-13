import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { CheckCircle2, AlertTriangle, XCircle, DollarSign, Package, FileCheck, Printer } from "lucide-react";

/**
 * Print Specifications extracted by LLM
 * Matches backend's PrintSpecs schema
 */
interface PrintSpecs {
  product_type?: string;
  quantity?: number;
  size?: string;
  paper_stock?: string;
  sides?: "single" | "double";
  finish?: string;
  color_mode?: string;
  options?: string[];
  turnaround_days?: number;
  is_rush?: boolean;
  artwork_dpi?: number;
  raw_input?: string;
}

/**
 * Validation result with three-tier feedback
 * Matches backend's ValidationResult schema
 */
interface ValidationResult {
  is_valid: boolean;
  errors: string[];
  warnings: string[];
  missing_fields: string[];
}

/**
 * Detailed pricing breakdown
 * Matches backend's PricingBreakdown schema
 */
interface PricingBreakdown {
  material_cost: number;
  print_cost: number;
  setup_cost: number;
  finishing_cost: number;
  option_costs: Record<string, number>;
  rush_fee: number;
  quantity_discount: number;
  margin_amount: number;
  margin_percent: number;
}

/**
 * Complete price estimate
 * Matches backend's PriceEstimate schema
 */
interface PriceEstimate {
  print_method: "digital" | "offset";
  print_method_reason: string;
  breakdown: PricingBreakdown;
  subtotal: number;
  tax: number;
  total: number;
  currency: string;
  estimate_notes: string[];
}

/**
 * Complete response from /intake endpoint
 * Matches backend's IntakeResponse schema
 */
interface IntakeResponse {
  request_id: string;
  status: "success" | "validation_errors" | "extraction_failed";
  extracted_specs?: PrintSpecs;
  validation: ValidationResult;
  estimate?: PriceEstimate;
}

interface EstimateResultProps {
  result: IntakeResponse;
}

/**
 * EstimateResult Component
 * 
 * Displays the complete response from the /intake endpoint:
 * - Status badge with appropriate styling
 * - Print method decision (digital vs offset)
 * - Extracted specifications in a structured format
 * - Validation errors/warnings/missing fields
 * - Detailed price breakdown with all cost components
 * 
 * Design Decision: Visual hierarchy emphasizes actionable info (errors, price)
 */
export function EstimateResult({ result }: EstimateResultProps) {
  const statusConfig = {
    success: { icon: CheckCircle2, color: "bg-green-500/10 text-green-600 border-green-200", label: "Success" },
    validation_errors: { icon: AlertTriangle, color: "bg-yellow-500/10 text-yellow-600 border-yellow-200", label: "Validation Issues" },
    extraction_failed: { icon: XCircle, color: "bg-destructive/10 text-destructive border-destructive/20", label: "Extraction Failed" },
  };

  const status = statusConfig[result.status];
  const StatusIcon = status.icon;

  return (
    <div className="space-y-4">
      {/* Status Header */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <StatusIcon className="h-5 w-5" />
              Estimate Result
            </CardTitle>
            <Badge variant="outline" className={status.color}>
              {status.label}
            </Badge>
          </div>
          <CardDescription className="font-mono text-xs">
            Request ID: {result.request_id}
          </CardDescription>
        </CardHeader>
      </Card>

      {/* Print Method Decision - Important for assessment */}
      {result.estimate && (
        <Card className="border-blue-200 bg-blue-500/5">
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center gap-2 text-base">
              <Printer className="h-4 w-4" />
              Print Method Decision
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-3 mb-2">
              <Badge variant="secondary" className="text-sm font-semibold uppercase">
                {result.estimate.print_method}
              </Badge>
              <span className="text-sm text-muted-foreground">
                {result.estimate.print_method === "digital" ? "Digital Printing" : "Offset Printing"}
              </span>
            </div>
            <p className="text-sm text-muted-foreground">
              {result.estimate.print_method_reason}
            </p>
          </CardContent>
        </Card>
      )}

      {/* Validation Alerts */}
      {result.validation.errors.length > 0 && (
        <Alert variant="destructive">
          <XCircle className="h-4 w-4" />
          <AlertTitle>Validation Errors</AlertTitle>
          <AlertDescription>
            <ul className="list-disc list-inside mt-2 space-y-1">
              {result.validation.errors.map((error, i) => (
                <li key={i}>{error}</li>
              ))}
            </ul>
          </AlertDescription>
        </Alert>
      )}

      {result.validation.warnings.length > 0 && (
        <Alert className="border-yellow-200 bg-yellow-500/10">
          <AlertTriangle className="h-4 w-4 text-yellow-600" />
          <AlertTitle className="text-yellow-600">Warnings</AlertTitle>
          <AlertDescription className="text-yellow-700">
            <ul className="list-disc list-inside mt-2 space-y-1">
              {result.validation.warnings.map((warning, i) => (
                <li key={i}>{warning}</li>
              ))}
            </ul>
          </AlertDescription>
        </Alert>
      )}

      {result.validation.missing_fields.length > 0 && (
        <Alert className="border-blue-200 bg-blue-500/10">
          <FileCheck className="h-4 w-4 text-blue-600" />
          <AlertTitle className="text-blue-600">Missing Information</AlertTitle>
          <AlertDescription className="text-blue-700">
            The following fields were not detected: {result.validation.missing_fields.join(", ")}
          </AlertDescription>
        </Alert>
      )}

      {/* Extracted Specs */}
      {result.extracted_specs && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Package className="h-4 w-4" />
              Extracted Specifications
            </CardTitle>
          </CardHeader>
          <CardContent>
            <dl className="grid grid-cols-2 gap-x-4 gap-y-3 text-sm">
              {result.extracted_specs.product_type && (
                <>
                  <dt className="text-muted-foreground">Product Type</dt>
                  <dd className="font-medium capitalize">{result.extracted_specs.product_type.replace(/_/g, " ")}</dd>
                </>
              )}
              {result.extracted_specs.quantity && (
                <>
                  <dt className="text-muted-foreground">Quantity</dt>
                  <dd className="font-medium">{result.extracted_specs.quantity.toLocaleString()}</dd>
                </>
              )}
              {result.extracted_specs.size && (
                <>
                  <dt className="text-muted-foreground">Size</dt>
                  <dd className="font-medium">{result.extracted_specs.size}</dd>
                </>
              )}
              {result.extracted_specs.paper_stock && (
                <>
                  <dt className="text-muted-foreground">Paper Stock</dt>
                  <dd className="font-medium capitalize">{result.extracted_specs.paper_stock}</dd>
                </>
              )}
              {result.extracted_specs.sides && (
                <>
                  <dt className="text-muted-foreground">Sides</dt>
                  <dd className="font-medium capitalize">{result.extracted_specs.sides}-sided</dd>
                </>
              )}
              {result.extracted_specs.color_mode && (
                <>
                  <dt className="text-muted-foreground">Color Mode</dt>
                  <dd className="font-medium capitalize">{result.extracted_specs.color_mode.replace(/_/g, " ")}</dd>
                </>
              )}
              {result.extracted_specs.finish && (
                <>
                  <dt className="text-muted-foreground">Finish</dt>
                  <dd className="font-medium capitalize">{result.extracted_specs.finish.replace(/_/g, " ")}</dd>
                </>
              )}
              {result.extracted_specs.turnaround_days !== undefined && (
                <>
                  <dt className="text-muted-foreground">Turnaround</dt>
                  <dd className="font-medium">
                    {result.extracted_specs.turnaround_days === 0 
                      ? "Same day" 
                      : `${result.extracted_specs.turnaround_days} business days`}
                    {result.extracted_specs.is_rush && (
                      <Badge variant="destructive" className="ml-2 text-xs">RUSH</Badge>
                    )}
                  </dd>
                </>
              )}
              {result.extracted_specs.artwork_dpi && (
                <>
                  <dt className="text-muted-foreground">Artwork DPI</dt>
                  <dd className="font-medium">{result.extracted_specs.artwork_dpi} DPI</dd>
                </>
              )}
              {result.extracted_specs.options && result.extracted_specs.options.length > 0 && (
                <>
                  <dt className="text-muted-foreground">Additional Options</dt>
                  <dd className="font-medium capitalize">
                    {result.extracted_specs.options.map(o => o.replace(/_/g, " ")).join(", ")}
                  </dd>
                </>
              )}
            </dl>
          </CardContent>
        </Card>
      )}

      {/* Detailed Price Breakdown */}
      {result.estimate && (
        <Card className="border-primary/20 bg-primary/5">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <DollarSign className="h-4 w-4" />
              Price Estimate
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Cost Breakdown */}
            <div className="space-y-2 text-sm">
              <div className="font-medium text-muted-foreground mb-2">Cost Breakdown</div>
              
              <div className="flex justify-between">
                <span className="text-muted-foreground">Material Cost</span>
                <span className="font-medium">
                  ${result.estimate.breakdown.material_cost.toFixed(2)}
                </span>
              </div>
              
              <div className="flex justify-between">
                <span className="text-muted-foreground">Print Cost</span>
                <span className="font-medium">
                  ${result.estimate.breakdown.print_cost.toFixed(2)}
                </span>
              </div>
              
              <div className="flex justify-between">
                <span className="text-muted-foreground">Setup Cost</span>
                <span className="font-medium">
                  ${result.estimate.breakdown.setup_cost.toFixed(2)}
                </span>
              </div>
              
              <div className="flex justify-between">
                <span className="text-muted-foreground">Finishing Cost</span>
                <span className="font-medium">
                  ${result.estimate.breakdown.finishing_cost.toFixed(2)}
                </span>
              </div>
              
              {/* Option Costs */}
              {Object.entries(result.estimate.breakdown.option_costs).map(([option, cost]) => (
                <div key={option} className="flex justify-between">
                  <span className="text-muted-foreground capitalize">{option.replace(/_/g, " ")}</span>
                  <span className="font-medium">
                    ${cost.toFixed(2)}
                  </span>
                </div>
              ))}
              
              {/* Rush Fee */}
              {result.estimate.breakdown.rush_fee > 0 && (
                <div className="flex justify-between text-orange-600">
                  <span>Rush Fee (30%)</span>
                  <span className="font-medium">
                    +${result.estimate.breakdown.rush_fee.toFixed(2)}
                  </span>
                </div>
              )}
              
              {/* Quantity Discount */}
              {result.estimate.breakdown.quantity_discount < 0 && (
                <div className="flex justify-between text-green-600">
                  <span>Quantity Discount</span>
                  <span className="font-medium">
                    ${result.estimate.breakdown.quantity_discount.toFixed(2)}
                  </span>
                </div>
              )}
              
              <Separator className="my-2" />
              
              {/* Margin */}
              <div className="flex justify-between text-muted-foreground">
                <span>Margin ({result.estimate.breakdown.margin_percent}%)</span>
                <span className="font-medium">
                  ${result.estimate.breakdown.margin_amount.toFixed(2)}
                </span>
              </div>
              
              <div className="flex justify-between">
                <span className="text-muted-foreground">Subtotal</span>
                <span className="font-medium">
                  ${result.estimate.subtotal.toFixed(2)}
                </span>
              </div>
              
              <div className="flex justify-between">
                <span className="text-muted-foreground">Tax</span>
                <span className="font-medium">
                  ${result.estimate.tax.toFixed(2)}
                </span>
              </div>
            </div>

            <Separator />

            {/* Total */}
            <div className="flex justify-between text-lg font-bold">
              <span>Total</span>
              <span className="text-primary">
                {result.estimate.currency} ${result.estimate.total.toFixed(2)}
              </span>
            </div>

            {/* Notes */}
            {result.estimate.estimate_notes.length > 0 && (
              <div className="pt-2 text-xs text-muted-foreground">
                <p className="font-medium mb-1">Notes:</p>
                <ul className="list-disc list-inside space-y-0.5">
                  {result.estimate.estimate_notes.map((note, i) => (
                    <li key={i}>{note}</li>
                  ))}
                </ul>
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}

export type { IntakeResponse };
