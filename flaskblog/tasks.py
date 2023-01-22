from celery import shared_task


@shared_task
def send_sms(phone_number, message):
    # Send SMS here using a third-party service or some other method
    print(f"Sending SMS to {phone_number} with message: {message}")
    pass