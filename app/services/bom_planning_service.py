"""
ماژول اصلی خدمات زمان‌بندی و هزینه
یکپارچه‌سازی تمام موتورهای محاسباتی
"""
from datetime import datetime
from typing import List, Dict, Any

from .scheduler_engine import SchedulerEngine, generate_schedule
from .cost_calculator import CostCalculator, calculate_project_costs
from .monte_carlo import MonteCarloSimulator, run_monte_carlo_simulation

class BOMPlanningService:
    """سرویس اصلی برنامه‌ریزی پروژه BOM"""
    
    def __init__(self, project_start_date: datetime = None):
        if project_start_date is None:
            project_start_date = datetime.now()
        self.project_start_date = project_start_date
    
    def generate_full_plan(self, parts: List[Any], 
                          storage_rate: float = 10.0,
                          risk_percentage: float = 10.0,
                          run_monte_carlo: bool = True,
                          mc_iterations: int = 500) -> Dict[str, Any]:
        """
        تولید برنامه کامل پروژه شامل:
        - زمان‌بندی CPM/PERT
        - مسیر بحرانی
        - برآورد هزینه
        - تحلیل ریسک مونت‌کارلو
        """
        
        # 1. اجرای زمان‌بندی قطعی (CPM با زمان‌های PERT)
        schedule_results = generate_schedule(self.project_start_date, parts)
        
        # 2. محاسبه هزینه‌ها
        cost_report = calculate_project_costs(
            schedule_results, 
            parts, 
            storage_rate=storage_rate,
            risk_percentage=risk_percentage
        )
        
        # 3. شبیه‌سازی مونت‌کارلو (اختیاری - زمان‌بر است)
        monte_carlo_results = None
        if run_monte_carlo:
            try:
                monte_carlo_results = run_monte_carlo_simulation(
                    parts, 
                    self.project_start_date, 
                    iterations=mc_iterations
                )
            except Exception as e:
                monte_carlo_results = {
                    'error': str(e),
                    'status': 'failed'
                }
        
        # 4. ترکیب نتایج
        full_plan = {
            'project_info': {
                'start_date': self.project_start_date.isoformat(),
                'total_parts': len(parts),
                'generated_at': datetime.now().isoformat()
            },
            'schedule': schedule_results,
            'costs': cost_report,
            'risk_analysis': monte_carlo_results,
            'summary': {
                'project_duration_days': schedule_results['project_duration_days'],
                'critical_path_length': len(schedule_results['critical_path_parts']),
                'total_estimated_cost': cost_report['summary']['total_estimated_cost'],
                'recommended_completion_date_p90': None,
                'risk_level': None
            }
        }
        
        # افزودن توصیه‌ها بر اساس مونت‌کارلو
        if monte_carlo_results and 'statistics' in monte_carlo_results:
            from datetime import timedelta
            p90_duration = monte_carlo_results['percentiles']['P90']
            recommended_end = self.project_start_date + timedelta(days=p90_duration)
            
            full_plan['summary']['recommended_completion_date_p90'] = recommended_end.isoformat()
            full_plan['summary']['risk_level'] = monte_carlo_results.get('risk_assessment', {}).get('risk_level', 'UNKNOWN')
        
        return full_plan
    
    def compare_scenarios(self, parts: List[Any], scenarios: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        مقایسه چند سناریوی مختلف (مثلاً با منابع مختلف یا زمان‌های متفاوت)
        هر سناریو می‌تواند ضرایب مختلفی برای زمان یا هزینه داشته باشد
        """
        results = []
        
        for scenario in scenarios:
            name = scenario.get('name', 'Unnamed')
            time_factor = scenario.get('time_factor', 1.0)
            cost_factor = scenario.get('cost_factor', 1.0)
            
            # اعمال ضرایب روی قطعات (به صورت موقت)
            modified_parts = []
            for part in parts:
                modified_part = type('ModifiedPart', (), {})()
                
                # کپی ویژگی‌ها
                for attr in dir(part):
                    if not attr.startswith('_'):
                        try:
                            value = getattr(part, attr)
                            if not callable(value):
                                setattr(modified_part, attr, value)
                        except:
                            pass
                
                # اعمال ضریب زمان
                if hasattr(modified_part, 'time_optimistic') and modified_part.time_optimistic:
                    modified_part.time_optimistic *= time_factor
                    modified_part.time_most_likely *= time_factor
                    modified_part.time_pessimistic *= time_factor
                
                # اعمال ضریب هزینه
                if hasattr(modified_part, 'cost_material') and modified_part.cost_material:
                    modified_part.cost_material *= cost_factor
                
                modified_parts.append(modified_part)
            
            # اجرای برنامه‌ریزی برای این سناریو
            plan = self.generate_full_plan(
                modified_parts,
                run_monte_carlo=False  # برای سرعت بیشتر، مونت‌کارلو را غیرفعال می‌کنیم
            )
            
            results.append({
                'scenario_name': name,
                'duration': plan['summary']['project_duration_days'],
                'cost': plan['summary']['total_estimated_cost'],
                'critical_path_length': plan['summary']['critical_path_length']
            })
        
        # پیدا کردن بهترین سناریو
        best_by_time = min(results, key=lambda x: x['duration'])
        best_by_cost = min(results, key=lambda x: x['cost'])
        
        return {
            'scenarios': results,
            'recommendations': {
                'fastest': best_by_time,
                'cheapest': best_by_cost,
                'balanced': self._find_balanced_scenario(results)
            }
        }
    
    def _find_balanced_scenario(self, results: List[Dict]) -> Dict:
        """پیدا کردن سناریوی متعادل (امتیاز ترکیبی زمان و هزینه)"""
        if not results:
            return {}
        
        # نرمال‌سازی و امتیازدهی
        max_duration = max(r['duration'] for r in results)
        max_cost = max(r['cost'] for r in results)
        
        scored_results = []
        for r in results:
            normalized_duration = r['duration'] / max_duration if max_duration > 0 else 0
            normalized_cost = r['cost'] / max_cost if max_cost > 0 else 0
            combined_score = (normalized_duration + normalized_cost) / 2
            scored_results.append({**r, 'balance_score': combined_score})
        
        return min(scored_results, key=lambda x: x['balance_score'])

# تابع کمکی برای استفاده سریع
def plan_bom_project(parts: List[Any], 
                    start_date: datetime = None,
                    **kwargs) -> Dict[str, Any]:
    service = BOMPlanningService(start_date)
    return service.generate_full_plan(parts, **kwargs)
