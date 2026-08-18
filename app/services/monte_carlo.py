"""
شبیه‌سازی مونت‌کارلو برای تحلیل ریسک زمان‌بندی پروژه
تخمین احتمال تکمیل پروژه در تاریخ‌های مختلف
"""
import random
import math
from typing import List, Dict, Any, Tuple
from datetime import datetime, timedelta
from .scheduler_engine import SchedulerEngine, ScheduleNode

class MonteCarloSimulator:
    def __init__(self, parts: List[Any], project_start_date: datetime, iterations: int = 1000):
        self.parts = parts
        self.project_start_date = project_start_date
        self.iterations = iterations
        self.results: List[float] = []  # مدت زمان پروژه در هر تکرار
        
    def _sample_pert_duration(self, optimistic: float, most_likely: float, pessimistic: float) -> float:
        """
        نمونه‌برداری از توزیع بتا برای زمان PERT
        استفاده از تقریب نرمال برای سادگی
        """
        te = (optimistic + 4 * most_likely + pessimistic) / 6.0
        sigma = (pessimistic - optimistic) / 6.0
        
        # نمونه‌برداری از توزیع نرمال با میانگین te و انحراف معیار sigma
        sampled_value = random.gauss(te, sigma)
        
        # اطمینان از مثبت بودن زمان
        return max(0.1, sampled_value)
    
    def _create_sampled_parts(self) -> List[Any]:
        """ایجاد نسخه نمونه‌برداری شده از قطعات با زمان‌های تصادفی"""
        sampled_parts = []
        
        for part in self.parts:
            # کپی کردن ویژگی‌های part
            sampled_part = type('SampledPart', (), {})()
            
            # کپی تمام ویژگی‌ها
            for attr in dir(part):
                if not attr.startswith('_'):
                    try:
                        value = getattr(part, attr)
                        if not callable(value):
                            setattr(sampled_part, attr, value)
                    except:
                        pass
            
            # جایگزینی زمان با نمونه تصادفی اگر داده‌های PERT موجود باشد
            if hasattr(part, 'time_optimistic') and part.time_optimistic and \
               hasattr(part, 'time_most_likely') and part.time_most_likely and \
               hasattr(part, 'time_pessimistic') and part.time_pessimistic:
                
                sampled_duration = self._sample_pert_duration(
                    part.time_optimistic,
                    part.time_most_likely,
                    part.time_pessimistic
                )
                setattr(sampled_part, 'lead_time', sampled_duration)
            
            sampled_parts.append(sampled_part)
        
        return sampled_parts
    
    def run_simulation(self) -> Dict[str, Any]:
        """اجرای شبیه‌سازی مونت‌کارلو"""
        self.results = []
        
        for i in range(self.iterations):
            # ایجاد نمونه تصادفی از قطعات
            sampled_parts = self._create_sampled_parts()
            
            # اجرای زمان‌بندی برای این نمونه
            engine = SchedulerEngine(self.project_start_date)
            engine.build_graph(sampled_parts)
            engine.forward_pass()
            
            # ذخیره مدت زمان پروژه
            self.results.append(engine.project_duration)
        
        # تحلیل نتایج
        return self._analyze_results()
    
    def _analyze_results(self) -> Dict[str, Any]:
        """تحلیل آماری نتایج شبیه‌سازی"""
        if not self.results:
            return {}
        
        sorted_results = sorted(self.results)
        n = len(sorted_results)
        
        # آماره‌های پایه
        mean_duration = sum(self.results) / n
        variance = sum((x - mean_duration) ** 2 for x in self.results) / n
        std_deviation = math.sqrt(variance)
        min_duration = sorted_results[0]
        max_duration = sorted_results[-1]
        
        # صدک‌ها
        percentile_50 = sorted_results[int(n * 0.50)]
        percentile_80 = sorted_results[int(n * 0.80)]
        percentile_90 = sorted_results[int(n * 0.90)]
        percentile_95 = sorted_results[int(n * 0.95)]
        
        # احتمال تکمیل در بازه‌های مختلف
        probability_distribution = []
        step = (max_duration - min_duration) / 20
        for i in range(21):
            threshold = min_duration + i * step
            count = sum(1 for r in self.results if r <= threshold)
            prob = count / n * 100
            probability_distribution.append({
                'duration': round(threshold, 2),
                'probability_percent': round(prob, 2)
            })
        
        # شناسایی بازه اطمینان
        confidence_intervals = {
            '90%': (sorted_results[int(n * 0.05)], sorted_results[int(n * 0.95)]),
            '80%': (sorted_results[int(n * 0.10)], sorted_results[int(n * 0.90)]),
            '50%': (sorted_results[int(n * 0.25)], sorted_results[int(n * 0.75)])
        }
        
        return {
            'iterations': n,
            'statistics': {
                'mean': round(mean_duration, 2),
                'std_deviation': round(std_deviation, 2),
                'min': round(min_duration, 2),
                'max': round(max_duration, 2),
                'median': round(percentile_50, 2)
            },
            'percentiles': {
                'P50': round(percentile_50, 2),
                'P80': round(percentile_80, 2),
                'P90': round(percentile_90, 2),
                'P95': round(percentile_95, 2)
            },
            'confidence_intervals': {
                k: (round(v[0], 2), round(v[1], 2)) for k, v in confidence_intervals.items()
            },
            'probability_distribution': probability_distribution,
            'risk_assessment': self._assess_risk(mean_duration, std_deviation, percentile_90)
        }
    
    def _assess_risk(self, mean: float, std_dev: float, p90: float) -> Dict[str, Any]:
        """ارزیابی ریسک پروژه بر اساس نتایج"""
        # ضریب تغییرات (CV)
        cv = (std_dev / mean) * 100 if mean > 0 else 0
        
        # سطح ریسک
        if cv < 10:
            risk_level = "LOW"
            risk_description = "عدم قطعیت کم، زمان‌بندی قابل اعتماد است"
        elif cv < 20:
            risk_level = "MEDIUM"
            risk_description = "عدم قطعیت متوسط، نیاز به مانیتورینگ دارد"
        else:
            risk_level = "HIGH"
            risk_description = "عدم قطعیت بالا، ریسک تأخیر زیاد است"
        
        # احتمال تأخیر نسبت به زمان مورد انتظار (CPM قطعی)
        # فرض: کاربر یک زمان پایه دارد، اینجا ما P90 را مبنا قرار می‌دهیم
        buffer_needed = p90 - mean
        
        return {
            'risk_level': risk_level,
            'risk_description': risk_description,
            'coefficient_of_variation': round(cv, 2),
            'recommended_buffer_days': round(max(0, buffer_needed), 2),
            'probability_of_delay_beyond_mean': round(50, 2)  # حدود 50% برای توزیع متقارن
        }

# تابع کمکی
def run_monte_carlo_simulation(parts: List[Any], project_start: datetime, 
                               iterations: int = 1000) -> Dict[str, Any]:
    simulator = MonteCarloSimulator(parts, project_start, iterations)
    return simulator.run_simulation()
