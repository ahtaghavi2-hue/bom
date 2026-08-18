"""
موتور زمان‌بندی هوشمند BOM
شامل: PERT, CPM, Critical Path
"""
import math
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

class ScheduleNode:
    """گره زمان‌بندی برای هر قطعه"""
    def __init__(self, part_id: int, name: str, duration: float, predecessors: List[int]):
        self.part_id = part_id
        self.name = name
        self.duration = duration  # مدت زمان مورد انتظار (te)
        self.predecessors = predecessors
        self.early_start = 0.0
        self.early_finish = 0.0
        self.late_start = float('inf')
        self.late_finish = float('inf')
        self.slack = 0.0
        self.is_critical = False
        self.scheduled_start_date: Optional[datetime] = None
        self.scheduled_end_date: Optional[datetime] = None

class SchedulerEngine:
    def __init__(self, project_start_date: datetime):
        self.project_start_date = project_start_date
        self.nodes: Dict[int, ScheduleNode] = {}
        self.critical_path: List[int] = []
        self.project_duration = 0.0

    def calculate_pert_duration(self, optimistic: float, most_likely: float, pessimistic: float) -> Dict[str, float]:
        """
        محاسبه زمان مورد انتظار و انحراف معیار با روش PERT
        te = (to + 4tm + tp) / 6
        sigma = (tp - to) / 6
        """
        te = (optimistic + 4 * most_likely + pessimistic) / 6.0
        sigma = (pessimistic - optimistic) / 6.0
        variance = sigma ** 2
        return {
            'expected': te,
            'sigma': sigma,
            'variance': variance
        }

    def build_graph(self, parts: List[Any]) -> None:
        """ساخت گراف زمان‌بندی از روی درخت BOM"""
        # ایجاد گره‌ها
        for part in parts:
            # محاسبه زمان PERT اگر داده‌های سه‌نقطه‌ای موجود باشد
            if hasattr(part, 'time_optimistic') and part.time_optimistic and \
               hasattr(part, 'time_most_likely') and part.time_most_likely and \
               hasattr(part, 'time_pessimistic') and part.time_pessimistic:
                pert_data = self.calculate_pert_duration(
                    part.time_optimistic, part.time_most_likely, part.time_pessimistic
                )
                duration = pert_data['expected']
            else:
                duration = getattr(part, 'lead_time', 1.0) or 1.0
            
            # منطق BOM: فرزندان (Components) باید قبل از والد (Assembly) آماده باشند.
            # پس پیش‌نیازهای ساخت یک اسمبلی، تمام اجزای مستقیم آن هستند.
            children = [p for p in parts if getattr(p, 'parent_id', None) == part.id]
            predecessors = [c.id for c in children]

            self.nodes[part.id] = ScheduleNode(
                part_id=part.id,
                name=getattr(part, 'name', f'Part {part.id}'),
                duration=duration,
                predecessors=predecessors
            )

    def forward_pass(self) -> None:
        """محاسبه شروع و پایان زودهنگام (Early Start/Finish)"""
        # گره‌های بدون پیش‌نیاز (برگ‌های درخت - مواد خام) نقطه شروع هستند
        no_predecessors = [nid for nid, node in self.nodes.items() if not node.predecessors]
        
        if not no_predecessors and self.nodes:
            # حلقه وجود دارد یا همه چیز وابسته است، شروع از گره‌هایی که کمترین وابستگی را دارند
            no_predecessors = list(self.nodes.keys())[:1]

        # مقداردهی اولیه
        for nid in no_predecessors:
            self.nodes[nid].early_start = 0.0
            self.nodes[nid].early_finish = self.nodes[nid].duration

        # پیمایش توپولوژیک
        visited = set(no_predecessors)
        queue = list(no_predecessors)
        
        while queue:
            current_id = queue.pop(0)
            current_node = self.nodes[current_id]
            
            # پیدا کردن گره‌هایی که current_id پیش‌نیاز آنهاست
            for nid, node in self.nodes.items():
                if current_id in node.predecessors:
                    # بروزرسانی Early Start بر اساس Early Finish پیش‌نیاز
                    if current_node.early_finish > node.early_start:
                        node.early_start = current_node.early_finish
                    
                    # بررسی اینکه آیا همه پیش‌نیازها بازدید شده‌اند
                    if all(pred in visited for pred in node.predecessors):
                        node.early_finish = node.early_start + node.duration
                        if nid not in visited:
                            visited.add(nid)
                            queue.append(nid)

        # یافتن حداکثر زمان پروژه
        if self.nodes:
            self.project_duration = max(n.early_finish for n in self.nodes.values())

    def backward_pass(self) -> None:
        """محاسبه شروع و پایان دیرهنگام (Late Start/Finish) و شناوری"""
        if not self.nodes:
            return

        # گره‌های انتهایی (ریشه‌های درخت - محصول نهایی)
        last_nodes = []
        for nid, node in self.nodes.items():
            is_last = True
            for other_id, other_node in self.nodes.items():
                if nid in other_node.predecessors:
                    is_last = False
                    break
            if is_last:
                last_nodes.append(nid)
                self.nodes[nid].late_finish = self.project_duration
                self.nodes[nid].late_start = self.project_duration - node.duration

        # ساخت گراف معکوس برای پیمایش
        reverse_deps = {nid: [] for nid in self.nodes}
        for nid, node in self.nodes.items():
            for pred_id in node.predecessors:
                reverse_deps[pred_id].append(nid)
        
        queue = list(last_nodes)
        visited = set(last_nodes)
        
        while queue:
            current_id = queue.pop(0)
            current_node = self.nodes[current_id]
            
            # بروزرسانی پیش‌نیازها
            for pred_id in current_node.predecessors:
                pred_node = self.nodes[pred_id]
                # Late Finish پیش‌نیاز = حداقل Late Start جانشینان
                new_late_finish = min([self.nodes[succ].late_start for succ in reverse_deps[pred_id]])
                
                if new_late_finish < pred_node.late_finish:
                    pred_node.late_finish = new_late_finish
                    pred_node.late_start = pred_node.late_finish - pred_node.duration
                    
                    if pred_id not in visited:
                        visited.add(pred_id)
                        queue.append(pred_id)

    def identify_critical_path(self) -> List[int]:
        """شناسایی مسیر بحرانی"""
        self.critical_path = []
        for nid, node in self.nodes.items():
            slack = node.late_start - node.early_start
            node.slack = slack
            if abs(slack) < 0.001: # شناوری نزدیک به صفر
                node.is_critical = True
                self.critical_path.append(nid)
        return self.critical_path

    def convert_to_dates(self) -> None:
        """تبدیل زمان‌های شناور به تاریخ‌های واقعی (فرض واحد روز)"""
        for node in self.nodes.values():
            start_delta = timedelta(days=node.early_start)
            end_delta = timedelta(days=node.early_finish)
            
            node.scheduled_start_date = self.project_start_date + start_delta
            node.scheduled_end_date = self.project_start_date + end_delta

    def run_full_schedule(self, parts: List[Any]) -> Dict[str, Any]:
        """اجرای کامل مراحل زمان‌بندی"""
        self.build_graph(parts)
        self.forward_pass()
        self.backward_pass()
        self.identify_critical_path()
        self.convert_to_dates()
        
        results = {
            'project_duration_days': self.project_duration,
            'critical_path_parts': self.critical_path,
            'schedule': [
                {
                    'part_id': n.part_id,
                    'name': n.name,
                    'start_day': n.early_start,
                    'end_day': n.early_finish,
                    'slack': n.slack,
                    'is_critical': n.is_critical,
                    'start_date': n.scheduled_start_date.isoformat() if n.scheduled_start_date else None,
                    'end_date': n.scheduled_end_date.isoformat() if n.scheduled_end_date else None
                }
                for n in self.nodes.values()
            ]
        }
        return results

# تابع کمکی برای فراخوانی سریع
def generate_schedule(project_start: datetime, parts: List[Any]) -> Dict[str, Any]:
    engine = SchedulerEngine(project_start)
    return engine.run_full_schedule(parts)
