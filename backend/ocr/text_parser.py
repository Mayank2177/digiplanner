import re
from datetime import datetime
import random


# ---------- HELPERS ----------

def _clean_amount(val):
    try:
        if not val: return 0.0
        # OCR Autocorrect: Fix common misreadings
        # O/o -> 0, S/s -> 5, I/l/| -> 1, B -> 8
        clean_val = val.lower()
        clean_val = clean_val.replace("o", "0").replace("s", "5").replace("i", "1").replace("l", "1").replace("|", "1").replace("b", "8")
        clean_val = clean_val.replace(",", "")
        # Remove any non-numeric characters except dots
        clean_val = "".join(c for c in clean_val if c.isdigit() or c == ".")
        return float(clean_val)
    except Exception:
        return 0.0


def _round2(val):
    """
    Round to 2 decimal places using math to satisfy strict linters.
    """
    return int(val * 100 + 0.5) / 100.0


def _default_bill_id():
    return f"BILL-{random.randint(100000, 999999)}"


def _extract_date(text):
    """
    NLP-style date extraction (multiple formats)
    """
    patterns = [
        r"\b(\d{4}-\d{2}-\d{2})\b",          # 2024-01-27
        r"\b(\d{2}/\d{2}/\d{4})\b",          # 27/01/2024
        r"\b(\d{2}-\d{2}-\d{4})\b",          # 27-01-2024
    ]

    for p in patterns:
        m = re.search(p, text)
        if m:
            raw = m.group(1)
            try:
                if "-" in raw and raw.count("-") == 2:
                    return datetime.strptime(raw, "%Y-%m-%d").strftime("%Y-%m-%d")
                if "/" in raw:
                    return datetime.strptime(raw, "%d/%m/%Y").strftime("%Y-%m-%d")
            except Exception:
                pass

    # fallback → today
    return datetime.today().strftime("%Y-%m-%d")


from ocr.templates import get_matching_template

# ---------- MAIN PARSER ----------

def parse_receipt(text: str):
    """
    Returns structured data and item list from raw OCR text.
    First tries template-based parsing, then falls back to generic rules.
    """
    
    # Try template-based parsing first
    template = get_matching_template(text)
    template_data = {}
    
    if template:
        # Extract fields using template patterns
        if template.bill_id_pattern:
            m = re.search(template.bill_id_pattern, text)
            if m: template_data['bill_id'] = m.group(1)
            
        if template.date_pattern:
            m = re.search(template.date_pattern, text)
            if m: template_data['date'] = m.group(1) # Note: might need normalization
            
        if template.total_pattern:
            m = re.search(template.total_pattern, text)
            if m: template_data['amount'] = _clean_amount(m.group(1))

        if template.tax_pattern:
            m = re.search(template.tax_pattern, text)
            if m: template_data['tax'] = _clean_amount(m.group(1))

        if template.subtotal_pattern:
            m = re.search(template.subtotal_pattern, text)
            if m: template_data['subtotal'] = _clean_amount(m.group(1))

        template_data['vendor'] = template.name

    lines = [l.strip() for l in text.splitlines() if l.strip()]

    # ---------- BILL ID ----------
    bill_id = template_data.get('bill_id')
    if not bill_id:
        # Reordered and added word boundaries to prevent partial matches like 'action' from 'Transaction'
        bill_prefixes = r"(?:transaction|invoice|receipt|order|ticket|bill|inv|rec|txn|trans)"
        bill_patterns = [
            rf"(?i)\b{bill_prefixes}\b\s*(?:no|id|number|#)?\s*[:.-]?\s*([a-zA-Z0-9/-]+)",
            r"(?i)#\s*([a-zA-Z0-9/-]+)",
            r"(?i)\b(?:inv|rec|txn)\b\s*[:.-]?\s*([a-zA-Z0-9/-]+)"
        ]
        
        for l in lines:
            for p in bill_patterns:
                m = re.search(p, l)
                if m:
                    candidate = m.group(1)
                    if candidate and len(candidate) > 2 and not any(kw in candidate.lower() for kw in ['total', 'tax', 'date', 'amount', 'item']):
                        bill_id = candidate
                        break
            if bill_id:
                break

    if not bill_id:
        bill_id = _default_bill_id()

    # ---------- VENDOR ----------
    vendor = template_data.get('vendor')
    if not vendor:
        vendor = "Unknown Vendor"
        generic_headers = ["tax invoice", "cash receipt", "bill of supply", "estimate", "original", "trans"]
        
        # Using simple loop to avoid slice indexing lint errors
        for i, line_text in enumerate(lines):
            if i >= 3:
                break
            if line_text.lower().strip() not in generic_headers and len(line_text) > 3:
                vendor = line_text
                break

    # ---------- DATE ----------
    date = template_data.get('date')
    if not date:
        date = _extract_date(text)
    else:
        # Basic normalization for template dates
        try:
            # Try some common formats or just return as is if it looks okay
            if re.match(r"\d{4}-\d{2}-\d{2}", date):
                pass 
            elif "/" in date:
                parts = date.split("/")
                if len(parts) == 3:
                    if len(parts[2]) == 2: parts[2] = "20" + parts[2]
                    # Default: Assume MM/DD/YYYY structure for US templates
                    # parts[0]=MM, parts[1]=DD, parts[2]=YYYY
                    mm, dd, yyyy = parts[0], parts[1], parts[2]
                    
                    # If MM > 12, swap to DD/MM/YYYY
                    if int(mm) > 12:
                         mm, dd = dd, mm
                         
                    date = f"{yyyy}-{mm}-{dd}"
        except:
             date = _extract_date(text)

    # ---------- FINANCIALS ----------
    total = 0.0
    tax = 0.0
    subtotal = 0.0
    
    potential_totals = []
    potential_taxes = []
    potential_subtotals = []

    # Clean text globally for labels and numbers (Noise reduction)
    clean_text = text.lower().replace("o", "0").replace("s", "5").replace("t[a4]x", "tax")
    all_numbers = [_clean_amount(n) for n in re.findall(r"\d+[.,]\d{2,3}\b|\b\d+\.\d+\b", clean_text)]
    
    for l in lines:
        # Normalize the line for better matching
        l_clean = l.lower().replace("o", "0").replace("s", "5").replace("|", "1").replace("i", "1")
        nums = re.findall(r"\d+[.,]\d{2,3}\b|\b\d+\.\d+\b", l_clean)
        if not nums:
            nums = re.findall(r"\d+[.,]?\d*", l_clean)
            
        current_nums = [_clean_amount(n) for n in nums if len(n) > 1]
        
        # TOTAL keywords: Prioritize "Grand Total" and handle fuzzy/corrupted labels
        if re.search(r"(?i)\b(grand\s*total|t[o0]t[a4]l|due|payable|amount|net\s*total)\b", l):
            if current_nums:
                potential_totals.append(current_nums[-1])
        
        # TAX keywords: Exhaustive list (Service Charge, VAT, GST, Sales Tax, Cess, etc.)
        tax_keywords = r"(?i)\b(tax|g\s*s\s*t|v\s*a\s*t|cgst|sgst|igst|utgst|sales\s*tax|service\s*charge|service\s*tax|luxury\s*tax|cess|hsn|sac|tva|iva|mwst|consumption\s*tax|tax\s*amount)\b"
        if re.search(tax_keywords, l):
            if "invoice" not in l.lower():
                if current_nums:
                    potential_taxes.append(current_nums[-1])
                else:
                    # Multi-line association: Check the next line if the current line has a tax label but no number
                    try:
                        next_line = lines[lines.index(l) + 1]
                        next_nums = re.findall(r"\d+[.,]\d{2,3}\b|\b\d+\.\d+\b", next_line)
                        if next_nums:
                            potential_taxes.append(_clean_amount(next_nums[0]))
                    except (IndexError, ValueError):
                        pass

        # SUBTOTAL keywords: Fuzzy matching
        if re.search(r"(?i)\b(sub\s*t[o0]t[a4]l|sub\s*ttl|sub\s*tot|stot|net\s*amount|net\s*amt|taxable|sub)\b", l):
            if current_nums:
                potential_subtotals.append(current_nums[-1])

    # Initial guesses
    total = template_data.get('amount') or (potential_totals[-1] if potential_totals else 0.0)
    tax = template_data.get('tax') or (potential_taxes[-1] if potential_taxes else 0.0)
    subtotal = template_data.get('subtotal') or (potential_subtotals[-1] if potential_subtotals else 0.0)

    # --- VERIFICATION ENGINE (PHASE 4) ---
    # Goal: Subtotal + Tax = Total
    
    # 1. Check if we found valid data already
    if total > 0 and abs((subtotal + tax) - total) < 0.1:
        pass # All good
    
    # 2. Try to find Total from all_numbers if missing
    if total == 0 and all_numbers:
        total = max(all_numbers)
        
    # 3. Explicit "No Tax" Case: If Subtotal and Total are near identical
    if total > 0 and tax == 0 and subtotal > 0:
        if abs(subtotal - total) < 1.0:
            subtotal = total
            tax = 0.0
            
    # 4. Solve for missing field if we have 2 out of 3
    if total > 0:
        if subtotal == 0 and tax > 0:
            subtotal = total - tax
        elif tax == 0 and subtotal > 0 and subtotal != total:
            tax = total - subtotal

    # 5. Advanced Brute Force Search
    if abs((subtotal + tax) - total) > 0.5:
        best_fit = None
        unique_nums = sorted(list(set(all_numbers)), reverse=True)
        
        # Priority: Match with existing Total
        if total > 0:
            for a in unique_nums:
                if a >= total: continue
                # Search for a tax that completes the total
                for b in unique_nums:
                    if abs((a + b) - total) < 0.1:
                        best_fit = (a, b, total)
                        break
                if best_fit: break
        
        if best_fit:
            subtotal, tax, total = best_fit

    # Final Fallbacks
    if total == 0.0 and all_numbers:
        total = max(all_numbers)
        
    if subtotal == 0.0 and total > 0:
        subtotal = total - tax
    elif subtotal > total: # Sanity check
        subtotal = total 
        tax = 0.0
    
    if subtotal < 0: subtotal = total

    # ---------- ITEMS ----------
    items = []
    # Identify item lines: [Quantity] [Name] [Price] or [Name] [Price]
    item_keywords_ignore = r"(?i)(total|subtotal|subttl|tax|vat|gst|change|cash|card|due|savings|discount|round|balance|items|summary|charge)"
    
    for l in lines:
        if re.search(r"(\d+\s*x\s*\d+)", l): # Skip multiplier lines for now or handle them
            pass
            
        if re.search(item_keywords_ignore, l):
            continue

        # Pattern 1: [Quantity] [Name] ... [Price]
        # Example: "2 Pizza 500.00"
        m = re.search(r"^(\d+)\s+(.+?)\s+₹?\s*(\d+[.,]\d{2}|\d+\.\d+)\s*$", l)
        if m:
            qty = int(m.group(1))
            name = m.group(2).strip()
            total_price = _clean_amount(m.group(3))
            if 0 < total_price <= total and len(name) > 1:
                items.append({"Item": name, "Quantity": qty, "Price": total_price})
                continue
                
        # Pattern 2: [Name] ... [Price]
        # Example: "Pizza 250.00"
        m = re.search(r"^(.+?)\s+₹?\s*(\d+[.,]\d{2}|\d+\.\d+)\s*[*x]?$", l)
        if not m:
            m = re.search(r"^(.+?)\s+₹?\s*(\d+)\s*[*x]?$", l)
            
        if m:
            name = m.group(1).strip()
            price = _clean_amount(m.group(2))
            if 0 < price <= total and len(name) > 2:
                items.append({
                    "Item": name,
                    "Price": price
                })

    # --- ITEM SUM VERIFICATION ---
    # If subtotal is 0 but we have items, use their sum
    item_sum = sum(i.get("Price", 0.0) for i in items)
    if subtotal == 0 and item_sum > 0:
        if total == 0 or abs(item_sum - total) < 0.5:
             subtotal = item_sum
             if total == 0: total = subtotal + tax
    elif subtotal > 0 and item_sum > 0:
        # If item sum is very close to subtotal, we have high confidence
        if abs(item_sum - subtotal) < 0.1:
            pass # High confidence

    # ---------- CATEGORY DETECTION (Rule-based) ----------
    def _extract_category(text, vendor):
        text_lower = text.lower()
        vendor_lower = vendor.lower()
        
        keywords = {
            "Utility": ["power", "electricity", "water", "gas", "bescom", "tata power", "bill", "supply", "electric", "broadband", "mobile", "recharge"],
            "Food": ["restaurant", "cafe", "kitchen", "hotel", "dining", "burger", "pizza", "swiggy", "zomato", "coffee", "tea", "bistro", "foods", "bakery", "canteen"],
            "Grocery": ["mart", "super market", "fresh", "store", "vegetable", "fruit", "market", "grocer", "kirana", "basket", "reliance", "dmart", "bigbasket"],
            "Medical": ["pharmacy", "hospital", "clinic", "doctor", "dr.", "medplus", "apollo", "pharma", "health", "medical", "diagnostic", "lab"],
            "Travel": ["fuel", "petrol", "diesel", "station", "pump", "uber", "ola", "rapido", "ride", "trip", "travel", "fastag", "toll"],
            "Shopping": ["retail", "fashion", "clothing", "trends", "zudio", "apparel", "garment", "mall", "shoe", "footwear", "lifestyle", "westside", "hm", "zara", "school shop"],
            "Entertainment": ["movie", "cinema", "theatre", "show", "entertainment", "game", "fun", "club", "resort"]
        }
        
        # Check vendor name first (higher priority)
        for cat, kw_list in keywords.items():
            if any(k in vendor_lower for k in kw_list):
                return cat
                
        # Check entire text
        for cat, kw_list in keywords.items():
            if any(k in text_lower for k in kw_list):
                return cat
                
        return "Uncategorized"

    category = _extract_category(text, vendor)

    # ---------- FINAL DATA ----------
    data = {
        "bill_id": bill_id,
        "vendor": vendor,
        "date": date,
        "amount": _round2(total),
        "tax": _round2(tax),
        "subtotal": _round2(subtotal),
        "category": category
    }

    return data, items