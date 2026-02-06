import re
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from decimal import Decimal
import dateparser

from app.models.schemas import ExtractionField, ExtractedValue, Citation
from app.core.config import settings

logger = logging.getLogger(__name__)

class FieldExtractor:
    
    def __init__(self):
        self.patterns = self._initialize_patterns()
        
    def _initialize_patterns(self) -> Dict[str, List[Tuple[str, str]]]:
        return {
            'effective_date': [
                (r'(?i)effective\s+(?:as\s+of|from)?\s*(\d{1,2}\s+\w+\s+\d{4})', 'Full date'),
                (r'(?i)effective\s+(?:as\s+of|from)?\s*(\d{1,2}/\d{1,2}/\d{4})', 'Slash date'),
                (r'(?i)date.*:\s*(\d{1,2}\s+\w+\s+\d{4})', 'Date after colon'),
                (r'(?i)dated.*?(\d{1,2}\s+\w+\s+\d{4})', 'Dated pattern'),
                (r'(?i)executed.*?(\d{1,2}\s+\w+\s+\d{4})', 'Executed pattern')
            ],
            'parties': [
                (r'(?i)between\s+(.+?)\s+and\s+(.+)', 'Between pattern'),
                (r'(?i)party\s+(?:a|1)[:\s]+(.+?)[\r\n]+party\s+(?:b|2)[:\s]+(.+)', 'Party A/B'),
                (r'(?i)this\s+agreement.*?by\s+and\s+between\s+(.+?)\s+and\s+(.+)', 'By and between'),
                (r'(?i)made\s+between\s+(.+?)\s+and\s+(.+)', 'Made between')
            ],
            'termination': [
                (r'(?i)terminat(?:e|ion).*?(\d+)\s+(day|month|year)s?', 'Termination period'),
                (r'(?i)term.*?(\d+)\s+(month|year)s?', 'Term period'),
                (r'(?i)expir(?:e|ation).*?(\d{1,2}/\d{1,2}/\d{4})', 'Expiration date'),
                (r'(?i)continue.*?for\s+(\d+)\s+(month|year)s?', 'Continue for period')
            ],
            'jurisdiction': [
                (r'(?i)jurisdiction.*?state\s+of\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', 'State jurisdiction'),
                (r'(?i)governed\s+by.*?laws\s+of\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', 'Governing law state'),
                (r'(?i)venue.*?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:county|district))', 'Venue location')
            ],
            'payment_terms': [
                (r'(?i)payment.*?(\$\d+(?:,\d+)*(?:\.\d{2})?)', 'Payment amount'),
                (r'(?i)amount.*?(\$\d+(?:,\d+)*(?:\.\d{2})?)', 'Amount'),
                (r'(?i)price.*?(\$\d+(?:,\d+)*(?:\.\d{2})?)', 'Price'),
                (r'(?i)sum.*?of\s*(\$\d+(?:,\d+)*(?:\.\d{2})?)', 'Sum of amount')
            ],
            'governing_law': [
                (r'(?i)govern(?:ing|ed).*?law.*?state\s+of\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', 'Governing law'),
                (r'(?i)laws\s+of\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', 'Laws of state'),
                (r'(?i)construed.*?accordance.*?laws.*?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', 'Construed accordance')
            ],
            'confidentiality': [
                (r'(?i)confidential.*?obligation', 'Confidential obligation'),
                (r'(?i)non.?disclosure', 'Non-disclosure'),
                (r'(?i)proprietary\s+information', 'Proprietary information')
            ],
            'indemnification': [
                (r'(?i)indemnif', 'Indemnification'),
                (r'(?i)hold\s+harmless', 'Hold harmless'),
                (r'(?i)defend.*?indemnif', 'Defend and indemnify')
            ],
            'warranties': [
                (r'(?i)warrant(?:y|ies)', 'Warranties'),
                (r'(?i)represent.*?warrant', 'Represent and warrant'),
                (r'(?i)as\s+is', 'As is')
            ],
            'liability': [
                (r'(?i)limitation.*?liability', 'Limitation of liability'),
                (r'(?i)consequential\s+damages', 'Consequential damages'),
                (r'(?i)exclu.*?liability', 'Exclusion of liability')
            ]
        }
    
    def extract_fields(self, text: str, fields: List[ExtractionField]) -> Dict[str, ExtractedValue]:
        results = {}
        
        for field in fields:
            field_name = field.field_name
            
            try:
                if field_name in self.patterns:
                    extracted_value = self._extract_with_patterns(text, field_name, field.data_type)
                else:
                    extracted_value = self._extract_generic(text, field)
                
                if extracted_value and extracted_value.confidence >= settings.MIN_CONFIDENCE:
                    results[field_name] = extracted_value
                    
            except Exception as e:
                logger.error(f"Error extracting field {field_name}: {str(e)}")
                continue
        
        return results
    
    def _extract_with_patterns(self, text: str, field_name: str, data_type: str) -> Optional[ExtractedValue]:
        patterns = self.patterns.get(field_name, [])
        best_match = None
        best_confidence = 0.0
        best_citation = None
        
        for pattern, description in patterns:
            try:
                matches = list(re.finditer(pattern, text, re.IGNORECASE | re.DOTALL))
                
                for match in matches:
                    confidence = self._calculate_match_confidence(match, field_name)
                    
                    if confidence > best_confidence:
                        best_confidence = confidence
                        best_match = match
                        best_citation = description
                        
            except re.error as e:
                logger.warning(f"Invalid regex pattern for {field_name}: {pattern} - {str(e)}")
                continue
        
        if best_match:
            value = self._extract_value_from_match(best_match, field_name, data_type)
            
            citations = []
            if best_citation:
                citations.append(Citation(
                    text=best_match.group(),
                    page=None, 
                    line_start=None,
                    line_end=None
                ))
            
            normalized_value = self._normalize_value(value, data_type)
            
            return ExtractedValue(
                value=value,
                normalized_value=normalized_value,
                confidence=best_confidence,
                citations=citations,
                raw_text=best_match.group()
            )
        
        return None
    
    def _extract_generic(self, text: str, field: ExtractionField) -> Optional[ExtractedValue]:
        field_name_variations = [
            field.field_name,
            field.display_name,
            field.field_name.replace('_', ' '),
            field.field_name.title()
        ]
        
        best_match = None
        best_confidence = 0.0
        
        for variation in field_name_variations:
            pattern = rf'(?i){re.escape(variation)}[:\-\s]+(.+?)(?:\n|\.|$)'
            
            try:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    confidence = 0.6 + (len(match.group(1)) / 100) 
                    
                    if confidence > best_confidence:
                        best_confidence = confidence
                        best_match = match
                        
            except re.error:
                continue
        
        if best_match:
            value = best_match.group(1).strip()
            normalized_value = self._normalize_value(value, field.data_type)
            
            return ExtractedValue(
                value=value,
                normalized_value=normalized_value,
                confidence=min(best_confidence, 0.9),
                citations=[Citation(text=best_match.group())],
                raw_text=best_match.group()
            )
        
        return None
    
    def _calculate_match_confidence(self, match: re.Match, field_name: str) -> float:
        base_confidence = 0.7

        match_length = len(match.group())
        if match_length > 30:
            base_confidence += 0.1
        elif match_length > 10:
            base_confidence += 0.05
        
        if match.groups():
            base_confidence += 0.1
        
        if field_name in ['effective_date', 'parties']:
            base_confidence += 0.05 

        return min(base_confidence, 0.95)
    
    def _extract_value_from_match(self, match: re.Match, field_name: str, data_type: str) -> Any:
        """Extract and format value from regex match"""
        if field_name == 'parties':
            groups = match.groups()
            if len(groups) >= 2:
                return [groups[0].strip(), groups[1].strip()]
            else:
                return match.group()
        
        elif field_name == 'termination':
            groups = match.groups()
            if len(groups) >= 2:
                return f"{groups[0]} {groups[1]}s"
            elif groups:
                return groups[0]
            else:
                return match.group()
        
        else:
            return match.group(1) if match.groups() else match.group()
    
    def _normalize_value(self, value: Any, data_type: str) -> Any:
        try:
            if data_type == 'date':
                parsed_date = dateparser.parse(str(value))
                if parsed_date:
                    return parsed_date.isoformat()
            
            elif data_type == 'number':
                cleaned = str(value).replace(',', '').replace('$', '').replace('%', '')
                if cleaned.replace('.', '').isdigit():
                    return float(cleaned)
            
            elif data_type == 'currency':
                match = re.search(r'(\$|€|£|¥)?\s*([\d,]+(?:\.\d{2})?)', str(value))
                if match:
                    currency = match.group(1) or '$'
                    amount = match.group(2).replace(',', '')
                    return {
                        'currency': currency,
                        'amount': float(amount),
                        'formatted': f"{currency}{amount}"
                    }
            
            elif data_type == 'percentage':
                match = re.search(r'(\d+(?:\.\d+)?)\s*%', str(value))
                if match:
                    return float(match.group(1)) / 100
            
        except Exception as e:
            logger.debug(f"Error normalizing value {value} as {data_type}: {str(e)}")
        
        return value  
    
    def extract_all_fields(self, text: str) -> Dict[str, ExtractedValue]:

        all_fields = [
            ExtractionField(
                field_name=field_name,
                display_name=field_name.replace('_', ' ').title(),
                data_type=self._infer_data_type(field_name)
            )
            for field_name in self.patterns.keys()
        ]
        
        return self.extract_fields(text, all_fields)
    
    def _infer_data_type(self, field_name: str) -> str:
        date_fields = ['effective_date', 'termination', 'expiration']
        number_fields = ['payment_terms', 'amount', 'price']
        boolean_fields = ['confidentiality', 'indemnification', 'warranties', 'liability']
        
        if field_name in date_fields:
            return 'date'
        elif field_name in number_fields:
            return 'number'
        elif field_name in boolean_fields:
            return 'boolean'
        else:
            return 'text'