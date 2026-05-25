"""
Normalization Strategies for specific source types.

Each source type (SAP, Utility, Travel) has a strategy class that knows
how to extract standard fields (activity_value, category, dates, metadata)
from the verbatim raw_data dict.

This isolates messy source-specific logic from the core CO2e math.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple
from decimal import Decimal
from datetime import datetime
import re

class NormalizationStrategy(ABC):
    @abstractmethod
    def extract_fields(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract canonical fields from raw data.
        Returns a dict containing at minimum:
        - category (str)
        - subcategory (str, optional)
        - activity_value (Decimal)
        - activity_unit (str)
        - period_start (date, optional)
        - period_end (date, optional)
        - metadata (dict)
        """
        pass

class SAPStrategy(NormalizationStrategy):
    def extract_fields(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        # raw_data already has mapped columns from SAPIngestionService
        try:
            value = Decimal(str(raw_data.get('quantity', '0')).replace(',', ''))
        except (ValueError, TypeError, Exception):
            raise ValueError(f"Invalid quantity: {raw_data.get('quantity')}")
            
        # Parse messy dates
        date_str = raw_data.get('date', '')
        parsed_date = None
        if date_str:
            # Handle 2024.01.15, 15/01/2024, 2024-01-15, Jan 15 2024
            date_str = date_str.strip().replace('.', '-')
            if '/' in date_str:
                parts = date_str.split('/')
                if len(parts) == 3:
                    # Assume DD/MM/YYYY
                    date_str = f"{parts[2]}-{parts[1]}-{parts[0]}"
            try:
                # Basic ISO parsing works for 2024-01-15
                from dateutil import parser
                parsed_date = parser.parse(date_str).date()
            except Exception:
                pass
                
        # Determine category from material_code
        mat_code = raw_data.get('material_code', '').upper()
        if mat_code == 'DIESEL-A':
            category, subcategory = 'Fuel Combustion - Diesel', 'Road Diesel'
        elif mat_code == 'PETROL-B':
            category, subcategory = 'Fuel Combustion - Petrol', 'Unleaded'
        elif mat_code == 'NATGAS':
            category, subcategory = 'Fuel Combustion - Natural Gas', 'Combustion'
        elif mat_code == 'LPG':
            category, subcategory = 'Fuel Combustion - LPG', 'Combustion'
        else:
            category, subcategory = f'Unknown Fuel - {mat_code}', ''

        return {
            'category': category,
            'subcategory': subcategory,
            'activity_value': value,
            'activity_unit': raw_data.get('unit', '').lower(),
            'period_start': parsed_date,
            'period_end': parsed_date,
            'metadata': {
                'plant_code': raw_data.get('plant_code'),
                'cost_center': raw_data.get('cost_center'),
                'amount': raw_data.get('amount'),
            }
        }

class UtilityStrategy(NormalizationStrategy):
    def extract_fields(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            value = Decimal(str(raw_data.get('Energy_Consumed', '0')))
        except Exception:
            raise ValueError(f"Invalid energy consumed: {raw_data.get('Energy_Consumed')}")

        from dateutil import parser
        try:
            p_start = parser.parse(raw_data.get('Billing_Period_Start')).date()
            p_end = parser.parse(raw_data.get('Billing_Period_End')).date()
        except Exception:
            p_start, p_end = None, None

        return {
            'category': 'Electricity - UK Grid',
            'subcategory': 'Generation',
            'activity_value': value,
            'activity_unit': raw_data.get('Unit', '').lower(),
            'period_start': p_start,
            'period_end': p_end,
            'metadata': {
                'meter_id': raw_data.get('Meter_ID'),
                'tariff_code': raw_data.get('Tariff_Code'),
                'renewable_percentage': raw_data.get('Renewable_Percentage')
            }
        }

class TravelStrategy(NormalizationStrategy):
    def extract_fields(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        t_type = raw_data.get('travel_type')
        from dateutil import parser
        
        try:
            p_date = parser.parse(raw_data.get('trip_date')).date()
        except Exception:
            p_date = None

        if t_type == 'flight':
            dist = Decimal(str(raw_data.get('distance_km') or '0'))
            # Fallback distance logic if missing
            if dist == 0 and raw_data.get('origin') and raw_data.get('destination'):
                # In real app: call geolocation service. Here: hardcode estimate
                dist = Decimal('1000.0') 
                
            if dist < 3000:
                cat = 'Flight - Short Haul (<3000km)'
            else:
                cat = 'Flight - Long Haul (>3700km)'
            
            subcat = 'Business Class' if raw_data.get('cabin_class') == 'business' else 'Economy Class'
            
            return {
                'category': cat,
                'subcategory': subcat,
                'activity_value': dist,
                'activity_unit': 'passenger-km',
                'period_start': p_date,
                'period_end': p_date,
                'metadata': {
                    'origin': raw_data.get('origin'),
                    'destination': raw_data.get('destination'),
                    'cabin_class': raw_data.get('cabin_class')
                }
            }
        elif t_type == 'hotel':
            try:
                nights = Decimal(str(raw_data.get('nights', '1')))
            except Exception:
                nights = Decimal('1')
                
            return {
                'category': 'Hotel Stay',
                'subcategory': 'Average Hotel',
                'activity_value': nights,
                'activity_unit': 'night',
                'period_start': p_date,
                'period_end': None,
                'metadata': {
                    'location': raw_data.get('location'),
                    'hotel_name': raw_data.get('hotel_name')
                }
            }
        elif t_type == 'ground_transport':
            try:
                dist = Decimal(str(raw_data.get('distance_km', '0')))
            except Exception:
                dist = Decimal('0')
                
            mode = raw_data.get('transport_mode', '')
            if mode == 'taxi':
                cat, subcat = 'Ground Transport - Taxi', 'Petrol/Diesel Taxi'
            elif mode == 'train':
                cat, subcat = 'Ground Transport - Train', 'National Rail'
            elif mode == 'rental_car':
                cat, subcat = 'Ground Transport - Rental Car', 'Medium Diesel'
            else:
                cat, subcat = 'Ground Transport - Other', mode
                
            return {
                'category': cat,
                'subcategory': subcat,
                'activity_value': dist,
                'activity_unit': 'km',
                'period_start': p_date,
                'period_end': p_date,
                'metadata': {
                    'transport_mode': mode
                }
            }
        else:
            raise ValueError(f"Unknown travel type: {t_type}")
