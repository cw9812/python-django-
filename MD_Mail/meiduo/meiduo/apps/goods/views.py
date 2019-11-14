from django.shortcuts import render

# Create your views here.
from drf_haystack.viewsets import HaystackViewSet
from rest_framework import generics
from rest_framework.filters import OrderingFilter

from meiduo.meiduo.apps.goods.models import SKU
from meiduo.meiduo.apps.goods.serializers import SKUSerializer, SKUIndexSerializer


class SKUListView(generics.ListAPIView):
    """
    sku列表数据
    """
    serializer_class = SKUSerializer
    filter_backends = (OrderingFilter,)
    ordering_fields = ('create_time', 'price', 'sales')

    def get_queryset(self):
        category_id = self.kwargs['category_id']
        return SKU.objects.filter(category_id=category_id, is_launched=True)


class SKUSearchViewSet(HaystackViewSet):
    """
    SKU搜索
    """
    index_models = [SKU]
    serializer_class = SKUIndexSerializer

