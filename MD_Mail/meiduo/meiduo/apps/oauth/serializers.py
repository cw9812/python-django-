from django_redis import get_redis_connection
from rest_framework import serializers

from meiduo.meiduo.apps.oauth.models import OAuthQQUser
from meiduo.meiduo.apps.oauth.qq_sdk import OAuthQQ
from meiduo.meiduo.apps.users.models import User
from meiduo.meiduo.utils import generate_jwt_token


class OAuthQQUserSerializer(serializers.ModelSerializer):
    """
    保存QQ用户序列化器
    """
    sms_code = serializers.CharField(label='短信验证码', write_only=True)
    access_token = serializers.CharField(label='操作凭证', write_only=True)
    token = serializers.CharField(read_only=True)
    mobile = serializers.RegexField(label='手机号', regex=r'^1[3-9]\d{9}$')

    class Meta:
        model = User
        fields = ('mobile', 'password', 'sms_code', 'access_token',
                  'id', 'username', 'token')

        extra_kwargs = {
            'username': {
                'read_only': True
            },
            'password': {
                'write_only': True,
                'min_length': 8,
                'max_length': 20,
                'error_messages': {
                    'min_length': '仅允许8-20个字符的密码',
                    'max_length': '仅允许8-20个字符的密码'
                }
            }
        }

    def validate(self, attrs):
        # 检验access_token
        access_token = attrs['access_token']

        openid = OAuthQQ.check_save_user_token(access_token)
        if not openid:
            raise serializers.ValidationError('无效的的access_token')

        attrs['openid'] = openid
        # 检验短信验证码
        mobile = attrs['mobile']
        sms_code = attrs['sms_code']
        redis_conn = get_redis_connection('sms_code')
        real_sms_code = redis_conn.get('sms_code_' + mobile)
        if real_sms_code.decode() != sms_code:
            raise serializers.ValidationError('短信验证码错误')

        # 如果用户存在,检查用户密码
        try:
            user = User.objects.get(mobile=mobile)
        except User.DoesNotExist:
            pass
        else:
            password = attrs['password']
            if not user.check_password(password):
                raise serializers.ValidationError('密码错误')
            attrs['user'] = user
        return attrs

    def create(self, validated_data):
        print('99')
        openid = validated_data['openid']
        user = validated_data.get('user')
        mobile = validated_data['mobile']
        password = validated_data['password']
        print(user)

        if not user:
            # 如果用户不存在,创建用户,绑定openid
            user = User.objects.create_user(username=mobile, mobile=mobile, password=password)

        OAuthQQUser.objects.create(user=user, openid=openid)
        # 签发jwt token
        user.token = generate_jwt_token.generate_jwt_token(user)
        return user
