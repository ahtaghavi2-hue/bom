"""
محاسبه‌گر هزینه پروژه ساخت BOM
شامل: هزینه مستقیم، سربار، انبارداری و تحلیل ریسک
"""
from typing import List, Dict, Any
from datetime import timedelta

class CostCalculator:
    def __init__(self, schedule_results: Dict[str, Any], parts: List[Any]):
        self.schedule = schedule_results.get('schedule', [])
        self.project_duration = schedule_results.get('project_duration_days', 0)
        self.parts_map = {p.id: p for p in parts}
        
    def calculate_direct_costs(self) -> Dict[str, float]:
        """محاسبه هزینه‌های مستقیم (مواد، نیروی کار، سربار مستقیم)"""
        total_material = 0.0
        total_labor = 0.0
        total_overhead = 0.0
        
        for item in self.schedule:
            part_id = item['part_id']
            part = self.parts_map.get(part_id)
            
            if not part:
                continue
            
            # هزینه مواد
            material_cost = getattr(part, 'cost_material', 0) or 0
            total_material += material_cost
            
            # هزینه نیروی کار (زمان * نرخ ساعتی)
            labor_rate = getattr(part, 'labor_rate_per_hour', 0) or 0
            duration_hours = item['end_day'] - item['start_day']
            # فرض: هر روز 8 ساعت کاری
            labor_cost = duration_hours * 8 * labor_rate
            total_labor += labor_cost
            
            # سربار مستقیم
            overhead_cost = getattr(part, 'cost_overhead', 0) or 0
            total_overhead += overhead_cost
        
        return {
            'material': total_material,
            'labor': total_labor,
            'overhead': total_overhead,
            'total_direct': total_material + total_labor + total_overhead
        }
    
    def calculate_storage_costs(self, daily_storage_rate: float = 10.0) -> Dict[str, float]:
        """
        محاسبه هزینه انبارداری
        فرض: قطعات پس از ساخت تا زمان اسمبل نهایی در انبار می‌مانند
        """
        total_storage_cost = 0.0
        storage_details = []
        
        # پیدا کردن تاریخ پایان پروژه (آخرین اسمبل)
        project_end_day = max(item['end_day'] for item in self.schedule) if self.schedule else 0
        
        for item in self.schedule:
            part_id = item['part_id']
            part = self.parts_map.get(part_id)
            
            if not part:
                continue
            
            # مدت زمان انتظار در انبار = پایان پروژه - پایان ساخت این قطعه
            storage_days = project_end_day - item['end_day']
            
            # هزینه انبار = روزها * نرخ روزانه * ضریب حجم/ارزش (اختیاری)
            storage_value = getattr(part, 'cost_material', 0) or 0
            volume_factor = getattr(part, 'storage_volume_factor', 1.0) or 1.0
            
            item_storage_cost = storage_days * daily_storage_rate * volume_factor
            total_storage_cost += item_storage_cost
            
            storage_details.append({
                'part_id': part_id,
                'storage_days': storage_days,
                'cost': item_storage_cost
            })
        
        return {
            'total_storage': total_storage_cost,
            'details': storage_details
        }
    
    def calculate_risk_adjusted_cost(self, base_cost: float, risk_percentage: float = 10.0) -> float:
        """اعمال ضریب ریسک به هزینه کل"""
        return base_cost * (1 + risk_percentage / 100.0)
    
    def generate_cost_report(self, storage_rate: float = 10.0, risk_percentage: float = 10.0) -> Dict[str, Any]:
        """تولید گزارش کامل هزینه"""
        direct_costs = self.calculate_direct_costs()
        storage_costs = self.calculate_storage_costs(storage_rate)
        
        subtotal = direct_costs['total_direct'] + storage_costs['total_storage']
        risk_amount = subtotal * (risk_percentage / 100.0)
        total_estimated_cost = subtotal + risk_amount
        
        report = {
            'project_duration_days': self.project_duration,
            'direct_costs': direct_costs,
            'storage_costs': {
                'total': storage_costs['total_storage'],
                'daily_rate_used': storage_rate
            },
            'risk_analysis': {
                'percentage': risk_percentage,
                'amount': risk_amount
            },
            'summary': {
                'subtotal': subtotal,
                'risk_buffer': risk_amount,
                'total_estimated_cost': total_estimated_cost
            },
            'cost_breakdown_by_phase': self._calculate_phase_costs()
        }
        
        return report
    
    def _calculate_phase_costs(self) -> List[Dict[str, Any]]:
        """تفکیک هزینه بر اساس مراحل زمانی"""
        if not self.schedule:
            return []
        
        # گروه‌بندی هزینه‌ها بر اساس هفته‌های پروژه
        weekly_costs = {}
        project_weeks = int(self.project_duration / 7) + 1
        
        for week in range(project_weeks):
            weekly_costs[week] = {
                'week_number': week + 1,
                'start_day': week * 7,
                'end_day': (week + 1) * 7,
                'labor_cost': 0.0,
                'storage_cost': 0.0,
                'total': 0.0
            }
        
        # توزیع هزینه نیروی کار در طول زمان
        for item in self.schedule:
            part = self.parts_map.get(item['part_id'])
            if not part:
                continue
            
            labor_rate = getattr(part, 'labor_rate_per_hour', 0) or 0
            duration_days = item['end_day'] - item['start_day']
            daily_labor_cost = duration_days * 8 * labor_rate / max(duration_days, 1)
            
            # تخصیص به هفته‌ها
            start_week = int(item['start_day'] / 7)
            end_week = int(item['end_day'] / 7)
            
            for week in range(start_week, min(end_week + 1, project_weeks)):
                weekly_costs[week]['labor_cost'] += daily_labor_cost * min(7, duration_days)
        
        # محاسبه مجموع هر هفته
        for week_data in weekly_costs.values():
            week_data['total'] = week_data['labor_cost'] + week_data['storage_cost']
        
        return list(weekly_costs.values())

# تابع کمکی
def calculate_project_costs(schedule_results: Dict[str, Any], parts: List[Any], 
                           storage_rate: float = 10.0, risk_percentage: float = 10.0) -> Dict[str, Any]:
    calculator = CostCalculator(schedule_results, parts)
    return calculator.generate_cost_report(storage_rate, risk_percentage)
