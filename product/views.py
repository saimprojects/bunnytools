from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from .models import Category, Product, Review, WhatsAppSettings, ProductPlan, BankAccount, Order
from .serializers import (
    CategorySerializer,
    ProductSerializer,
    ReviewSerializer,
    WhatsAppSettingsSerializer,
    ProductPlanSerializer,
    BankAccountSerializer,
    OrderSerializer,
    OrderCreateSerializer,
    OrderStatusUpdateSerializer,
)


class IsAdminOrReadOnly(permissions.BasePermission):
    """Custom permission to allow only admins to modify data."""

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_staff


class IsAdminUser(permissions.BasePermission):
    """Permission for admin-only endpoints."""
    
    def has_permission(self, request, view):
        return request.user and request.user.is_staff


class CategoryViewSet(viewsets.ModelViewSet):
    """CRUD viewset for categories."""
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.method in permissions.SAFE_METHODS:
            qs = qs.filter(status=True)
        return qs


class ProductViewSet(viewsets.ModelViewSet):
    """CRUD viewset for products with public read and admin write access."""
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        qs = super().get_queryset().prefetch_related('images', 'reviews', 'categories', 'plans')
        if self.request.method in permissions.SAFE_METHODS:
            qs = qs.filter(status=True)
        return qs


class ReviewViewSet(viewsets.ModelViewSet):
    """CRUD viewset for reviews. Reviews are managed by admins only."""
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        qs = super().get_queryset().select_related('product')
        if self.request.method in permissions.SAFE_METHODS:
            qs = qs.filter(status=True)
        return qs


class ProductPlanViewSet(viewsets.ModelViewSet):
    queryset = ProductPlan.objects.select_related('product')
    serializer_class = ProductPlanSerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.method in permissions.SAFE_METHODS:
            qs = qs.filter(is_active=True)
        return qs


class WhatsAppSettingsPublicView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        obj, _ = WhatsAppSettings.objects.get_or_create(pk=1, defaults={"whatsapp_number": "+923001234567"})
        return Response(WhatsAppSettingsSerializer(obj).data)


class BankAccountViewSet(viewsets.ModelViewSet):
    """CRUD viewset for bank accounts - Admin only for write, public for read."""
    queryset = BankAccount.objects.filter(is_active=True)
    serializer_class = BankAccountSerializer
    
    def get_permissions(self):
        if self.request.method in permissions.SAFE_METHODS:
            return [permissions.AllowAny()]
        return [IsAdminUser()]


class OrderViewSet(viewsets.ModelViewSet):
    """Viewset for handling orders."""
    queryset = Order.objects.select_related('product', 'plan', 'bank_account')
    
    def get_permissions(self):
        # ✅ IMPORTANT: create aur track endpoints PUBLIC hain (no auth required)
        if self.action == 'create' or self.action == 'track':
            return [permissions.AllowAny()]
        # Baaki sab endpoints (list, retrieve, update, delete) admin only
        return [IsAdminUser()]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return OrderCreateSerializer
        if self.action in ['update_status', 'partial_update_status']:
            return OrderStatusUpdateSerializer
        return OrderSerializer
    
    def create(self, request, *args, **kwargs):
        """Override create to return full order details."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = serializer.save()
        
        # Return full order data using OrderSerializer
        output_serializer = OrderSerializer(order, context={'request': request})
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)
    
    def get_queryset(self):
        qs = super().get_queryset()
        
        # Filter by status if provided
        status_filter = self.request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter.upper())
        
        # Filter by product if provided
        product_id = self.request.query_params.get('product')
        if product_id:
            qs = qs.filter(product_id=product_id)
            
        return qs
    
    @action(detail=True, methods=['patch'], permission_classes=[IsAdminUser])
    def update_status(self, request, pk=None):
        """Admin endpoint to update order status."""
        order = self.get_object()
        serializer = OrderStatusUpdateSerializer(order, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response(OrderSerializer(order).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.AllowAny])
    def track(self, request):
        """Public endpoint to track order by ID or email. NO AUTH REQUIRED."""
        order_id = request.query_params.get('order_id')
        email = request.query_params.get('email')
        
        print(f"🔍 Track request - order_id: {order_id}, email: {email}")  # Debug log
        
        if order_id:
            try:
                order = Order.objects.get(id=order_id)
                serializer = OrderSerializer(order, context={'request': request})
                return Response(serializer.data)
            except Order.DoesNotExist:
                return Response(
                    {'error': 'Order not found'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
        elif email:
            orders = Order.objects.filter(customer_email__iexact=email)
            if orders.exists():
                serializer = OrderSerializer(orders, many=True, context={'request': request})
                return Response(serializer.data)
            return Response(
                {'error': 'No orders found for this email'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        else:
            return Response(
                {'error': 'Please provide order_id or email parameter'}, 
                status=status.HTTP_400_BAD_REQUEST
            )