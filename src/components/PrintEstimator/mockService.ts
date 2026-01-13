/**
 * Mock Service for Demo Mode
 * 
 * This module provides simulated API responses when the backend is unavailable.
 * Used for:
 * - Assessment demonstrations without running Docker
 * - Frontend development without backend dependency
 * - Showcase mode in production
 * 
 * IMPORTANT: This is NOT production code - it's for demo purposes only.
 * Real API logic remains in the main component for actual Docker usage.
 * 
 * Response structure matches the enhanced backend schemas:
 * - PriceEstimate with print_method, breakdown, subtotal, tax, total
 * - PricingBreakdown with material_cost, print_cost, setup_cost, etc.
 */

import { IntakeRequest } from "./IntakeForm";
import { IntakeResponse } from "./EstimateResult";

/**
 * Generates a realistic mock response based on input content.
 * Parses the input text to extract basic info for more realistic demo.
 * 
 * Response structure matches backend's IntakeResponse schema exactly.
 */
export function generateMockResponse(request: IntakeRequest): IntakeResponse {
  // Generate a realistic request ID
  const requestId = `demo-${Date.now().toString(36)}-${Math.random().toString(36).substring(2, 7)}`;
  
  // Parse content for more realistic response
  const content = request.content?.toLowerCase() || "";
  
  // Detect product type from content
  const productType = detectProductType(content);
  
  // Detect quantity from content
  const quantity = detectQuantity(content);
  
  // Determine print method based on quantity (realistic business logic)
  const { method: printMethod, reason: printMethodReason } = determinePrintMethod(quantity, productType);
  
  // Detect additional specs
  const sides = detectSides(content);
  const options = detectOptions(content);
  const isRush = detectRush(content);
  const turnaroundDays = detectTurnaround(content);
  
  // Calculate realistic pricing with full breakdown
  const pricing = calculateMockPricing(productType, quantity, printMethod, sides, options, isRush);
  
  // Generate validation based on content completeness
  const validation = generateValidation(content, productType, quantity);
  
  return {
    request_id: requestId,
    status: validation.is_valid ? "success" : "validation_errors",
    extracted_specs: {
      product_type: productType,
      quantity: quantity,
      size: detectSize(content, productType),
      paper_stock: detectPaperStock(content),
      sides: sides,
      color_mode: detectColorMode(content),
      finish: detectFinish(content),
      options: options,
      turnaround_days: turnaroundDays,
      is_rush: isRush,
      artwork_dpi: detectArtworkDpi(content),
      raw_input: request.content,
    },
    validation: validation,
    estimate: {
      print_method: printMethod,
      print_method_reason: printMethodReason,
      breakdown: pricing.breakdown,
      subtotal: pricing.subtotal,
      tax: pricing.tax,
      total: pricing.total,
      currency: "USD",
      estimate_notes: [
        `Demo mode - prices are illustrative only`,
        quantity >= 1000 ? "Volume discount applied" : "Standard pricing tier",
        isRush ? "Rush fee included" : "Standard turnaround",
      ],
    },
  };
}

/**
 * Detects product type from natural language input
 */
function detectProductType(content: string): string {
  if (content.includes("business card")) return "business_cards";
  if (content.includes("flyer") || content.includes("flier")) return "flyers";
  if (content.includes("brochure")) return "brochures";
  if (content.includes("poster")) return "posters";
  if (content.includes("banner")) return "banners";
  if (content.includes("postcard")) return "postcards";
  if (content.includes("letterhead")) return "letterheads";
  if (content.includes("envelope")) return "envelopes";
  if (content.includes("booklet")) return "booklets";
  if (content.includes("catalog")) return "catalogs";
  return "business_cards"; // Default fallback
}

/**
 * Extracts quantity from text using regex patterns
 */
function detectQuantity(content: string): number {
  // Look for patterns like "500", "1,000", "5k"
  const patterns = [
    /(\d{1,3}(?:,\d{3})*)\s*(?:copies|pieces|units|cards|flyers|brochures)?/i,
    /(\d+)k\b/i, // 5k = 5000
    /(\d+)\s+/,
  ];
  
  for (const pattern of patterns) {
    const match = content.match(pattern);
    if (match) {
      let num = match[1].replace(/,/g, "");
      if (content.includes(match[0]) && match[0].toLowerCase().includes("k")) {
        return parseInt(num) * 1000;
      }
      return parseInt(num) || 500;
    }
  }
  return 500; // Default quantity
}

/**
 * Determines print method based on quantity and product type
 * Digital: < 500 (faster, per-unit cost higher)
 * Offset: >= 500 (slower setup, lower per-unit cost)
 * 
 * Returns method and explanation (matches backend logic)
 */
function determinePrintMethod(
  quantity: number,
  productType: string
): { method: "digital" | "offset"; reason: string } {
  // Offset threshold - typically 500 for most products
  const offsetThreshold = productType === "posters" ? 250 : 500;
  
  if (quantity >= offsetThreshold) {
    return {
      method: "offset",
      reason: `Quantity of ${quantity} exceeds ${offsetThreshold} - offset printing is more cost-effective at this volume`
    };
  } else {
    return {
      method: "digital",
      reason: `Quantity of ${quantity} is below ${offsetThreshold} - digital printing offers faster turnaround and no plate setup`
    };
  }
}

/**
 * Detects paper size from content
 */
function detectSize(content: string, productType: string): string {
  if (content.includes("3.5x2") || content.includes("3.5 x 2")) return "3.5x2";
  if (content.includes("8.5x11") || content.includes("letter")) return "8.5x11";
  if (content.includes("11x17")) return "11x17";
  if (content.includes("4x6")) return "4x6";
  if (content.includes("5x7")) return "5x7";
  if (content.includes("a4")) return "A4";
  if (content.includes("a3")) return "A3";
  
  // Default sizes based on product type
  const defaults: Record<string, string> = {
    business_cards: "3.5x2",
    flyers: "8.5x11",
    brochures: "8.5x11",
    posters: "11x17",
    postcards: "4x6",
    letterheads: "8.5x11",
    envelopes: "#10",
  };
  return defaults[productType] || "8.5x11";
}

/**
 * Detects paper stock (type + weight) from content
 * Matches backend's paper_stock field
 */
function detectPaperStock(content: string): string {
  // Check for weight first
  let weight = "";
  if (content.includes("14pt") || content.includes("14 pt")) weight = "14pt";
  else if (content.includes("16pt") || content.includes("16 pt")) weight = "16pt";
  else if (content.includes("100lb") || content.includes("100 lb")) weight = "100lb";
  else if (content.includes("80lb") || content.includes("80 lb")) weight = "80lb";
  else weight = "14pt";
  
  // Check for type
  let type = "";
  if (content.includes("glossy") || content.includes("gloss")) type = "gloss";
  else if (content.includes("matte")) type = "matte";
  else if (content.includes("cardstock") || content.includes("card stock")) type = "cardstock";
  else if (content.includes("recycled")) type = "recycled";
  else if (content.includes("uncoated")) type = "uncoated";
  else type = "cardstock";
  
  return `${weight} ${type}`;
}

/**
 * Detects printing sides from content
 */
function detectSides(content: string): "single" | "double" {
  if (content.includes("double-sided") || content.includes("double sided") || content.includes("both sides")) {
    return "double";
  }
  if (content.includes("single-sided") || content.includes("single sided") || content.includes("one side")) {
    return "single";
  }
  return "double"; // Default for business cards
}

/**
 * Detects color mode from content
 */
function detectColorMode(content: string): string {
  if (content.includes("full color") || content.includes("full-color") || content.includes("cmyk")) {
    return "full_color";
  }
  if (content.includes("black and white") || content.includes("b&w") || content.includes("grayscale")) {
    return "black_white";
  }
  if (content.includes("spot color") || content.includes("pantone")) {
    return "spot_color";
  }
  return "full_color";
}

/**
 * Detects finish from content
 */
function detectFinish(content: string): string {
  if (content.includes("matte")) return "matte";
  if (content.includes("gloss") || content.includes("glossy")) return "gloss";
  if (content.includes("satin")) return "satin";
  if (content.includes("uncoated")) return "uncoated";
  if (content.includes("soft touch")) return "soft_touch";
  return "matte";
}

/**
 * Detects additional options from content
 */
function detectOptions(content: string): string[] {
  const options: string[] = [];
  
  if (content.includes("rounded corner")) options.push("rounded_corners");
  if (content.includes("foil") || content.includes("gold foil") || content.includes("silver foil")) {
    options.push("foil_stamping");
  }
  if (content.includes("emboss")) options.push("embossing");
  if (content.includes("spot uv") || content.includes("spot-uv")) options.push("spot_uv");
  if (content.includes("laminate") || content.includes("lamination")) options.push("lamination");
  if (content.includes("perforate") || content.includes("perforation")) options.push("perforation");
  if (content.includes("die cut") || content.includes("die-cut")) options.push("die_cut");
  
  return options;
}

/**
 * Detects rush order from content
 */
function detectRush(content: string): boolean {
  return content.includes("rush") || 
         content.includes("urgent") || 
         content.includes("asap") || 
         content.includes("next day") ||
         content.includes("same day");
}

/**
 * Detects turnaround days from content
 */
function detectTurnaround(content: string): number | undefined {
  const dayMatch = content.match(/(\d+)\s*(?:day|business day)/i);
  if (dayMatch) {
    return parseInt(dayMatch[1]);
  }
  if (content.includes("same day")) return 0;
  if (content.includes("next day")) return 1;
  if (content.includes("rush")) return 2;
  return undefined;
}

/**
 * Detects artwork DPI from content
 */
function detectArtworkDpi(content: string): number | undefined {
  const dpiMatch = content.match(/(\d+)\s*dpi/i);
  if (dpiMatch) {
    return parseInt(dpiMatch[1]);
  }
  return undefined;
}

/**
 * Pricing breakdown structure matching backend's PricingBreakdown schema
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
 * Calculates mock pricing with full breakdown matching backend schema
 * 
 * This simulates the deterministic rule-based pricing engine:
 * - Material cost based on paper and quantity
 * - Print cost based on method (digital vs offset)
 * - Setup cost (higher for offset)
 * - Finishing cost
 * - Option costs (flat or per-unit)
 * - Rush fees
 * - Quantity discounts
 * - Margin calculation
 */
function calculateMockPricing(
  productType: string,
  quantity: number,
  printMethod: "digital" | "offset",
  sides: "single" | "double",
  options: string[],
  isRush: boolean
): { breakdown: PricingBreakdown; subtotal: number; tax: number; total: number } {
  // Base material prices per product type (per unit)
  const materialPrices: Record<string, number> = {
    business_cards: 0.02,
    flyers: 0.05,
    brochures: 0.15,
    posters: 0.35,
    postcards: 0.04,
    letterheads: 0.06,
    envelopes: 0.08,
    banners: 8.00,
    booklets: 0.50,
    catalogs: 1.20,
  };
  
  // Print cost per unit (varies by method)
  const printPrices: Record<string, { digital: number; offset: number }> = {
    business_cards: { digital: 0.06, offset: 0.03 },
    flyers: { digital: 0.10, offset: 0.05 },
    brochures: { digital: 0.30, offset: 0.15 },
    posters: { digital: 0.90, offset: 0.45 },
    postcards: { digital: 0.08, offset: 0.04 },
    letterheads: { digital: 0.12, offset: 0.06 },
    envelopes: { digital: 0.14, offset: 0.07 },
    banners: { digital: 25.00, offset: 20.00 },
    booklets: { digital: 1.50, offset: 0.75 },
    catalogs: { digital: 3.50, offset: 1.75 },
  };
  
  // Option costs
  const optionPrices: Record<string, { flat: number; perUnit: number }> = {
    rounded_corners: { flat: 0, perUnit: 0.01 },
    foil_stamping: { flat: 50, perUnit: 0.05 },
    embossing: { flat: 75, perUnit: 0.04 },
    spot_uv: { flat: 40, perUnit: 0.03 },
    lamination: { flat: 25, perUnit: 0.02 },
    perforation: { flat: 20, perUnit: 0.01 },
    die_cut: { flat: 100, perUnit: 0.06 },
  };
  
  // Calculate material cost
  const materialUnitPrice = materialPrices[productType] || 0.05;
  const material_cost = Math.round(materialUnitPrice * quantity * 100) / 100;
  
  // Calculate print cost
  const printUnitPrices = printPrices[productType] || { digital: 0.10, offset: 0.05 };
  let print_cost = printUnitPrices[printMethod] * quantity;
  
  // Double-sided adds 50% to print cost
  if (sides === "double") {
    print_cost *= 1.5;
  }
  print_cost = Math.round(print_cost * 100) / 100;
  
  // Setup cost (offset is higher)
  const setup_cost = printMethod === "offset" ? 75.00 : 25.00;
  
  // Finishing cost (cutting, coating, packaging)
  const finishing_cost = quantity >= 500 ? 35.00 : 15.00;
  
  // Calculate option costs
  const option_costs: Record<string, number> = {};
  let totalOptionCost = 0;
  for (const option of options) {
    const pricing = optionPrices[option];
    if (pricing) {
      const cost = pricing.flat + (pricing.perUnit * quantity);
      option_costs[option] = Math.round(cost * 100) / 100;
      totalOptionCost += cost;
    }
  }
  
  // Rush fee (30% of subtotal if rush)
  const baseSubtotal = material_cost + print_cost + setup_cost + finishing_cost + totalOptionCost;
  const rush_fee = isRush ? Math.round(baseSubtotal * 0.30 * 100) / 100 : 0;
  
  // Quantity discount
  let discountPercent = 0;
  if (quantity >= 5000) discountPercent = 0.20;
  else if (quantity >= 2500) discountPercent = 0.15;
  else if (quantity >= 1000) discountPercent = 0.10;
  else if (quantity >= 500) discountPercent = 0.05;
  
  const quantity_discount = -Math.round((material_cost + print_cost) * discountPercent * 100) / 100;
  
  // Calculate subtotal before margin
  const costSubtotal = material_cost + print_cost + setup_cost + finishing_cost + 
                       totalOptionCost + rush_fee + quantity_discount;
  
  // Margin (25%)
  const margin_percent = 25;
  const margin_amount = Math.round(costSubtotal * (margin_percent / 100) * 100) / 100;
  
  // Final calculations
  const subtotal = Math.round((costSubtotal + margin_amount) * 100) / 100;
  const taxRate = 0.0825; // 8.25% tax rate
  const tax = Math.round(subtotal * taxRate * 100) / 100;
  const total = Math.round((subtotal + tax) * 100) / 100;
  
  // Ensure minimum order value
  const minOrder = 25.00;
  const finalTotal = Math.max(total, minOrder);
  
  return {
    breakdown: {
      material_cost,
      print_cost,
      setup_cost,
      finishing_cost,
      option_costs,
      rush_fee,
      quantity_discount,
      margin_amount,
      margin_percent,
    },
    subtotal,
    tax,
    total: finalTotal,
  };
}

/**
 * Generates validation result with realistic flags
 * Matches backend's ValidationResult schema
 */
function generateValidation(
  content: string,
  productType: string,
  quantity: number
): { is_valid: boolean; errors: string[]; warnings: string[]; missing_fields: string[] } {
  const errors: string[] = [];
  const warnings: string[] = [];
  const missing_fields: string[] = [];
  
  // Check for basic requirements
  if (!content || content.trim().length < 5) {
    errors.push("Input content is too short or empty");
  }
  
  if (quantity <= 0) {
    errors.push("Quantity must be greater than 0");
  }
  
  if (quantity > 100000) {
    warnings.push("Large order: quantities over 100,000 require manual quote");
  }
  
  // Check for missing common fields (for demo realism)
  if (!content.includes("sided") && !content.includes("side")) {
    missing_fields.push("sides");
    warnings.push("Printing sides not specified - defaulting to double-sided");
  }
  
  if (!content.match(/\d+pt|\d+lb/)) {
    missing_fields.push("paper_stock");
    warnings.push("Paper weight not specified - using standard 14pt");
  }
  
  if (!content.includes("color") && !content.includes("b&w") && !content.includes("grayscale")) {
    missing_fields.push("color_mode");
  }
  
  // Artwork DPI check
  const dpiMatch = content.match(/(\d+)\s*dpi/i);
  if (dpiMatch) {
    const dpi = parseInt(dpiMatch[1]);
    if (dpi < 300) {
      warnings.push(`Artwork DPI (${dpi}) is below recommended 300 DPI - may appear pixelated`);
    }
  }
  
  // Product-specific warnings
  if (productType === "business_cards" && quantity < 100) {
    warnings.push("Minimum recommended quantity for business cards is 100");
  }
  
  if (productType === "posters" && quantity < 10) {
    warnings.push("Minimum recommended quantity for posters is 10");
  }
  
  return {
    is_valid: errors.length === 0,
    errors,
    warnings,
    missing_fields,
  };
}

/**
 * Checks if the backend API is reachable
 * Used to automatically trigger demo mode when backend is down
 */
export async function checkApiHealth(apiUrl: string): Promise<boolean> {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 3000); // 3 second timeout
    
    const response = await fetch(`${apiUrl}/health`, {
      method: "GET",
      signal: controller.signal,
    });
    
    clearTimeout(timeoutId);
    return response.ok;
  } catch {
    // Network error, timeout, or CORS issue = backend unreachable
    return false;
  }
}
