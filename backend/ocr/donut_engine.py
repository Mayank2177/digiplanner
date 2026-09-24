"""
donut_engine.py — DONUT CORD-v2 receipt processing engine (EMERGENCY FIX)

FIXES APPLIED:
- Handle receipts with multiple "Total" lines (take the LAST one)
- Better vendor extraction from first line
- Improved total/subtotal/tax detection
- Service charge handling
"""

import io
import os
import re
from typing import Any, Dict, Optional
from PIL import Image
import torch
from utils.logger import log_error, log_info, log_warning

os.environ['HF_HOME'] = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "models", "hf_cache")
os.environ['TRANSFORMERS_CACHE'] = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "models", "hf_cache")


class DONUTError(Exception):
    """Raised when DONUT processing fails."""
    pass


def clean_price_string(value: Any) -> Optional[str]:
    """Clean a price value by removing currency symbols and validating format."""
    if value is None:
        return None
    
    value_str = str(value).strip()
    
    # Reject values that contain letters (except currency symbols)
    # This filters out ZIP codes (91770), times (39PM), addresses, etc.
    if re.search(r'[a-zA-Z]', value_str):
        # Check if it's ONLY currency symbol + numbers (like "$33.26")
        test_str = re.sub(r'[\$€£¥₹]', '', value_str)
        if re.search(r'[a-zA-Z]', test_str):
            return None  # Contains letters after removing currency
    
    # Remove common currency symbols
    value_str = re.sub(r'[\$€£¥₹]', '', value_str)
    # Remove commas
    value_str = value_str.replace(',', '')
    # Remove parentheses (sometimes used for negative numbers, but we'll ignore them)
    value_str = value_str.replace('(', '').replace(')', '')
    # Keep only digits and decimal point
    value_str = re.sub(r'[^\d.]', '', value_str)
    
    # Validate it's a proper number
    try:
        float_val = float(value_str)
        # Receipt amounts should be reasonable: $0.01 to $10,000
        if float_val < 0.01 or float_val > 10000:
            return None
        # ZIP codes often have 5 digits with no decimal - filter them out
        if float_val > 999 and '.' not in str(value):
            return None
        return value_str
    except ValueError:
        return None


def validate_date(date_str: str) -> bool:
    """Validate if a string looks like a date."""
    if not date_str:
        return False
    
    date_patterns = [
        r'\d{1,2}[-/]\d{1,2}[-/]\d{2,4}',
        r'\d{4}[-/]\d{1,2}[-/]\d{1,2}',
        r'\d{1,2}\s+\w+\s+\d{4}',
        r'\w{3}\s+\d{1,2},?\s+\d{4}',  # Apr 01, 2019
    ]
    
    for pattern in date_patterns:
        if re.search(pattern, str(date_str)):
            return True
    return False


class ReceiptProcessor:
    """DONUT CORD-v2 receipt processor with robust extraction."""
    
    def __init__(self, model_name: str = "naver-clova-ix/donut-base-finetuned-cord-v2"):
        try:
            from transformers import DonutProcessor, VisionEncoderDecoderModel
            import os
            
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            model_dir = os.path.join(project_root, "models", "donut_model")
            os.makedirs(model_dir, exist_ok=True)
            
            log_info(f"Loading DONUT model: {model_name}")
            log_info(f"Model directory: {model_dir}")
            
            model_config = os.path.join(model_dir, "config.json")
            if os.path.exists(model_config):
                log_info("✅ Loading DONUT from local cache...")
                self.processor = DonutProcessor.from_pretrained(model_dir)
                self.model = VisionEncoderDecoderModel.from_pretrained(model_dir)
            else:
                log_info("📥 First-time download: Downloading DONUT model (~800MB)...")
                log_info("⏳ This will take 5-10 minutes. Model will be saved locally.")
                self.processor = DonutProcessor.from_pretrained(model_name)
                self.model = VisionEncoderDecoderModel.from_pretrained(model_name)
                
                log_info(f"💾 Saving model to {model_dir}...")
                self.processor.save_pretrained(model_dir)
                self.model.save_pretrained(model_dir)
                log_info("✅ Model saved locally. Next startup will be instant!")
            
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            self.model.to(self.device)
            
            log_info(f"✅ DONUT CORD-v2 loaded successfully on {self.device}")
            
        except ImportError as e:
            log_error(f"Transformers not installed: {e}")
            raise DONUTError("Transformers not installed. Run: pip install transformers torch")
        except Exception as e:
            log_error(f"Failed to load DONUT model: {e}")
            raise DONUTError(f"Could not initialize DONUT: {e}")
    
    def extract_receipt_data(self, image: Image.Image) -> Dict[str, Any]:
        """Extract structured receipt data using DONUT CORD-v2."""
        try:
            if image.mode != "RGB":
                image = image.convert("RGB")
            
            pixel_values = self.processor(image, return_tensors="pt").pixel_values.to(self.device)
            
            task_prompt = "<s_cord-v2>"
            decoder_input_ids = self.processor.tokenizer(
                task_prompt,
                add_special_tokens=False,
                return_tensors="pt"
            ).input_ids.to(self.device)
            
            log_info("Running DONUT CORD-v2 inference...")
            outputs = self.model.generate(
                pixel_values,
                decoder_input_ids=decoder_input_ids,
                max_length=self.model.config.decoder.max_position_embeddings,
                pad_token_id=self.processor.tokenizer.pad_token_id,
                eos_token_id=self.processor.tokenizer.eos_token_id,
                use_cache=True,
                bad_words_ids=[[self.processor.tokenizer.unk_token_id]],
                return_dict_in_generate=True,
                num_beams=1,
                early_stopping=True,
            )
            
            sequence = self.processor.batch_decode(outputs.sequences)[0]
            log_info(f"DONUT raw output: {sequence[:300]}...")
            
            sequence = sequence.replace(self.processor.tokenizer.eos_token, "")
            sequence = sequence.replace(self.processor.tokenizer.pad_token, "")
            sequence = sequence.replace(task_prompt, "")
            
            try:
                parsed_json = self.processor.token2json(sequence)
                log_info(f"DONUT parsed JSON: {parsed_json}")
            except Exception as parse_error:
                log_error(f"Failed to parse DONUT output to JSON: {parse_error}")
                return self._get_empty_extraction()
            
            return self._normalize_cord_output(parsed_json)
            
        except Exception as e:
            log_error(f"DONUT inference failed: {e}")
            raise DONUTError(f"Receipt extraction failed: {e}")
    
    def _normalize_cord_output(self, cord_json: Dict) -> Dict[str, Any]:
        """
        Normalize CORD-v2 output with EMERGENCY FIXES for presentation.
        
        DONUT CORD-v2 returns highly variable JSON structures:
        - menu can be dict or list
        - total can be dict or list
        - sub_total can be nested inside total items
        - vendor might be in menu.nm or menu[0].nm
        """
        log_info(f"Normalizing CORD output: {cord_json}")
        
        try:
            # EMERGENCY FIX: Extract vendor
            vendor = None
            
            # Try structured keys first
            for store_key in ["store_info", "store", "company", "merchant"]:
                if store_key in cord_json:
                    store_obj = cord_json[store_key]
                    if isinstance(store_obj, dict):
                        vendor = store_obj.get("name") or store_obj.get("store_name") or store_obj.get("company")
                        if vendor:
                            break
            
            # EMERGENCY: Extract from menu structure (can be dict or list)
            if not vendor and "menu" in cord_json:
                menu = cord_json["menu"]
                
                # If menu is a dict, vendor is in menu.nm
                if isinstance(menu, dict):
                    vendor = menu.get("nm")
                    if vendor:
                        log_info(f"Extracted vendor from menu.nm: {vendor}")
                
                # If menu is a list, vendor might be in first item
                elif isinstance(menu, list) and len(menu) > 0:
                    first_item = menu[0]
                    if isinstance(first_item, dict):
                        first_nm = first_item.get("nm", "")
                        price_field = first_item.get("price")
                        
                        # Check if first item looks like a header (business name)
                        # Business names usually don't have prices or have text prices
                        has_valid_price = False
                        if price_field:
                            cleaned_price = clean_price_string(price_field)
                            if cleaned_price:
                                has_valid_price = True
                        
                        # Also check if the name looks like a business (contains "Restaurant", "Cafe", etc.)
                        looks_like_business = any(word in first_nm.lower() for word in 
                            ['restaurant', 'cafe', 'shop', 'store', 'bar', 'grill', 'kitchen', 'diner', 'bistro'])
                        
                        if first_nm and (not has_valid_price or looks_like_business):
                            vendor = first_nm
                            log_info(f"Extracted vendor from menu[0].nm: {vendor}")
            
            # EMERGENCY FIX: Find financial data (can be deeply nested)
            total = None
            tax = None
            subtotal = None
            service_charge = None
            
            # Recursive function to search for financial fields in nested structures
            def search_nested_fields(obj, path=""):
                """Recursively search for total, tax, subtotal in nested dict/list."""
                found_data = {
                    "totals": [],
                    "taxes": [],
                    "subtotals": [],
                    "service_charges": []
                }
                
                if isinstance(obj, dict):
                    # Check this level for financial fields
                    for key in ["total_price", "total", "grand_total", "final_total"]:
                        if key in obj:
                            value = obj[key]
                            # Skip values that contain "%" or "TIP" (tip suggestions)
                            if isinstance(value, str) and ('%' in value or 'tip' in value.lower()):
                                continue
                            cleaned = clean_price_string(value)
                            if cleaned:
                                found_data["totals"].append(float(cleaned))
                                log_info(f"Found total at {path}.{key}: ${cleaned}")
                    
                    # IMPORTANT: Skip cashprice and changeprice if they contain tip percentages
                    for key in ["cashprice", "changeprice"]:
                        if key in obj:
                            value = obj[key]
                            # Only use these if they don't contain '%' or 'tip'
                            if isinstance(value, str) and ('%' in value or 'tip' in value.lower() or ':' in value):
                                log_info(f"Skipping {key} at {path} (looks like tip suggestion): {value}")
                                continue
                            cleaned = clean_price_string(value)
                            if cleaned:
                                found_data["totals"].append(float(cleaned))
                                log_info(f"Found total at {path}.{key}: ${cleaned}")
                    
                    for key in ["tax_price", "tax", "TAX"]:
                        if key in obj:
                            value = obj[key]
                            # Skip tax values with parentheses (those are tip-related)
                            if isinstance(value, str) and ('(' in value or ')' in value):
                                log_info(f"Skipping {key} at {path} (has parentheses, likely tip calc): {value}")
                                continue
                            cleaned = clean_price_string(value)
                            if cleaned:
                                found_data["taxes"].append(float(cleaned))
                                log_info(f"Found tax at {path}.{key}: ${cleaned}")
                    
                    for key in ["subtotal_price", "subtotal", "Subtotal"]:
                        if key in obj:
                            cleaned = clean_price_string(obj[key])
                            if cleaned:
                                # CRITICAL FIX: If this subtotal_price is under a service charge item,
                                # it's actually the FINAL TOTAL, not a subtotal!
                                parent_is_service_charge = False
                                if "nm" in obj:
                                    nm_lower = str(obj["nm"]).lower()
                                    if "service" in nm_lower and "charge" in nm_lower:
                                        parent_is_service_charge = True
                                        found_data["totals"].append(float(cleaned))
                                        log_info(f"Found FINAL TOTAL at {path}.{key} (service charge item): ${cleaned}")
                                
                                if not parent_is_service_charge:
                                    found_data["subtotals"].append(float(cleaned))
                                    log_info(f"Found subtotal at {path}.{key}: ${cleaned}")
                    
                    # Check for service charge in name field
                    if "nm" in obj:
                        nm = str(obj["nm"]).lower()
                        if "service" in nm or "s. service charge" in nm:
                            # Look for the price in subtotal_price or other price fields
                            for price_key in ["subtotal_price", "price", "total_price"]:
                                if price_key in obj:
                                    cleaned = clean_price_string(obj[price_key])
                                    if cleaned:
                                        found_data["service_charges"].append(float(cleaned))
                                        log_info(f"Found service charge at {path}.nm: ${cleaned}")
                                        break
                    
                    # Recurse into nested dicts
                    for key, value in obj.items():
                        nested = search_nested_fields(value, f"{path}.{key}")
                        for k in found_data:
                            found_data[k].extend(nested[k])
                
                elif isinstance(obj, list):
                    # Recurse into list items
                    for i, item in enumerate(obj):
                        nested = search_nested_fields(item, f"{path}[{i}]")
                        for k in found_data:
                            found_data[k].extend(nested[k])
                
                return found_data
            
            # Search the entire JSON structure
            all_financial_data = search_nested_fields(cord_json, "root")
            
            # Pick the highest total (final total after all charges)
            if all_financial_data["totals"]:
                total = str(max(all_financial_data["totals"]))
                log_info(f"✅ Selected highest total: ${total}")
            
            # Pick the highest tax (most accurate)
            if all_financial_data["taxes"]:
                tax = str(max(all_financial_data["taxes"]))
                log_info(f"✅ Selected tax: ${tax}")
            
            # Pick the appropriate subtotal
            # If we found a service charge total, the subtotal should be BEFORE service charge
            if all_financial_data["subtotals"]:
                # Filter out obviously wrong subtotals (like timestamps "0512")
                valid_subtotals = [s for s in all_financial_data["subtotals"] if s > 0.50]
                
                # If we have a total and tax, the subtotal should be close to (total - service_charge)
                # Pick the subtotal that makes sense
                if valid_subtotals:
                    if total and tax:
                        total_num = float(total)
                        tax_num = float(tax)
                        # Find subtotal closest to (total - tax - service_charge)
                        # Or just pick the one that's less than total
                        reasonable_subtotals = [s for s in valid_subtotals if s < total_num * 0.95]
                        if reasonable_subtotals:
                            subtotal = str(max(reasonable_subtotals))
                        else:
                            subtotal = str(min(valid_subtotals))  # Pick smallest if all are too high
                    else:
                        subtotal = str(max(valid_subtotals))
                    
                    log_info(f"✅ Selected subtotal: ${subtotal}")
            
            # VALIDATION: Check if subtotal + tax ≈ total (within 10% tolerance)
            # BUT: If there's a service charge, the math is: subtotal + tax + service_charge = total
            if total and tax:
                try:
                    total_num = float(total)
                    tax_num = float(tax)
                    
                    # Check if we have a service charge
                    service_charge_num = 0
                    if all_financial_data["service_charges"]:
                        service_charge_num = max(all_financial_data["service_charges"])
                        service_charge = str(service_charge_num)
                    
                    if subtotal:
                        subtotal_num = float(subtotal)
                        
                        # Calculate expected total
                        calculated_total = subtotal_num + tax_num + service_charge_num
                        diff = abs(calculated_total - total_num)
                        
                        # If they match (within 10%), we're good
                        if diff / total_num <= 0.10:
                            log_info(f"✅ Validation passed: ${subtotal} + ${tax} + ${service_charge_num} ≈ ${total}")
                        else:
                            log_warning(f"⚠️ Total validation failed: subtotal({subtotal}) + tax({tax}) + service({service_charge_num}) = {calculated_total} != total({total})")
                            
                            # Try to fix: calculate subtotal from total - tax - service_charge
                            corrected_subtotal = total_num - tax_num - service_charge_num
                            if corrected_subtotal > 0:
                                log_info(f"🔧 Auto-correcting subtotal: {subtotal} → {corrected_subtotal}")
                                subtotal = str(corrected_subtotal)
                    else:
                        # No subtotal found, calculate it
                        calculated_subtotal = total_num - tax_num - service_charge_num
                        if calculated_subtotal > 0:
                            subtotal = str(calculated_subtotal)
                            log_info(f"🔧 Calculated subtotal: ${subtotal}")
                        
                except (ValueError, ZeroDivisionError):
                    pass
            
            # Service charge if found
            if all_financial_data["service_charges"]:
                service_charge = str(max(all_financial_data["service_charges"]))
                log_info(f"✅ Found service charge: ${service_charge}")
            
            # Extract date with more patterns
            date = None
            
            def search_for_date(obj):
                """Recursively search for date fields."""
                if isinstance(obj, dict):
                    for date_key in ["date", "receipt_date", "invoice_date", "transaction_date", "Date", "Open Time"]:
                        if date_key in obj:
                            date_value = obj[date_key]
                            if validate_date(str(date_value)):
                                return str(date_value)
                    
                    # Recurse
                    for value in obj.values():
                        result = search_for_date(value)
                        if result:
                            return result
                
                elif isinstance(obj, list):
                    for item in obj:
                        result = search_for_date(item)
                        if result:
                            return result
                
                return None
            
            date = search_for_date(cord_json)
            
            # Extract bill_id
            bill_id = None
            for id_key in ["receipt_number", "invoice_no", "order_number", "transaction_id", "receipt_id", "Bill", "bill"]:
                if id_key in cord_json:
                    id_value = cord_json[id_key]
                    id_str = str(id_value).strip()
                    if id_str and not re.match(r'^\$?\d+\.\d{2}$', id_str):
                        bill_id = id_str
                        break
            
            result = {
                "vendor": vendor,
                "date": date,
                "total": total,
                "tax": tax,
                "subtotal": subtotal,
                "bill_id": bill_id,
                "currency": self._detect_currency(cord_json, total, tax, subtotal),
                "line_items": self._extract_line_items(cord_json),
            }
            
            log_info(f"✅ Normalized extraction: {result}")
            
            if not vendor:
                log_warning("⚠️ Could not extract vendor name from receipt")
            if not total:
                log_warning("⚠️ Could not extract total amount from receipt")
            
            return result
            
        except Exception as e:
            log_error(f"Error normalizing CORD output: {e}")
            return self._get_empty_extraction()
    
    def _extract_line_items(self, cord_json: Dict) -> list:
        """
        Extract individual line items (menu items) from the receipt.
        Returns list of dicts: [{"name": "Pork Pancakes", "quantity": 1, "unit_price": 17.00, "total_price": 17.00}, ...]
        """
        line_items = []
        
        if "menu" not in cord_json:
            log_info("⚠️ No 'menu' field in DONUT output")
            return line_items
        
        menu = cord_json["menu"]
        log_info(f"Menu type: {type(menu)}, is list: {isinstance(menu, list)}")
        
        # Handle menu as list
        if isinstance(menu, list):
            log_info(f"Processing {len(menu)} menu items")
            for i, item in enumerate(menu):
                if not isinstance(item, dict):
                    log_info(f"  Item {i}: Not a dict, skipping")
                    continue
                
                name = item.get("nm", "")
                if not name:
                    log_info(f"  Item {i}: No name, skipping")
                    continue
                
                # Skip items that look like headers (business names, addresses, etc.)
                skip_keywords = ['restaurant', 'cafe', 'ca ', 'phone', 'date:', 'table:', 'server:', 'bill:', 'receipt']
                if any(keyword in name.lower() for keyword in skip_keywords):
                    log_info(f"  Item {i}: '{name}' - Header, skipping")
                    continue
                
                # Extract quantity
                quantity = 1
                cnt = item.get("cnt")
                if cnt:
                    try:
                        quantity = int(cnt)
                    except (ValueError, TypeError):
                        quantity = 1
                
                # Extract price
                price = item.get("price")
                if not price:
                    log_info(f"  Item {i}: '{name}' - No price, skipping")
                    continue
                
                # Parse price
                cleaned_price = clean_price_string(price)
                if not cleaned_price:
                    log_info(f"  Item {i}: '{name}' - Price '{price}' couldn't be cleaned, skipping")
                    continue
                
                price_float = float(cleaned_price)
                
                # Skip if price looks wrong (too high = phone number, too low = quantity)
                if price_float < 0.10 or price_float > 500:
                    log_info(f"  Item {i}: '{name}' - Price ${price_float} out of range, skipping")
                    continue
                
                # Extract unit price if available
                unit_price = price_float
                unitprice = item.get("unitprice")
                if unitprice:
                    cleaned_unit = clean_price_string(unitprice)
                    if cleaned_unit:
                        unit_price = float(cleaned_unit)
                
                log_info(f"  Item {i}: '{name}' - ${price_float} - EXTRACTED")
                line_items.append({
                    "name": name.strip(),
                    "quantity": quantity,
                    "unit_price": unit_price if quantity > 1 else price_float,
                    "total_price": price_float,
                })
        
        # Handle menu as dict (single item)
        elif isinstance(menu, dict):
            name = menu.get("nm", "")
            price = menu.get("price")
            
            if name and price:
                cleaned_price = clean_price_string(price)
                if cleaned_price:
                    price_float = float(cleaned_price)
                    if 0.10 < price_float < 500:
                        line_items.append({
                            "name": name.strip(),
                            "quantity": 1,
                            "unit_price": price_float,
                            "total_price": price_float,
                        })
        
        log_info(f"✅ Extracted {len(line_items)} line items")
        return line_items
    
    def _detect_currency(self, cord_json: Dict, total: Optional[str], tax: Optional[str], subtotal: Optional[str]) -> str:
        """
        Detect currency from the receipt by checking for currency symbols in the raw values.
        Returns currency code (USD, INR, EUR, GBP, etc.)
        """
        currency_map = {
            '$': 'USD',
            '₹': 'INR',
            '€': 'EUR',
            '£': 'GBP',
            '¥': 'JPY',
            'USD': 'USD',
            'INR': 'INR',
            'EUR': 'EUR',
            'GBP': 'GBP',
            'JPY': 'JPY',
        }
        
        # Search the entire JSON structure for currency symbols
        def search_for_currency(obj):
            if isinstance(obj, str):
                for symbol, code in currency_map.items():
                    if symbol in obj:
                        return code
            elif isinstance(obj, dict):
                for value in obj.values():
                    result = search_for_currency(value)
                    if result:
                        return result
            elif isinstance(obj, list):
                for item in obj:
                    result = search_for_currency(item)
                    if result:
                        return result
            return None
        
        detected = search_for_currency(cord_json)
        if detected:
            log_info(f"✅ Detected currency: {detected}")
            return detected
        
        # Default to USD if no currency detected
        log_info("⚠️ No currency symbol found, defaulting to USD")
        return 'USD'
    
    def _get_empty_extraction(self) -> Dict[str, Any]:
        """Return empty extraction result when processing fails."""
        return {
            "vendor": None,
            "date": None,
            "total": None,
            "tax": None,
            "subtotal": None,
            "bill_id": None,
            "currency": "USD",
            "line_items": [],
        }


_processor: Optional[ReceiptProcessor] = None


def get_processor() -> ReceiptProcessor:
    global _processor
    if _processor is None:
        log_info("Initializing DONUT CORD-v2 processor (first request may be slow)...")
        _processor = ReceiptProcessor()
    return _processor


def extract_receipt_fields(image: Image.Image) -> Dict[str, Any]:
    try:
        processor = get_processor()
        return processor.extract_receipt_data(image)
    except Exception as e:
        raise DONUTError(f"Receipt extraction failed: {e}")
