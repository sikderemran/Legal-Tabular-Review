
import re
from typing import Any, Dict, List, Optional
from datetime import datetime
from decimal import Decimal
import dateparser

class FieldNormalizer:
    
    @staticmethod
    def normalize(value: Any, data_type: str) -> Any:
        if value is None:
            return None
        
        try:
            if data_type == 'date':
                return FieldNormalizer.normalize_date(value)
            elif data_type == 'number':
                return FieldNormalizer.normalize_number(value)
            elif data_type == 'currency':
                return FieldNormalizer.normalize_currency(value)
            elif data_type == 'boolean':
                return FieldNormalizer.normalize_boolean(value)
            elif data_type == 'percentage':
                return FieldNormalizer.normalize_percentage(value)
            elif data_type == 'duration':
                return FieldNormalizer.normalize_duration(value)
            else:
                return FieldNormalizer.normalize_text(value)
        except Exception:
            return value 
    
    @staticmethod
    def normalize_date(date_str: str) -> Optional[str]:
        """Normalize date string to ISO format"""
        if not date_str or not isinstance(date_str, str):
            return date_str
        date_str = re.sub(r'(?i)^(?:date|effective|as of|from)\s*[:]?\s*', '', date_str).strip()
        formats = [
            '%B %d, %Y',
            '%b %d, %Y', 
            '%d %B %Y',
            '%d %b %Y', 
            '%m/%d/%Y', 
            '%d/%m/%Y', 
            '%Y-%m-%d', 
        ]
        
        for fmt in formats:
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.isoformat()
            except ValueError:
                continue
        
        parsed = dateparser.parse(date_str)
        if parsed:
            return parsed.isoformat()
        
        return date_str
    
    @staticmethod
    def normalize_number(value: Any) -> Optional[float]:
        if isinstance(value, (int, float)):
            return float(value)
        
        if not isinstance(value, str):
            return None
        
        cleaned = re.sub(r'[^\d.-]', '', value)
        
        try:
            return float(cleaned)
        except ValueError:
            return None
    
    @staticmethod
    def normalize_currency(value: Any) -> Dict[str, Any]:
        if isinstance(value, dict):
            return value
        
        if not isinstance(value, str):
            return {'raw': value}
        match = re.search(r'(\$|€|£|¥|USD|EUR|GBP|JPY)?\s*([\d,]+(?:\.\d{2})?)', value.upper())
        
        if match:
            currency = match.group(1) or '$'
            amount_str = match.group(2).replace(',', '')
        
            currency_map = {
                'USD': '$', 'EUR': '€', 'GBP': '£', 'JPY': '¥',
                '$': '$', '€': '€', '£': '£', '¥': '¥'
            }
            
            currency_symbol = currency_map.get(currency.upper(), '$')
            
            try:
                amount = float(amount_str)
                return {
                    'currency': currency_symbol,
                    'amount': amount,
                    'formatted': f"{currency_symbol}{amount:,.2f}"
                }
            except ValueError:
                pass
        
        return {'raw': value}
    
    @staticmethod
    def normalize_boolean(value: Any) -> bool:
        if isinstance(value, bool):
            return value
        
        if isinstance(value, str):
            true_patterns = [
                r'(?i)^yes$', r'(?i)^true$', r'(?i)^required$',
                r'(?i)^obligatory$', r'(?i)^mandatory$'
            ]
            
            false_patterns = [
                r'(?i)^no$', r'(?i)^false$', r'(?i)^not required$',
                r'(?i)^optional$'
            ]
            
            for pattern in true_patterns:
                if re.match(pattern, value):
                    return True
            
            for pattern in false_patterns:
                if re.match(pattern, value):
                    return False
        return False
    
    @staticmethod
    def normalize_percentage(value: Any) -> Optional[float]:
        if isinstance(value, (int, float)):
            return float(value) / 100
        
        if not isinstance(value, str):
            return None
    
        match = re.search(r'(\d+(?:\.\d+)?)\s*%', value)
        
        if match:
            try:
                return float(match.group(1)) / 100
            except ValueError:
                pass
        
        return None
    
    @staticmethod
    def normalize_duration(value: Any) -> Dict[str, Any]:
        if isinstance(value, dict) and 'value' in value and 'unit' in value:
            return value
        
        if not isinstance(value, str):
            return {'raw': value}
        
        match = re.search(r'(\d+)\s+(day|month|year)s?', value.lower())
        
        if match:
            return {
                'value': int(match.group(1)),
                'unit': match.group(2),
                'display': f"{match.group(1)} {match.group(2)}s"
            }
        
        return {'raw': value}
    
    @staticmethod
    def normalize_text(value: Any) -> str:
        if value is None:
            return ''
        
        if not isinstance(value, str):
            return str(value)
        text = value.strip()
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
        
        return text
    
    @staticmethod
    def normalize_parties(parties_list: List[str]) -> List[Dict[str, str]]:
        normalized = []
        
        for party in parties_list:
            if not party:
                continue
            entity_type = 'individual'
            corporate_indicators = ['LLC', 'INC', 'CORP', 'LTD', 'CO', 'COMPANY', 'PARTNERSHIP']
            
            for indicator in corporate_indicators:
                if indicator in party.upper():
                    entity_type = 'organization'
                    break
            
            normalized.append({
                'name': party.strip(),
                'type': entity_type,
                'normalized_name': party.upper().strip()
            })
        
        return normalized