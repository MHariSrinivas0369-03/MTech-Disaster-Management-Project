"""
SMS notification service using Twilio
"""
import logging
from twilio.rest import Client
from twilio.base.exceptions import TwilioException
from config import TWILIO_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE, MY_PHONE
from database import get_volunteers

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SMSService:

    def __init__(self):
        if not all([TWILIO_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE]):
            logger.warning("Twilio credentials not properly configured")
            self.client = None
        else:
            self.client = Client(TWILIO_SID, TWILIO_AUTH_TOKEN)

        self.sent_messages = []

    def send_sms(self, to_phone, message):
        """Send SMS message to a phone number"""
        if not self.client:
            logger.error("Twilio client not initialized. Check credentials.")
            return False

        try:
            # Clean phone number format
            if not to_phone.startswith('+'):
                if to_phone.startswith('91'):
                    to_phone = '+' + to_phone
                elif len(to_phone) == 10:
                    to_phone = '+91' + to_phone
                else:
                    to_phone = '+91' + to_phone

            message_obj = self.client.messages.create(body=message,
                                                      from_=TWILIO_PHONE,
                                                      to=to_phone)

            self.sent_messages.append({
                'to': to_phone,
                'message_sid': message_obj.sid,
                'status': 'sent',
                'timestamp': message_obj.date_created
            })

            logger.info(
                f"SMS sent successfully to {to_phone}, SID: {message_obj.sid}")
            return True

        except TwilioException as e:
            logger.error(f"Twilio error sending SMS to {to_phone}: {str(e)}")
            return False
        except Exception as e:
            logger.error(
                f"Unexpected error sending SMS to {to_phone}: {str(e)}")
            return False

    def send_alert_to_volunteer(self, volunteer, alert):
        """Send alert message to a single volunteer"""
        volunteer_message = f"VOLUNTEER ASSIGNMENT - {volunteer['name']}\n\n{alert['message']}\n\nPlease proceed to the location and report back. Stay safe!"
        return self.send_sms(volunteer['phone'], volunteer_message)

    def send_admin_alert(self, alert):
        """Send alert to admin/authority phone number"""
        if not MY_PHONE or MY_PHONE == "+919999999999":
            logger.warning("Admin phone number not configured")
            return False

        admin_message = f"ADMIN ALERT\n\n{alert['message']}\n\nImmediate attention required for {alert['district']} district."

        return self.send_sms(MY_PHONE, admin_message)

    def send_test_message(self):
        """Send a test message to verify SMS service"""
        if not MY_PHONE or MY_PHONE == "+919999999999":
            logger.warning("Admin phone number not configured for test")
            return False

        test_message = "🧪 HP Disaster Alert System - Test Message\n\nSMS service is working correctly. System is monitoring weather conditions across all 12 districts of Himachal Pradesh."

        return self.send_sms(MY_PHONE, test_message)

    def broadcast_emergency_alert(self, message, district=None):
        """Broadcast emergency message to all available volunteers"""
        volunteers = get_volunteers()

        if district:
            volunteers = [v for v in volunteers if v[3] == district]

        sent_count = 0

        for volunteer in volunteers:
            vol_id, name, phone, vol_district, skills, status, registered_at, workload, lat, lon = volunteer

            emergency_message = f"🚨 EMERGENCY BROADCAST\n\n{message}\n\nThis is an urgent alert for {district or 'all districts'}. Please respond immediately if you can assist."

            if self.send_sms(phone, emergency_message):
                sent_count += 1

        if self.send_sms(
                MY_PHONE,
                f"EMERGENCY BROADCAST SENT\n\n{message}\n\nSent to {sent_count} volunteers."
        ):
            sent_count += 1

        return sent_count

    def get_sms_stats(self):
        """Get SMS sending statistics"""
        return {
            'total_sent': len(self.sent_messages),
            'recent_messages': self.sent_messages[-10:],
            'service_status': 'Active' if self.client else 'Inactive'
        }

def test_sms_service():
    """Test SMS service functionality"""
    sms_service = SMSService()

    print("=== SMS Service Test ===")
    print(f"Service Status: {sms_service.get_sms_stats()['service_status']}")

    if sms_service.client:
        print("Sending test message...")
        success = sms_service.send_test_message()
        print(f"Test message sent: {'✅ Success' if success else '❌ Failed'}")
    else:
        print("❌ SMS service not configured (missing Twilio credentials)")

    stats = sms_service.get_sms_stats()
    print(f"Total messages sent: {stats['total_sent']}")


if __name__ == "__main__":
    test_sms_service()