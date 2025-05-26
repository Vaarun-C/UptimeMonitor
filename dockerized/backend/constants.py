from database_manager import DatabaseManager
from monitoring_service import MonitoringService
from notification_service import NotificationService

# Global instances
db_manager = DatabaseManager()
monitoring_service = MonitoringService(db_manager)
notification_service = NotificationService(db_manager)