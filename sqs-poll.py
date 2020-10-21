import invoice_process

from utilities import send_email, get_sqs_resource


QUEUE_NAME = 'ltc-ancillary-reconciliation.fifo'
MAX_QUEUE_MESSAGES = 1

sqs = get_sqs_resource()
queue = sqs.get_queue_by_name(QueueName=QUEUE_NAME)

from_email = 'LTC <don@audienz.com>'
to_emails = 'don.5001001@gmail.com'

while True:
    for message in queue.receive_messages(MaxNumberOfMessages=MAX_QUEUE_MESSAGES, WaitTimeSeconds=5):
        file_name = message.body.replace('+', ' ')
        print (file_name, '='*10)
        message.delete()

        (facility_pharmacy_map, invoice_dt, source, data) = invoice_process.validate_file(file_name)
        if not data:
            raise exception("The file is invalid.")

        res = invoice_process.process_invoice(facility_pharmacy_map, invoice_dt, source, data)

        subject = f'Invoice Processed ({pharmacy})'
        # send_email(subject, from_email, to_emails, email_body, log_file)
