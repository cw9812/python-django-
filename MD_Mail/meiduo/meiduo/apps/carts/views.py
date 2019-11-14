from django_redis import get_redis_connection
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from meiduo.meiduo.apps.carts import constants
from meiduo.meiduo.apps.carts.serializers import CartSerializer, CartSKUSerializer, CartDeleteSerializer, CartSelectAllSerializer
from meiduo.meiduo.apps.goods.models import SKU
from meiduo.meiduo.utils import myjson


class CartView(APIView):
    """
    购物车
    """
    def perform_authentication(self, request):
        """
        重写父类的用户验证方法, 不在进入试图前就检查JWT
        """
        pass

    def post(self, request):
        """
        添加购物车
        """
        serializer = CartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        sku_id = serializer.validated_data.get('sku_id')
        count = serializer.validated_data.get('count')
        selected = serializer.validated_data.get('selected')

        # 尝试对请求的用户进行验证
        try:
            user = request.user
        except Exception:
            # 验证失败,用户未登录
            user = None

        if user is not None and user.is_authenticated:
            # 用户已登录,在redis中保存
            redis_conn = get_redis_connection('cart')
            pl = redis_conn.pipeline()
            # 记录购物车商品数量
            pl.hincrby('cart_%s' % user.id, sku_id, count)
            # 记录购物车的勾选项
            if selected:
                pl.sadd('cart_select_%s' % user.id, sku_id)
            pl.execute()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            # 用户未登录，在cookie中保存
            # {
            #     1001: { "count": 10, "selected": true},
            #     ...
            # }
            # 使用pickle序列化购物车数据，pickle操作的是bytes类型
            cart = request.COOKIES.get('cart')
            if cart is not None:
                cart = myjson.loads(cart)
            else:
                cart = {}

            sku = cart.get(sku_id)
            if sku:
                cart_count = int(sku.get('count'))
            else:
                cart_count = 0

            cart[sku_id] = {
                'count': count + cart_count,
                'selected': selected
            }

            cookie_cart = myjson.dumps(cart)
            response = Response(serializer.data, status=status.HTTP_201_CREATED)

            # 设置购物车的cookie
            # 需要设置有效期, 否则是临时cookie
            response.set_cookie('cart', cookie_cart, max_age=constants.CART_COOKIE_EXPIRES)
            return response

    def get(self, request):
        """
        获取购物车
        """
        try:
            user = request.user
        except Exception:
            user = None

        if user is not None and user.is_authenticated:
            # 用户已登录,从redis中读取
            redis_conn = get_redis_connection('cart')
            redis_cart = redis_conn.hgetall('cart_%s' % user.id)
            redis_cart_selected = redis_conn.smembers('cart_selected_%s' % user.id)
            cart = {}
            for sku_id, count in redis_cart.items():
                cart[int(sku_id)] = {
                    'count': int(count),
                    'selected': sku_id in redis_cart_selected
                }
        else:
            # 用户未登录,从cookie中读取
            cart = request.COOKIES.get('cart')
            if cart is not None:
                cart = myjson.loads(cart)
            else:
                cart = {}

        # 遍历处理购物车数据
        skus = SKU.objects.filter(id__in=cart.keys())
        for sku in skus:
            sku.count = cart[sku.id]['count']
            sku.selected = cart[sku.id]['selected']

        serializer = CartSKUSerializer(skus, many=True)
        return Response(serializer.data)

    def put(self, request):
        """
        修改购物车数据
        """
        serializer = CartSerializer(data=request.data)
        serializer.is_valid()
        sku_id = serializer.validated_data.get('sku_id')
        count = serializer.validated_data.get('count')
        selected = serializer.validated_data.get('selected')

        # 尝试对请求的用户进行验证
        try:
            user = request.user
        except Exception:
            # 验证失败,用户未登录
            user = None

        if user is not None and user.is_authenticated:
            # 用户已登录,在redis中保存
            redis_conn = get_redis_connection('cart')
            pl = redis_conn.pipeline()
            pl.hset('cart_%s' % user.id, sku_id, count)
            if selected:
                pl.sadd('cart_selected_%s' % user.id, sku_id)
            else:
                pl.srem('cart_selected_%s' % user.id, sku_id)
            pl.execute()
            return Response(serializer.data)
        else:
            # 用户未登录,在cookie中保存
            # 使用pickle序列化购物车数据,pickle操作的是bytes类型
            cart = request.COOKIES.get('cart')
            if cart is not None:
                cart = myjson.loads(cart)
            else:
                cart = {}

            cart[sku_id] = {
                'count': count,
                'selected': selected
            }
            cookie_cart = myjson.dumps(cart)

            response = Response(serializer.data)
            # 设置购物车的cookie
            # 需要设置有效期,否则是临时cookie
            response.set_cookie('cart', cookie_cart, max_age=constants.CART_COOKIE_EXPIRES)
            return response

    def delete(self, request):
        """
        删除购物车数据
        """
        serializer = CartDeleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        sku_id = serializer.validated_data['sku_id']

        try:
            user = request.user
        except Exception:
            user = None

        if user is not None and user.is_authenticated:
            # 用户已登录,在redis中保存
            redis_conn = get_redis_connection('cart')
            pl = redis_conn.pipeline()
            pl.hdel('cart_%s' % user.id, sku_id)
            pl.srem('cart_select_%s' % user.id, sku_id)
            pl.execute()
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            # 用户未登录,在cookie中保存
            response = Response(status=status.HTTP_204_NO_CONTENT)
            cart = request.COOKIES.get('cart')
            if cart is not None:
                cart = myjson.loads(cart)
                if sku_id in cart:
                    del cart[sku_id]
                    cookie_cart = myjson.dumps(cart)
                    # 设置购物车的cookie
                    # 需要设置有效期,否则是临时cookie
                    response.set_cookie('cart', cookie_cart, max_age=constants.CART_COOKIE_EXPIRES)
                return response


class CartSelectAllView(APIView):
    """
    购物车全选
    """
    def perform_authentication(self, request):
        pass

    def put(self, request):
        serializer = CartSelectAllSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        selected = serializer.validated_data['selected']

        try:
            user = request.user
        except Exception:
            user = None

        if user is not None and user.is_authenticated:
            redis_conn = get_redis_connection('cart')
            cart = redis_conn.hgetall('cart_%s' % user.id)
            sku_id_list = cart.keys()
            if selected:
                # 全选
                redis_conn.sadd('cart_selected_%s' % user.id, *sku_id_list)
            else:
                # 取消全选
                redis_conn.srem('car_selected_%s' % user.id, *sku_id_list)
            return Response({'message': 'OK'})
        else:
            cart = request.COOKIES.get('cart')

            response = Response({'message': 'OK'})

            if cart is not None:
                cart = myjson.loads(cart)
                for sku_id in cart:
                    cart[sku_id]['selected'] = selected
                cookie_cart = myjson.dumps(cart)
                # 设置购物车的cookie
                response.set_cookie('cart', cookie_cart, max_age=constants.CART_COOKIE_EXPIRES)

            return response

