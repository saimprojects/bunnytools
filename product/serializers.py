"""
Serializers to convert model instances into JSON for API responses and
to validate incoming data for creation and updates.
"""
from rest_framework import serializers
from .models import (
    Category,
    Product,
    ProductImage,
    Review,
    WhatsAppSettings,
    ProductPlan,
    BankAccount,
    Order,
)


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug']


class ProductImageSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'is_main', 'ordering']

    def get_image(self, obj):
        if obj.image:
            return obj.image.url
        return None


class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = [
            'id',
            'customer_name',
            'rating',
            'comment',
            'created_at',
        ]


class ProductPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductPlan
        fields = [
            'id',
            'title',
            'duration_months',
            'price',
        ]


class ProductSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)
    reviews = ReviewSerializer(many=True, read_only=True)
    categories = CategorySerializer(many=True, read_only=True)
    plans = ProductPlanSerializer(many=True, read_only=True)
    main_image = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id',
            'title',
            'description',
            'price',
            'status',
            'categories',
            'images',
            'main_image',
            'reviews',
            'plans',
            'created_at',
            'updated_at',
        ]

    def get_main_image(self, obj):
        img = obj.images.filter(is_main=True).first() or obj.images.first()
        return img.image.url if img else None


class WhatsAppSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = WhatsAppSettings
        fields = ['whatsapp_number']


class BankAccountSerializer(serializers.ModelSerializer):
    bank_name_display = serializers.CharField(source='get_bank_name_display', read_only=True)
    
    class Meta:
        model = BankAccount
        fields = [
            'id',
            'bank_name',
            'bank_name_display',
            'account_title',
            'account_number',
            'iban',
            'is_active',
        ]


class OrderCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = [
            'customer_name',
            'customer_email',
            'customer_phone',
            'customer_address',
            'product',
            'plan',
            'amount',
            'bank_account',
            'transaction_id',
            'payment_proof',
        ]

    def validate(self, data):
        # Validate that if plan is selected, amount matches plan price
        if data.get('plan'):
            if data['amount'] != data['plan'].price:
                raise serializers.ValidationError({
                    'amount': 'Amount does not match the selected plan price'
                })
        return data


class OrderSerializer(serializers.ModelSerializer):
    product_details = ProductSerializer(source='product', read_only=True)
    plan_details = ProductPlanSerializer(source='plan', read_only=True)
    bank_account_details = BankAccountSerializer(source='bank_account', read_only=True)
    payment_proof_url = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Order
        fields = [
            'id',
            'customer_name',
            'customer_email',
            'customer_phone',
            'customer_address',
            'product',
            'product_details',
            'plan',
            'plan_details',
            'amount',
            'bank_account',
            'bank_account_details',
            'transaction_id',
            'payment_proof',
            'payment_proof_url',
            'status',
            'status_display',
            'admin_notes',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['status', 'admin_notes']
    
    def get_payment_proof_url(self, obj):
        if obj.payment_proof:
            return obj.payment_proof.url
        return None


class OrderStatusUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['status', 'admin_notes']