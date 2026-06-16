from django.urls import path
from api import views
from api.views import (
    health,
    list_opportunities,
    opportunity_detail,
    top_opportunities,
    interests_view,
    run_pipeline_and_save,
)

urlpatterns = [
    path("health", health),
    path("opportunities", list_opportunities),
    path("opportunities/top", top_opportunities),
    path("opportunities/<int:pk>", opportunity_detail),
    path("register", views.register),
    path("login", views.login),
    path("company/interests", interests_view),
    path("pipeline/run", run_pipeline_and_save),
]
