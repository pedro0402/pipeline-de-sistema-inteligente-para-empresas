from django.urls import path

from api.views import list_opportunities, opportunity_detail, top_opportunities

urlpatterns = [
    path("opportunities", list_opportunities),
    path("opportunities/top", top_opportunities),
    path("opportunities/<int:pk>", opportunity_detail),
]
