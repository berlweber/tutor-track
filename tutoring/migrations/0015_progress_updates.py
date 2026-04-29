from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tutoring", "0014_student_first_name_student_last_name_and_more"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="monthlyreport",
            name="unique_monthly_report_per_assignment",
        ),
        migrations.RenameField(
            model_name="monthlyreport",
            old_name="month",
            new_name="report_date",
        ),
        migrations.AlterField(
            model_name="monthlyreport",
            name="content",
            field=models.TextField(verbose_name="עידכון התקדמות"),
        ),
        migrations.AlterField(
            model_name="monthlyreport",
            name="report_date",
            field=models.DateField(verbose_name="תאריך העדכון"),
        ),
        migrations.AlterModelOptions(
            name="monthlyreport",
            options={"ordering": ["-report_date", "-created_at"]},
        ),
    ]
