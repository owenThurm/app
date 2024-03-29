from django.urls import path
from django.conf.urls import url
from . import views

urlpatterns = [
    url('promo/deactivateall', views.DeactivateAllAPIView.as_view()),
    url('promo/dequeue', views.DequeuePromoAccountAPIView.as_view()),
    url('promo/liking', views.LikingAPIView.as_view()),
    url('promo/review', views.SetProxyAPIView.as_view()),
    url('promo/disable', views.DisableAPIView.as_view()),
    url('promo/limited', views.PromoLimitedAPIView.as_view()),
    url('promo/commentfilter', views.PromoCommentFilterAPIView.as_view()),
    url('user/commentfilter', views.CommentFilterAPIView.as_view()),
    url('user/promoaccounts', views.UserPromoAccountsAPIView.as_view()),
    url('user/resetpassword', views.ResetPasswordAPIView.as_view()),
    url('user/customcomments', views.CustomCommentPoolAPIView.as_view()),
    url('user/setcustomcomments', views.SetCommentPoolAPIView.as_view()),
    url('user/authenticateemail', views.AuthenticateUserWithEmailValidation.as_view()),
    url('user/authenticate', views.AuthenticationAPIView.as_view()),
    url('user/getidentity', views.TokenIdentityAPIView.as_view()),
    url('user/forgotpassword', views.ForgotPasswordAPIView.as_view()),
    url('user/tokenresetpassword', views.ResetPasswordWithTokenAPIView.as_view()),
    url('user/statistics', views.UserStatisticsAPIView.as_view()),
    url('lambdacallback', views.LambdaCallbackAPIView.as_view()),
    url('user', views.UserAPIView.as_view()),
    url('promo', views.PromoAPIView.as_view()),
    url('deactivate', views.DeactivateAPIView.as_view()),
    url('activate', views.ActivateAPIView.as_view()),
]