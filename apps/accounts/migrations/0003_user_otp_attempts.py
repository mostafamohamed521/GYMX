# Generated for OTP brute-force protection (otp_attempts counter)

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_user_email_otp_user_emergency_contact_name_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='otp_attempts',
            field=models.PositiveSmallIntegerField(default=0),
        ),
    ]
