from pathlib import Path
import json

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Avg, Count, Q
from django.shortcuts import get_object_or_404, redirect, render

from .forms import (
    AdminSetPasswordForm, AdminUserCreateForm, AdminUserEditForm, PredictionForm
)
from .ml_predictor import load_metrics, predict
from .models import StudentPrediction


def home(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    return render(request, "predictor/home.html")


@login_required
def dashboard(request):
    qs = StudentPrediction.objects.filter(user=request.user)
    stats = qs.aggregate(avg=Avg("estimated_average"))
    total = qs.count()
    passed = qs.filter(pass_fail="Pass").count()

    context = {
        "total": total,
        "passed": passed,
        "failed": total - passed,
        "pass_rate": round((passed / total) * 100, 1) if total else 0,
        "average": round(stats["avg"], 2) if stats["avg"] is not None else 0,
        "recent": qs[:5],
        "metrics": load_metrics(),
    }
    return render(request, "predictor/dashboard.html", context)


@login_required
def new_prediction(request):
    if request.method == "POST":
        form = PredictionForm(request.POST)
        if form.is_valid():
            d = form.cleaned_data
            data = {
                "gender": d["gender"],
                "race/ethnicity": d["race_ethnicity"],
                "parental level of education": d["parental_education"],
                "lunch": d["lunch"],
                "test preparation course": d["test_preparation"],
                "reading score": d["reading_score"],
                "writing score": d["writing_score"],
            }

            try:
                result = predict(data)
            except FileNotFoundError:
                messages.error(
                    request,
                    "ML models are not trained yet. Run: python train_models.py",
                )
                return redirect("predict")
            except Exception as exc:
                messages.error(request, f"Prediction error: {exc}")
                return render(
                    request, "predictor/predict.html", {"form": form}
                )

            record = StudentPrediction.objects.create(
                user=request.user,
                gender=d["gender"],
                race_ethnicity=d["race_ethnicity"],
                parental_education=d["parental_education"],
                lunch=d["lunch"],
                test_preparation=d["test_preparation"],
                reading_score=d["reading_score"],
                writing_score=d["writing_score"],
                predicted_math_score=result["predicted_math"],
                estimated_average=result["estimated_average"],
                performance_category=result["performance_category"],
                pass_fail=result["pass_fail"],
                ridge_math=result["ridge_math"],
                xgb_math=result["xgb_math"],
                svm_prediction=result["svm_prediction"],
                xgb_prediction=result["xgb_prediction"],
                pass_probability=result["pass_probability"],
                fail_probability=result["fail_probability"],
            )
            return redirect("result", pk=record.pk)
    else:
        form = PredictionForm()

    return render(request, "predictor/predict.html", {"form": form})


@login_required
def result(request, pk):
    if request.user.is_staff:
        record = get_object_or_404(StudentPrediction, pk=pk)
    else:
        record = get_object_or_404(
            StudentPrediction, pk=pk, user=request.user
        )
    return render(
        request,
        "predictor/result.html",
        {"record": record, "metrics": load_metrics()},
    )


@login_required
def history(request):
    records = StudentPrediction.objects.filter(user=request.user)
    return render(
        request,
        "predictor/history.html",
        {"records": records, "metrics": load_metrics()},
    )


@login_required
def profile(request):
    return render(request, "predictor/profile.html")


def staff_required(view):
    return user_passes_test(
        lambda user: user.is_authenticated and user.is_staff,
        login_url="login",
    )(view)


@staff_required
def admin_dashboard(request):
    User = get_user_model()
    predictions = StudentPrediction.objects.select_related("user")
    total_users = User.objects.count()
    total_predictions = predictions.count()
    passed = predictions.filter(pass_fail="Pass").count()
    failed = total_predictions - passed
    avg = predictions.aggregate(v=Avg("estimated_average"))["v"]

    today = __import__("django.utils.timezone", fromlist=["now"]).now().date()
    today_count = predictions.filter(created_at__date=today).count()

    # Dataset overview is intentionally read-only and comes from the same
    # CSV consumed by train_models.py.
    dataset_rows = 0
    dataset_columns = 0
    csv_path = Path(__file__).resolve().parent.parent / "dataset" / "StudentsPerformance.csv"
    try:
        import pandas as pd
        data = pd.read_csv(csv_path)
        dataset_rows, dataset_columns = data.shape
    except Exception:
        pass

    context = {
        "total_users": total_users,
        "total_predictions": total_predictions,
        "passed": passed,
        "failed": failed,
        "pass_rate": round(passed / total_predictions * 100, 1)
        if total_predictions else 0,
        "average": round(avg, 2) if avg is not None else 0,
        "today_count": today_count,
        "recent": predictions[:10],
        "metrics": load_metrics(),
        "dataset_rows": dataset_rows,
        "dataset_columns": dataset_columns,
    }
    return render(request, "predictor/admin_dashboard.html", context)


# ---------------------------------------------------------------------------
# In-app user management (staff only)
# ---------------------------------------------------------------------------


@staff_required
def user_list(request):
    User = get_user_model()
    query = request.GET.get("q", "").strip()
    users = User.objects.annotate(
        prediction_count=Count("predictions")
    ).order_by("-date_joined")
    if query:
        users = users.filter(
            Q(username__icontains=query) | Q(email__icontains=query)
        )
    return render(
        request,
        "predictor/admin_users.html",
        {"users": users, "query": query},
    )


@staff_required
def user_add(request):
    if request.method == "POST":
        form = AdminUserCreateForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f"Account '{user.username}' created.")
            return redirect("user_detail", pk=user.pk)
    else:
        form = AdminUserCreateForm()
    return render(request, "predictor/admin_user_form.html", {"form": form, "mode": "add"})


@staff_required
def user_detail(request, pk):
    User = get_user_model()
    person = get_object_or_404(User, pk=pk)
    predictions = StudentPrediction.objects.filter(user=person)
    return render(
        request,
        "predictor/admin_user_detail.html",
        {"person": person, "predictions": predictions},
    )


@staff_required
def user_edit(request, pk):
    User = get_user_model()
    person = get_object_or_404(User, pk=pk)
    if request.method == "POST":
        form = AdminUserEditForm(request.POST, instance=person)
        if form.is_valid():
            if person == request.user and not form.cleaned_data["is_staff"]:
                messages.error(request, "You can't remove your own staff access.")
            elif person == request.user and not form.cleaned_data["is_active"]:
                messages.error(request, "You can't deactivate your own account.")
            else:
                form.save()
                messages.success(request, f"Account '{person.username}' updated.")
                return redirect("user_detail", pk=person.pk)
    else:
        form = AdminUserEditForm(instance=person)
    return render(
        request,
        "predictor/admin_user_form.html",
        {"form": form, "mode": "edit", "person": person},
    )


@staff_required
def user_set_password(request, pk):
    User = get_user_model()
    person = get_object_or_404(User, pk=pk)
    if request.method == "POST":
        form = AdminSetPasswordForm(person, request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, f"Password updated for '{person.username}'.")
            return redirect("user_detail", pk=person.pk)
    else:
        form = AdminSetPasswordForm(person)
    return render(
        request,
        "predictor/admin_user_password.html",
        {"form": form, "person": person},
    )


@staff_required
def user_delete(request, pk):
    User = get_user_model()
    person = get_object_or_404(User, pk=pk)
    if request.method == "POST":
        if person == request.user:
            messages.error(request, "You can't delete your own account.")
            return redirect("user_detail", pk=person.pk)
        username = person.username
        person.delete()
        messages.success(request, f"Account '{username}' and its predictions were deleted.")
        return redirect("user_list")
    return render(request, "predictor/admin_user_confirm_delete.html", {"person": person})


@staff_required
def prediction_delete(request, pk):
    record = get_object_or_404(StudentPrediction, pk=pk)
    owner_pk = record.user_id
    if request.method == "POST":
        record.delete()
        messages.success(request, "Prediction record deleted.")
    return redirect("user_detail", pk=owner_pk)
