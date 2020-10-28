import invoice_process

from utilities import send_email, get_sqs_resource


QUEUE_NAME = 'ltc-ancillary-reconciliation.fifo'
MAX_QUEUE_MESSAGES = 1

sqs = get_sqs_resource()
queue = sqs.get_queue_by_name(QueueName=QUEUE_NAME)

from_email = 'LTC <it.corridor051@gmail.com>'
to_emails = 'jason.5001001@gmail.com'

TEST_MODE = True

while True:
    for message in queue.receive_messages(MaxNumberOfMessages=MAX_QUEUE_MESSAGES, WaitTimeSeconds=5):
        file_name = message.body.replace('+', ' ')
        print (file_name, '='*10)
        message.delete()

        result, log_file, invoice_info = invoice_process.validate_file(file_name, TEST_MODE)
        if result:
            result = invoice_process.process_invoice(invoice_info, log_file, TEST_MODE)
            email_body = 'Inserted successfully' if result else 'Insertion failed'
        else:
            email_body = 'Validation failed'

        subject = f'Invoice Processed ({file_name})'
        send_email(subject, from_email, to_emails, email_body, log_file)
