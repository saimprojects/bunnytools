from django.contrib import admin
from django.db.models import Count, Q
from django.utils.html import format_html
from django.urls import path
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import datetime
import json
from .models import (
    Product,
    ProductImage,
    Category,
    Review,
    WhatsAppSettings,
    ProductPlan,
    BankAccount,
    Order,
)


# =========================
# Inline Admins
# =========================

class ProductPlanInline(admin.TabularInline):
    model = ProductPlan
    extra = 1
    fields = ("title", "duration_months", "price", "is_active")
    ordering = ("duration_months",)


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ("image", "is_main", "ordering")
    ordering = ("ordering",)


class ReviewInline(admin.TabularInline):
    model = Review
    extra = 0
    readonly_fields = ("created_at",)
    fields = ("customer_name", "rating", "comment", "status", "created_at")


# =========================
# Product Admin
# =========================

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "plans_count",
        "images_count",
        "status",
        "created_at",
    )
    list_filter = ("status", "categories")
    search_fields = ("title",)
    filter_horizontal = ("categories",)
    inlines = [
        ProductPlanInline,
        ProductImageInline,
        ReviewInline,
    ]
    ordering = ("-created_at",)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(
            _plans_count=Count("plans"),
            _images_count=Count("images"),
        )

    @admin.display(description="Plans")
    def plans_count(self, obj):
        return obj._plans_count

    @admin.display(description="Images")
    def images_count(self, obj):
        return obj._images_count


# =========================
# Product Plan Admin
# =========================

@admin.register(ProductPlan)
class ProductPlanAdmin(admin.ModelAdmin):
    list_display = (
        "product",
        "title",
        "duration_display",
        "price",
        "is_active",
    )
    list_filter = ("is_active",)
    search_fields = ("product__title", "title")
    ordering = ("product", "duration_months")

    @admin.display(description="Duration")
    def duration_display(self, obj):
        if obj.duration_months == 0:
            return "Lifetime"
        return f"{obj.duration_months} Month(s)"


# =========================
# Category Admin
# =========================

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "status")
    list_filter = ("status",)
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}


# =========================
# Review Admin
# =========================

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = (
        "product",
        "customer_name",
        "rating",
        "status",
        "created_at",
    )
    list_filter = ("status", "rating")
    search_fields = ("customer_name", "product__title")
    readonly_fields = ("created_at",)


# =========================
# WhatsApp Settings (Singleton)
# =========================

@admin.register(WhatsAppSettings)
class WhatsAppSettingsAdmin(admin.ModelAdmin):
    list_display = ("whatsapp_number", "updated_at")

    def has_add_permission(self, request):
        try:
            return not WhatsAppSettings.objects.exists()
        except Exception:
            return True

    def has_delete_permission(self, request, obj=None):
        return False


# =========================
# Bank Account Admin
# =========================

@admin.register(BankAccount)
class BankAccountAdmin(admin.ModelAdmin):
    list_display = (
        "bank_name",
        "account_title",
        "account_number",
        "is_active",
        "created_at",
    )
    list_filter = ("is_active", "bank_name")
    search_fields = ("account_title", "account_number", "iban")
    ordering = ("bank_name", "-created_at")


# =========================
# Order Admin
# =========================

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "customer_name",
        "product",
        "plan_display",
        "amount",
        "status_badge",
        "payment_proof_preview",
        "created_at",
    )
    list_filter = ("status", "product", "bank_account", "created_at")
    search_fields = (
        "customer_name",
        "customer_email",
        "customer_phone",
        "transaction_id",
        "id",
    )
    readonly_fields = (
        "created_at",
        "updated_at",
        "payment_proof_preview_large",
    )
    fieldsets = (
        ("Customer Information", {
            "fields": (
                "customer_name",
                "customer_email",
                "customer_phone",
                "customer_address",
            )
        }),
        ("Order Details", {
            "fields": (
                "product",
                "plan",
                "amount",
                "bank_account",
            )
        }),
        ("Payment Information", {
            "fields": (
                "transaction_id",
                "payment_proof",
                "payment_proof_preview_large",
            )
        }),
        ("Order Status", {
            "fields": (
                "status",
                "admin_notes",
            )
        }),
        ("Timestamps", {
            "fields": (
                "created_at",
                "updated_at",
            )
        }),
    )
    ordering = ("-created_at",)
    actions = ["mark_as_completed", "mark_as_processing", "mark_as_cancelled"]

    @admin.display(description="Plan")
    def plan_display(self, obj):
        if obj.plan:
            return obj.plan.title
        return "—"

    @admin.display(description="Status")
    def status_badge(self, obj):
        colors = {
            'PENDING': 'orange',
            'PROCESSING': 'blue',
            'COMPLETED': 'green',
            'CANCELLED': 'red',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="color: white; background-color: {}; padding: 5px 10px; '
            'border-radius: 4px; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )

    @admin.display(description="Payment Proof")
    def payment_proof_preview(self, obj):
        if obj.payment_proof:
            return format_html(
                '<a href="{}" target="_blank">'
                '<img src="{}" style="max-height: 50px; border-radius: 4px;"/>'
                '</a>',
                obj.payment_proof.url,
                obj.payment_proof.url
            )
        return "No proof uploaded"

    @admin.display(description="Payment Proof (Full Size)")
    def payment_proof_preview_large(self, obj):
        if obj.payment_proof:
            return format_html(
                '<a href="{}" target="_blank">'
                '<img src="{}" style="max-width: 400px; border-radius: 8px;"/>'
                '</a><br/>'
                '<a href="{}" target="_blank" style="margin-top: 10px; display: inline-block; '
                'padding: 5px 10px; background: #007bff; color: white; text-decoration: none; '
                'border-radius: 4px;">Open Full Image</a>',
                obj.payment_proof.url,
                obj.payment_proof.url,
                obj.payment_proof.url
            )
        return "No proof uploaded"

    @admin.action(description="Mark selected orders as Completed")
    def mark_as_completed(self, request, queryset):
        queryset.update(status='COMPLETED')
        self.message_user(request, f"{queryset.count()} orders marked as completed.")

    @admin.action(description="Mark selected orders as Processing")
    def mark_as_processing(self, request, queryset):
        queryset.update(status='PROCESSING')
        self.message_user(request, f"{queryset.count()} orders marked as processing.")

    @admin.action(description="Mark selected orders as Cancelled")
    def mark_as_cancelled(self, request, queryset):
        queryset.update(status='CANCELLED')
        self.message_user(request, f"{queryset.count()} orders marked as cancelled.")


# =========================
# Admin Site Customization
# =========================

# Customize admin site header and title
admin.site.site_header = "Bunny Tools Admin Panel"
admin.site.site_title = "Admin Portal"
admin.site.index_title = "Dashboard"

# Add custom context to admin index
original_index = admin.site.index
def custom_index(request, extra_context=None):
    if extra_context is None:
        extra_context = {}
    
    # Get pending orders count
    pending_orders_count = Order.objects.filter(status='PENDING').count()
    new_orders_today = Order.objects.filter(
        created_at__date=datetime.date.today()
    ).count()
    
    extra_context['pending_orders_count'] = pending_orders_count
    extra_context['new_orders_today'] = new_orders_today
    
    return original_index(request, extra_context)

admin.site.index = custom_index