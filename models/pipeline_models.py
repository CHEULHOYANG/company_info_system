"""
영업 파이프라인 관리 모델
"""
from datetime import datetime, date, timedelta

class ManagedCompany:
    """관심 기업 관리 테이블 모델"""
    
    # 상태 옵션
    STATUS_OPTIONS = [
        ('prospect', '잠재고객'),
        ('contacted', '접촉중'),
        ('proposal', '제안단계'),
        ('negotiation', '협상중'),
        ('contract', '계약완료'),
        ('hold', '보류')
    ]
    
    # 상태별 알림 주기 (일수)
    ALERT_PERIODS = {
        'prospect': 14,      # 잠재고객: 2주
        'contacted': 7,      # 접촉중: 1주
        'proposal': 3,       # 제안단계: 3일
        'negotiation': 2,    # 협상중: 2일
        'contract': 30,      # 계약완료: 1개월
        'hold': 30          # 보류: 1개월
    }
    
    @staticmethod
    def get_status_badge_color(status):
        """상태별 뱃지 색상 반환"""
        colors = {
            'prospect': 'bg-gray-100 text-gray-800',
            'contacted': 'bg-blue-100 text-blue-800',
            'proposal': 'bg-yellow-100 text-yellow-800',
            'negotiation': 'bg-orange-100 text-orange-800',
            'contract': 'bg-green-100 text-green-800',
            'hold': 'bg-red-100 text-red-800'
        }
        return colors.get(status, 'bg-gray-100 text-gray-800')
    
    @staticmethod
    def calculate_d_day(target_date):
        """D-Day 계산"""
        if not target_date:
            return None
        
        if isinstance(target_date, str):
            target_date = datetime.strptime(target_date, '%Y-%m-%d').date()
        
        today = date.today()
        diff = (target_date - today).days
        
        if diff == 0:
            return "D-Day"
        elif diff > 0:
            return f"D-{diff}"
        else:
            return f"D+{abs(diff)}"
    
    @staticmethod
    def check_urgent_alert(last_contact_date, status):
        """긴급 알림 체크"""
        if not last_contact_date:
            return True
        
        if isinstance(last_contact_date, str):
            last_contact_date = datetime.strptime(last_contact_date, '%Y-%m-%d').date()
        
        alert_period = ManagedCompany.ALERT_PERIODS.get(status, 14)
        threshold_date = date.today() - timedelta(days=alert_period)
        
        return last_contact_date < threshold_date


class ContactHistory:
    """접촉 이력 테이블 모델"""
    
    # 접촉 유형
    CONTACT_TYPES = [
        ('phone', '전화'),
        ('visit', '방문'),
        ('email', '이메일'),
        ('message', '문자'),
        ('gift', '선물지급'),
        ('consulting', '컨설팅'),
        ('meeting', '미팅'),
        ('proposal', '제안서 제출'),
        ('contract', '계약 체결')
    ]
    
    @staticmethod
    def get_contact_type_icon(contact_type):
        """접촉 유형별 아이콘 반환"""
        icons = {
            'phone': '?',
            'visit': '?',
            'email': '?',
            'message': '?',
            'gift': '?',
            'consulting': '?',
            'meeting': '?',
            'proposal': '?',
            'contract': '?'
        }
        return icons.get(contact_type, '?')