from drf_haystack.serializers import HaystackSerializer
from rest_framework import serializers

from meiduo.meiduo.apps.goods.models import SKU
from meiduo.meiduo.apps.goods.search_indexes import SKUIndex


class SKUSerializer(serializers.ModelSerializer):
    """
    SKU序列化器
    """

    class Meta:
        model = SKU
        fields = ('id', 'name', 'price', 'default_image_url', 'comments')


class SKUIndexSerializer(HaystackSerializer):
    """
    SKU索引结果数据序列化器
    """
    object = SKUSerializer(read_only=True)

    class Meta:
        index_classes = [SKUIndex]
        fields = (
            'text',  # 用于接收查询关键字
            'object',  # 用于返回查询结果
        )
