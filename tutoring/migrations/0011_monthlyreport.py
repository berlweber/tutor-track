from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("tutoring", "0010_alter_assignment_session_length"),
    ]

    operations = [
        migrations.CreateModel(
            name="MonthlyReport",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("month", models.DateField(verbose_name="חודש הדוח")),
                ("content", models.TextField(verbose_name="דוח התקדמות")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("assignment", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="tutoring.assignment")),
            ],
            options={
                "ordering": ["-month", "-updated_at"],
            },
        ),
        migrations.AddConstraint(
            model_name="monthlyreport",
            constraint=models.UniqueConstraint(fields=("assignment", "month"), name="unique_monthly_report_per_assignment"),
        ),
    ]
