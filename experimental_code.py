import time
import spidev
import smtplib
from email.mime.text import MIMEText
from datetime import datetime, timedelta

# SPI setup
spi = spidev.SpiDev()
spi.open(0, 0)
spi.max_speed_hz = 1350000

# User-defined configuration
min_val = 300  # Your calibrated wet ADC value
max_val = 850  # Your calibrated dry ADC value
threshold_percentage = 20  # Alert if below this percentage

# Email configuration
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587
EMAIL_ADDRESS = 'your_email@gmail.com'
EMAIL_PASSWORD = 'your_app_password'  # Use an app password if Gmail
RECIPIENT_EMAIL = 'recipient_email@example.com'

def read_channel(channel):
    adc = spi.xfer2([1, (8 + channel) << 4, 0])
    data = ((adc[1] & 3) << 8) + adc[2]
    return data

def convert_to_percent(value, min_val, max_val):
    value = max(min_val, min(value, max_val))
    percentage = ((max_val - value) / (max_val - min_val)) * 100
    return round(percentage, 1)

def send_email_alert(moisture_percent):
    subject = '⚠️ Low Soil Moisture Alert'
    body = f'Soil moisture has dropped to {moisture_percent}%.'
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = RECIPIENT_EMAIL

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.sendmail(EMAIL_ADDRESS, RECIPIENT_EMAIL, msg.as_string())
        print("✅ Email alert sent.")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
    finally:
        server.quit()

try:
    last_email_sent = datetime.min
    email_interval = timedelta(days=1)

    while True:
        adc_value = read_channel(0)
        moisture_percent = convert_to_percent(adc_value, min_val, max_val)
        print(f"Soil Moisture: {moisture_percent}% (ADC Value: {adc_value})")

        if moisture_percent < threshold_percentage and datetime.now() - last_email_sent > email_interval:
            send_email_alert(moisture_percent)
            last_email_sent = datetime.now()

        time.sleep(10)

except KeyboardInterrupt:
    print("Program terminated by user.")

finally:
    spi.close()
