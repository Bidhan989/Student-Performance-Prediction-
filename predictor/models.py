from django.contrib.auth.models import User
from django.db import models


class StudentPrediction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="predictions")
    gender = models.CharField(max_length=20)
    race_ethnicity = models.CharField(max_length=30)
    parental_education = models.CharField(max_length=100)
    lunch = models.CharField(max_length=30)
    test_preparation = models.CharField(max_length=30)
    reading_score = models.FloatField()
    writing_score = models.FloatField()

    # Final prediction outputs
    predicted_math_score = models.FloatField()
    estimated_average = models.FloatField()
    performance_category = models.CharField(max_length=30)
    pass_fail = models.CharField(max_length=10)

    # Model-by-model outputs
    ridge_math = models.FloatField(default=0)
    xgb_math = models.FloatField(default=0)
    svm_prediction = models.CharField(max_length=10, default="Fail")
    xgb_prediction = models.CharField(max_length=10, default="Fail")
    pass_probability = models.FloatField(default=0)
    fail_probability = models.FloatField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username} - {self.created_at:%Y-%m-%d %H:%M}"
