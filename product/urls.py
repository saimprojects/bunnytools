from django.urls import path
from rest_framework.routers import DefaultRouter
from django.contrib import admin

from .views import (
    CategoryViewSet,
    ProductViewSet,
    ReviewViewSet,
    WhatsAppSettingsPublicView,
    ProductPlanViewSet,
    BankAccountViewSet,
    OrderViewSet,
)

router = DefaultRouter()
router.register(r"categories", CategoryViewSet, basename="category")
router.register(r"products", ProductViewSet, basename="product")
router.register(r"reviews", ReviewViewSet, basename="review")
router.register(r"plans", ProductPlanViewSet, basename="plan")
router.register(r"bank-accounts", BankAccountViewSet, basename="bank-account")
router.register(r"orders", OrderViewSet, basename="order")

urlpatterns = [
    *router.urls,
    path("whatsapp/", WhatsAppSettingsPublicView.as_view(), name="whatsapp-settings"),
]