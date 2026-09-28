from django.contrib import admin
from .models import StudentPrediction


@admin.register(StudentPrediction)
class StudentPredictionAdmin(admin.ModelAdmin):
    list_display = (
        "user", "predicted_math_score", "estimated_average",
        "performance_category", "pass_fail", "xgb_prediction", "created_at",
    )
    list_filter = ("pass_fail", "performance_category", "xgb_prediction", "svm_prediction", "created_at")
    search_fields = ("user__username", "user__email")
    readonly_fields = ("created_at",)
    ordering = ("-created_at",)
    list_per_page = 25

    fieldsets = (
        ("Student", {
            "fields": (
                "user", "gender", "race_ethnicity",
                "parental_education", "lunch", "test_preparation",
                "reading_score", "writing_score",
            )
        }),
        ("Prediction", {
            "fields": (
                "predicted_math_score", "estimated_average",
                "performance_category", "pass_fail",
            )
        }),
        ("Model outputs", {
            "fields": (
                "ridge_math", "xgb_math",
                "svm_prediction", "xgb_prediction",
                "pass_probability", "fail_probability",
            )
        }),
        ("Audit", {"fields": ("created_at",)}),
    )
