from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("predictor", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="studentprediction",
            name="ridge_math",
            field=models.FloatField(default=0),
        ),
        migrations.AddField(
            model_name="studentprediction",
            name="xgb_math",
            field=models.FloatField(default=0),
        ),
        migrations.AddField(
            model_name="studentprediction",
            name="svm_prediction",
            field=models.CharField(default="Fail", max_length=10),
        ),
        migrations.AddField(
            model_name="studentprediction",
            name="xgb_prediction",
            field=models.CharField(default="Fail", max_length=10),
        ),
    ]
