import logging
from notifications.services import NotificationService
from analytics.models import ErrorEventLog

logger = logging.getLogger(__name__)

class EmergencyService:
    @staticmethod
    def handle_emergency(patient, triage_result):
        if triage_result.get('urgency') in ['HIGH', 'CRITICAL'] or triage_result.get('emergency_risk'):
            try:
                # 1. Websocket Alert to Admins/Emergency Staff
                from accounts.models import CustomUser
                staff_users = CustomUser.objects.filter(is_staff=True)[:5]
                for staff in staff_users:
                    NotificationService.send_notification(
                        user=staff,
                        n_type="EMERGENCY_TRIAGE_ALERT",
                        title=f"Critical Triage Alert: {patient.get_full_name() or patient.username}",
                        message=f"Patient {patient.username} triaged as {triage_result.get('urgency')}. Department: {triage_result.get('department')}.",
                        priority="high",
                        link=f"/admin/accounts/customuser/{patient.id}/change/"
                    )
                
                # 2. Enterprise Audit Log
                ErrorEventLog.objects.create(
                    source="AI_EMERGENCY_DETECT",
                    error_type="CRITICAL_TRIAGE",
                    error_message=f"Patient {patient.username} triaged as {triage_result.get('urgency')}. Rec: {triage_result.get('recommendation')}",
                    stack_trace=None
                )
            except Exception as e:
                logger.error(f"Failed to handle emergency escalation: {e}")
