import os

import invoice_process

from utilities import send_email, get_sqs_resource


QUEUE_NAME = os.getenv('QUEUE_NAME')
MAX_QUEUE_MESSAGES = 1

sqs = get_sqs_resource()
queue = sqs.get_queue_by_name(QueueName=QUEUE_NAME)

from_email = os.getenv("FROM_EMAIL", 'LTC <reporter@ltc.com>')
to_email = os.getenv("TO_EMAIL", 'info@ltc.com')

TEST_MODE = True

while True:
    for message in queue.receive_messages(MaxNumberOfMessages=MAX_QUEUE_MESSAGES, WaitTimeSeconds=5):
        file_name = message.body.replace('+', ' ')
        print (file_name, '='*10)
        message.delete()

        result, log_file, invoice_info = invoice_process.validate_file(file_name, TEST_MODE)
        if result:
            result = invoice_process.process_invoice(invoice_info, log_file, TEST_MODE)
            email_body = 'Uploaded successfully' if result else 'Insertion failed'
        else:
            email_body = 'Validation failed'

        subject = f'Invoice Uploaded Successfully ({file_name})'
        send_email(subject, from_email, [to_email], email_body, log_file)
