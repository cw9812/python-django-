from django.conf.urls import url
from rest_framework.routers import DefaultRouter
from rest_framework_jwt.views import obtain_jwt_token

from meiduo.meiduo.apps.users import views

urlpatterns = [
    url(r'^usernames/(?P<username>\w{5,20})/count/$',
        views.UsernameCountView.as_view()),
    url(r'mobiles/(?P<mobile>1[3-9]\d{9}/count/$)',
        views.MobileCountView.as_view()),
    url(r'^users/$', views.UserView.as_view()),
    url(r'^user/$', views.UserDetailView.as_view()),
    url(r'^emails/$', views.EmailView.as_view()),
    url(r'^emails/verification/$', views.VerifyEmailView.as_view()),
    url('^browse_histories/$', views.UserBrowsingHistoryView.as_view()),
    url(r'^authorizations/$', views.UserAuthorizeView.as_view()),

]

router = DefaultRouter()
router.register('addresses', views.AddressViewSet, base_name='addresses')
urlpatterns += router.urls
