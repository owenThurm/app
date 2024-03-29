from django.shortcuts import render
from rest_framework import views, status
from rest_framework.response import Response
from .services.promo_account_service import PromoAccountService
from .services.user_service import UserService
from . import models
from django.contrib.auth import authenticate
from . import serializers
from .utils import add_to_queue
from datetime import datetime
import pytz
import os
import smtplib

promo_account_service = PromoAccountService()
user_service = UserService()

# Create your views here.
class UserAPIView(views.APIView):
  """APIView for getting and creating Users"""

  serializer_class = serializers.UserSerializer

  def get(self, request, format=None):
    try:
      user_username = request.query_params['username']
      if(user_username != None):
        try:
          user_data = user_service.get_user_data(user_username)
        except Exception as e:
          return Response({
            "message": "No user corresponding to username: " + user_username,
          }, status=status.HTTP_404_NOT_FOUND)
        return Response({
          "message": "successfully got user",
          "user_data": user_data
        }, status=status.HTTP_200_OK)
    except Exception as e:
      pass
    try:
      user_email = request.query_params['email']
      if(user_email != None):
        try:
          user_username = user_service.get_username_from_email(user_email)
          user_data = user_service.get_user_data(user_username)
        except Exception as e:
          return Response({
            "message": "No user corresponding to email: " + user_email,
          }, status=status.HTTP_404_NOT_FOUND)
        return Response({
          "message": "successfully got user",
          "user_data": user_data
        }, status=status.HTTP_200_OK)
    except Exception as e:
      pass
    users = user_service.get_user_set()
    return Response(users, status=status.HTTP_200_OK)

  def post(self, request, format=None):
    '''
      Used to create a user. When creating a user,
      Sends an email to the given address that contains a link
      to the login page with the email validation token as a
      query parameter.
    '''
    try:
      request.data['email'] = request.data['email'].lower()
    except Exception as e:
      pass
    user_serializer = serializers.UserSerializer(data=request.data)

    if user_serializer.is_valid():
      user_email = request.data['email']
      user_serializer.save()
      auth_token = user_service.generate_token(user_serializer.data['username'])
      # Send email validation email
      user_service.send_register_email_validation_email(user_email)
      return Response({
        'message': 'saved', 'data': user_serializer.data,
        'token': auth_token
      }, status=status.HTTP_200_OK)
    else:
      return Response({
        "message": "invalid user",
        "data": user_serializer.data,
        "errors": user_serializer.errors,
      }, status=status.HTTP_200_OK)

  def delete(self, request, format=None):
    '''
      Used to delete Users

      expects the following body:

      {
        "user_username": "owenthurm"
      }
    '''

    delete_user_seralizer = serializers.UserUsernameSerializer(data=request.data)

    if delete_user_seralizer.is_valid():
      user_username = request.data['user_username']
      try:
        user_service.delete_user(user_username)
        return Response({
          "message": "deleted user",
          "data": delete_user_seralizer.data,
        }, status=status.HTTP_200_OK)
      except Exception as e:
        return Response({
          "message": "user with given username not found",
          "data": delete_user_seralizer.data,
        }, status=status.HTTP_404_NOT_FOUND)
    else:
      return Response({
        "message": "invalid",
        "data": delete_user_seralizer.data,
        "errors": delete_user_seralizer.errors,
      }, status=status.HTTP_400_BAD_REQUEST)

class PromoAPIView(views.APIView):
  """APIView for Promo Accounts"""
  serializer_class = serializers.GetPromoSerializer

  def get(self, request, format=None):
    try:
      promo_username = request.query_params['username']
      if(promo_username != None):
        try:
          promo_account_data = promo_account_service.get_promo_account_data(promo_username)
          return Response({
            "message": "promo data",
            "data": promo_account_data
          }, status=status.HTTP_200_OK)
        except Exception as e:
          return Response({
            "message": "No promo account corresponding to username: " + promo_username,
          }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
      promo_set_data = promo_account_service.get_promo_set()
    return Response(promo_set_data, status=status.HTTP_200_OK)

  def post(self, request, format=None):
    '''post a promo and set it for review'''
    '''
    Expects the following format:

    {
      promo_username: "promo account username",
      promo_password: "promo account password",
      promo_targets: ["promo target account1", "target account2", ...],
      user: "Growth Automation user username who owns promo account"
    }
    '''
    try:
      user_username = request.data['user']
    except Exception as e:
      return Response({
        "message": "no user provided",
        "data": request.data,
      }, status=status.HTTP_400_BAD_REQUEST)
    request.data['user'] = models.User.objects.get(username=user_username).id
    promo_serializer = serializers.PostPromoSerializer(data=request.data)

    if promo_serializer.is_valid():
      promo_serializer.save()
      return Response({
        "message": "saved",
        "data": promo_serializer.data
      }, status=status.HTTP_200_OK)
    else:
      return Response({
        "message": "invalid",
        "data": promo_serializer.data,
        "errors": promo_serializer.errors
      }, status=status.HTTP_400_BAD_REQUEST)

  def put(self, request, format=None):
    '''update a promo account and set it for review'''

    '''
      Expects the following body:

      {
        "old_promo_username": "upcomingstreetwearfashion",
        "new_promo_username": "genuineaesthetic",
        "new_promo_password": "password123",
        "new_promo_targets": "riotsociety",
      }
    '''

    update_promo_serializer = serializers.UpdatePromoSerializer(data=request.data)

    if update_promo_serializer.is_valid():
      old_promo_username = request.data['old_promo_username']
      new_promo_username = request.data['new_promo_username']
      new_promo_password = request.data['new_promo_password']
      new_promo_targets = request.data['new_promo_targets']
      try:
        promo_account_service.update_promo_account(old_promo_username, new_promo_username,
                                                  new_promo_password, new_promo_targets)
        return Response({
          "message": "updated",
          "data": update_promo_serializer.data
        }, status=status.HTTP_200_OK)
      except Exception as e:
        return Response({
          "message": "no promo account corresponding to old promo username",
          "data": old_promo_username
        }, status=status.HTTP_404_NOT_FOUND)
    else:
      return Response({
        "message": "invalid",
        "data": update_promo_serializer.data,
        "errors": update_promo_serializer.errors,
      }, status=status.HTTP_400_BAD_REQUEST)

  def delete(self, request, format=None):
    '''
      deletes a promo account

      expects the following body:

      {
        "promo_username": "upcomingstreetwearfashion"
      }
    '''

    delete_promo_serializer = serializers.PromoUsernameSerializer(data=request.data)

    if delete_promo_serializer.is_valid():
      promo_username = request.data['promo_username']
      try:
        promo_account_service.delete_promo_account(promo_username)
        return Response({
          "message": "deleted promo account",
          "data": delete_promo_serializer.data,
        }, status=status.HTTP_200_OK)
      except Exception as e:
        return Response({
          "message": "couldn't find promo account corresponding to username",
          "data": delete_promo_serializer.data,
        }, status=status.HTTP_404_NOT_FOUND)
    else:
      return Response({
        "message": "deleted promo accounts",
        "data": delete_promo_serializer.data,
        "errors": delete_promo_serializer.errors,
      }, status=status.HTTP_400_BAD_REQUEST)

class AuthenticationAPIView(views.APIView):
  '''An APIView for authenticating users'''

  serializer_class = serializers.AuthenticationSerializer

  def post(self, request, format=None):
    '''
      post email and password in body
      returns true if authenticated, false if not.

      Expects the following body:

      {
        'email': 'owen.p.thurm@gmail.com',
        'password': 'Password123',
      }
    '''

    auth_serializer = serializers.AuthenticationSerializer(data=request.data)

    if auth_serializer.is_valid():
      # authenticate
      user_email = auth_serializer.data['email']
      user_password = auth_serializer.data['password']
      user_username = user_service.authenticate_user(user_email, user_password)
      if user_username is None:
        # did not pass authentication
        return Response({
          "message": "invalid credentials",
          "authenticated": False
        }, status=status.HTTP_200_OK)
      else:
        auth_token = user_service.generate_token(user_username)
        return Response({
          "message": "successfully authenticated",
          "authenticated": True,
          "data": user_username,
          "token": auth_token,
        }, status=status.HTTP_200_OK)
    else:
      return Response({
        "message": "invalid",
        "data": auth_serializer.data,
        "errors": auth_serializer.errors,
      }, status=status.HTTP_400_BAD_REQUEST)

class TokenIdentityAPIView(views.APIView):
  '''Used to get the identity corresponding to a given token'''

  def post(self, request, format=None):
    '''
      Expects the following body:

      {
        token: 'akdjfhaadf434...'
      }
    '''

    token_serializer = serializers.TokenSerializer(data=request.data)

    if token_serializer.is_valid():
      user_token = token_serializer.data['token']
      try:
        (user_username, user_email)  = user_service.get_identity_from_token(user_token)
      except Exception as e:
        return Response({
          "message": "no valid token matching given token",
          "data": token_serializer.data,
        }, status=status.HTTP_200_OK)
      return Response({
        "message": "user identity",
        "username": user_username,
        "email": user_email
      }, status=status.HTTP_200_OK)
    else:
      return Response({
        "message": "invalid",
        "data": token_serializer.data,
        "errors": token_serializer._errors
      }, status=status.HTTP_400_BAD_REQUEST)

class ActivateAPIView(views.APIView):
  '''An APIView for activating promo accounts'''

  class_serializers = serializers.PromoUsernameSerializer

  def post(self, request, format=None):
    '''
      expects the following body:

      {
        "promo_username": "upcomingstreetwearfashion"
      }
    '''

    activation_serializer = serializers.PromoUsernameSerializer(data=request.data)

    if activation_serializer.is_valid():
      try:
        promo_username = request.data['promo_username']
        promo_is_disabled = promo_account_service.promo_is_disabled(promo_username)
        promo_is_under_review = promo_account_service.promo_is_under_review(promo_username)
        promo_is_queued = promo_account_service.promo_is_queued(promo_username)
      except Exception as e:
        return Response({
          "message": "can't find promo account corresponding to promo username",
          "data": promo_username,
        }, status=status.HTTP_404_NOT_FOUND)
      if promo_is_disabled:
        return Response({
          "message": "promo is disabled",
          "data": activation_serializer.data,
        }, status=status.HTTP_200_OK)
      if promo_is_under_review:
        return Response({
          "message": "promo is under review",
          "data": activation_serializer.data
        }, status=status.HTTP_200_OK)
      if promo_is_queued:
        promo_account_service.activate_promo_account(promo_username)
        return Response({
          "message": "activated",
          "data": activation_serializer.data
        }, status=status.HTTP_200_OK)
      else:
        promo_account_service.activate_and_queue_promo_account(promo_username)
        return Response({
          "message": "activated and queued",
          "data": activation_serializer.data
        }, status=status.HTTP_200_OK)
    else:
      return Response({
        "message": "invalid",
        "data": activation_serializer.data,
        "errors": activation_serializer.errors,
      }, status=status.HTTP_400_BAD_REQUEST)

class DeactivateAPIView(views.APIView):
  '''An APIView for deactivating promo accounts'''

  class_serializer = serializers.PromoUsernameSerializer

  def post(self, request, format=None):
    '''expects a promo_username in the body'''
    deactivation_serializer = serializers.PromoUsernameSerializer(data=request.data)

    if deactivation_serializer.is_valid():
      promo_username = request.data['promo_username']
      try:
        promo_account_service.deactivate_promo_account(promo_username)
      except Exception as e:
        return Response({
          "message": "no promo corresponding to promo username",
          "data": promo_username
        }, status=status.HTTP_404_NOT_FOUND)

      return Response({
        "message": "deactivated",
        "data": deactivation_serializer.data
      }, status=status.HTTP_200_OK)
    else:
      return Response({
        "message": "invalid",
        "data": deactivation_serializer.data
      }, status=status.HTTP_400_BAD_REQUEST)

class DeactivateAllAPIView(views.APIView):
  '''Used to deactivate all promo accounts'''

  def post(self, request, format=None):
    '''expects no body'''
    promo_account_service.deactivate_all_promo_accounts()
    return Response({
      "message": "Deactivated all promo accounts"
    }, status=status.HTTP_200_OK)

class DequeuePromoAccountAPIView(views.APIView):
  '''Take a promo account out of the commenting queue'''

  def post(self, request, format=None):
    '''
        expects a promo_username in the body

        {
          "promo_username": "genuineaesthetic"
        }
    '''


    dequeue_serializer = serializers.PromoUsernameSerializer(data=request.data)

    if dequeue_serializer.is_valid():

      dequeued_promo_username = request.data.get('promo_username')
      promo_account_service.dequeue_promo_account(dequeued_promo_username)

      return Response({
        "message": "Dequeued account",
        "data": dequeued_promo_username
      }, status=status.HTTP_200_OK)

    else:
      return Response({
        "message": "invalid",
        "data": dequeue_serializer.data
      }, status=status.HTTP_400_BAD_REQUEST)


class SetProxyAPIView(views.APIView):
  '''Sets the Proxy for an account'''

  class_serializer = serializers.AddProxySerializer

  def post(self, request, format=None):
    '''
    expects the following body format:

    {
      "promo_username": "promoaccountusername1",
      "proxy": "127.323.543.564.788..."
    }
    '''

    proxy_review_serializer = serializers.AddProxySerializer(data=request.data)

    if proxy_review_serializer.is_valid():

      try:
        reveiwing_promo_account = models.Promo_Account.objects.get(
          promo_username=proxy_review_serializer.data['promo_username'])
      except Exception as e:
        return Response({
          "message": "invalid",
          "data": "no promo account corresponding to name: "
          + proxy_review_serializer.data['promo_username']
        }, status=status.HTTP_404_NOT_FOUND)

      for account in models.Promo_Account.objects.all():
        if account.proxy == proxy_review_serializer.data['proxy']:
          return Response({
            "message": "proxy already in use",
            "data": "proxy being used by promo: " + account.promo_username
          }, status=status.HTTP_206_PARTIAL_CONTENT)
      reveiwing_promo_account.proxy = proxy_review_serializer.data['proxy']
      reveiwing_promo_account.under_review = False
      reveiwing_promo_account.save()
      return Response({
        "message": "reviewed and updated proxy",
        "data": proxy_review_serializer.data
      }, status=status.HTTP_200_OK)
    else:
      return Response({
        "message": "invalid",
        "data": proxy_review_serializer.data
      }, status=status.HTTP_400_BAD_REQUEST)

class UserPromoAccountsAPIView(views.APIView):
  '''Used to get a list of the promo accounts associated with a user'''

  class_serializer = serializers.GetUserPromoAccountsSerializer

  def post(self, request, format=None):
    '''
    Expects the following body format
    {
      "username": "genuine apparel growth user username"
    }
    '''
    user_serializer = serializers.GetUserPromoAccountsSerializer(data=request.data)

    if user_serializer.is_valid():
      try:
        user = models.User.objects.get(username=user_serializer.data['username'])
      except Exception as e:
        return Response({
          "message": "invalid",
          "data": "No user corresponding to username: " + user_serializer.data['username']
        }, status=status.HTTP_404_NOT_FOUND)
      promo_accounts = []

      for promo_account in user.promo_account_set.all():
        promo_accounts.append(str(promo_account))

      return Response({
        "message": "promo accounts",
        "data": promo_accounts
      }, status=status.HTTP_200_OK)
    else:
      return Response({
        "message": "invalid",
        "data": user_serializer.data
      }, status=status.HTTP_400_BAD_REQUEST)

class ResetPasswordAPIView(views.APIView):
  '''Used to reset the password for a growth automation user'''

  class_serializer = serializers.ResetPasswordSerializer

  def post(self, request, format=None):
    '''
    Expects the following body format

    {
      "username": "owenthurm",
      "new_password": "password123"
    }
    '''

    reset_password_serializer = serializers.ResetPasswordSerializer(data=request.data)

    if reset_password_serializer.is_valid():
      user_manager = models.UserManager()
      user_username = request.data['username']
      new_password = request.data['new_password']
      try:
        user_manager.set_password(user_username, new_password)
      except Exception as e:
        print(e)
        return Response({
          "message": "Issue changing password"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
      return Response({
        "message": "password updated",
        "data": user_username
      }, status=status.HTTP_200_OK)
    else:
      return Response({
        "message": "invalid",
        "data": reset_password_serializer.data
      }, status=status.HTTP_400_BAD_REQUEST)

class SetCommentPoolAPIView(views.APIView):
  '''
    Used to set the comment pool for an account
    -- either custom pool or default pool
  '''

  serializer_class = serializers.SetCommentPoolSerializer

  def post(self, request, format=None):
    '''
      expects the following body:

      {
        "user_username": "upcomingstreetwearfashion",
        "using_custom_comments": false
      }
    '''

    update_comment_pool_serializer = serializers.SetCommentPoolSerializer(data=request.data)

    if update_comment_pool_serializer.is_valid():
      user_username = request.data['user_username']
      using_custom_comments = request.data['using_custom_comments']
      if not user_service.user_is_custom_comment_eligible(user_username) and using_custom_comments:
        return Response({
          "message": "user is not eligible for custom comments",
          "data": update_comment_pool_serializer.data
        }, status=status.HTTP_206_PARTIAL_CONTENT)
      try:
        user_service.update_user_comment_pool_setting(user_username, using_custom_comments)
      except Exception as e:
        return Response({
          "message": "Couldn't find a user corresponding to username",
          "data": update_comment_pool_serializer.data
        }, status=status.HTTP_404_NOT_FOUND)
      return Response({
        "message": "updated",
        "data": update_comment_pool_serializer.data
      }, status=status.HTTP_200_OK)
    else:
      return Response({
        "message": "invalid",
        "data": update_comment_pool_serializer.data
      }, status=status.HTTP_400_BAD_REQUEST)

class CustomCommentPoolAPIView(views.APIView):
  '''
    Used to add a list of custom comments to a
    user's custom comment pool
  '''

  def get_queryset(self):
    return models.CustomComment.objects.all()

  def get(self, request, format=None):
    '''
      Used to get a single user's custom comment pool
      if a user's username is passed in the query params
      and used to get all custom comments if not.

      expects ?user=owenthurm

      in query params
    '''
    try:
      user_username = request.query_params['user']
      if user_username != None:
        try:
          custom_comments = user_service.get_user_custom_comment_pool(user_username)
          custom_comments_serializer = serializers.GetCustomCommentSerializer(custom_comments, many=True)

          return Response({
            "message": user_username + "'s comment pool",
            "data": custom_comments_serializer.data
          }, status=status.HTTP_200_OK)
        except Exception as e:
          return Response({
            "message": "could not find comment pool corresponding to user",
            "data": user_username
          }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
      custom_comments = self.get_queryset()
      custom_comments_serializer = serializers.GetCustomCommentSerializer(custom_comments, many=True)
      return Response(custom_comments_serializer.data, status=status.HTTP_200_OK)


  class_serializer = serializers.AddCustomCommentsSerializer

  def post(self, request, format=None):
    '''
      expects the following body:

      {
        "user_username": "owenthurm"
        "new_custom_comments": ["hey what's good, shoot me a dm when you can",
                                "what's up, dm me whenever you can", ...]
      }
    '''

    new_comments_serializer = serializers.AddCustomCommentsSerializer(data=request.data)

    if new_comments_serializer.is_valid():
      user_username = request.data['user_username']
      new_custom_comments = request.data['new_custom_comments']
      comments_are_unique = user_service.comments_are_unique(user_username, new_custom_comments)
      if not comments_are_unique:
        duplicate_comment_text = user_service.get_duplicate_comment(user_username, new_custom_comments)
        return Response({
          "message": "Comments are not unique",
          "data": duplicate_comment_text
        }, status=status.HTTP_200_OK)
      try:
        user_service.add_to_user_custom_comment_pool(user_username, new_custom_comments)
      except Exception as e:
        return Response({
          "message": "Couldn't find a user corresponding to username",
          "data": new_comments_serializer.data
        }, status=status.HTTP_404_NOT_FOUND)
      return Response({
        "message": "updated",
        "data": new_comments_serializer.data
        }, status=status.HTTP_200_OK)
    else:
      return Response({
        "message": "invalid",
        "data": new_comments_serializer.data
      }, status=status.HTTP_400_BAD_REQUEST)

  def delete(self, request, format=None):
    '''
      expects the following body:

      {
        "user_username": "owenthurm",
        "custom_comment_text": "Hey what's up! Shoot us a dm when you can!"
      }
    '''

    delete_custom_comment_serializer = serializers.DeleteCustomCommentSerializer(data=request.data)

    if delete_custom_comment_serializer.is_valid():
      user_username = request.data['user_username']
      custom_comment_text = request.data['custom_comment_text']
      try:
        user_service.delete_custom_comment(user_username, custom_comment_text)
        if not user_service.user_is_custom_comment_eligible(user_username):
          user_service.update_user_comment_pool_setting(user_username, False)
      except Exception as e:
        return Response({
          "message": "Couldn't locate custom comment with that text for given user",
          "data": delete_custom_comment_serializer.data
        }, status=status.HTTP_404_NOT_FOUND)
      return Response({
        "message": "deleted",
        "data": delete_custom_comment_serializer.data
        }, status=status.HTTP_200_OK)
    else:
      return Response({
        "message": "invalid",
        "data": delete_custom_comment_serializer.data
      }, status=status.HTTP_400_BAD_REQUEST)

  def put(self, request, format=None):
    '''
      expects the following body format:

      {
        "user_username": "owenthurm",
        "old_custom_comment_text": "",
        "new_custom_comment_text": ""
      }
    '''

    update_custom_comment_serializer = serializers.UpdateCustomCommentSerializer(data=request.data)

    if update_custom_comment_serializer.is_valid():
      user_username = request.data['user_username']
      old_custom_comment_text = request.data['old_custom_comment_text']
      new_custom_comment_text = request.data['new_custom_comment_text']
      try:
        user_service.update_custom_comment_text(user_username, old_custom_comment_text,
                                                          new_custom_comment_text)
      except Exception as e:
        return Response({
          "message": "Couldn't find comment to update from given user",
          "data": update_custom_comment_serializer.data
        }, status=status.HTTP_404_NOT_FOUND)
      return Response({
        "message": "updated",
        "data": update_custom_comment_serializer.data
      }, status=status.HTTP_200_OK)
    else:
      return Response({
        "message": "invalid",
        "data": update_custom_comment_serializer.data
      }, status=status.HTTP_400_BAD_REQUEST)

class ForgotPasswordAPIView(views.APIView):

  def post(self, request, format=None):
    '''
      Expects the following body:

      {
        "email": "owen.p.thurm@gmail.com"
      }
    '''

    forgot_password_serializer = serializers.ForgotPasswordSerializer(data=request.data)

    if forgot_password_serializer.is_valid():
      email = request.data["email"]
      try:
        user_username = user_service.get_user_username_from_email(email)
      except Exception as e:
        return Response({
          "message": "No user corresponding to email",
          "data": forgot_password_serializer.data
        })
      # generate a reset password token for that user
      reset_password_token = user_service.generate_email_validation_token_for_user(user_username)
      reset_password_url = 'https://growthautomation.netlify.com/resetpassword/reset?token='+reset_password_token
      # send an email with reset password instructions as well as a link to
      # https://growthautomation.netlify.com/resetpassword/reset?token=adfadfadfasdfadfl
      with smtplib.SMTP('smtp.gmail.com', 587) as smtp:
        smtp.ehlo()
        smtp.starttls()
        smtp.ehlo()

        smtp.login('genuineapparelsuccess@gmail.com', 'ntdqiwzyasuvpruo')

        subject = 'Growth Automation Reset Password'
        body = f'Follow this link to reset your password!\n{reset_password_url}'

        msg = f'Subject: {subject}\n\n{body}'

        smtp.sendmail('genuineapparelsuccess@gmail.com', email, msg)

      return Response({
        "message": "Reset Password Email Sent",
        "data": forgot_password_serializer.data
      }, status=status.HTTP_200_OK)
    else:
      return Response({
        "message": "invalid",
        "data": forgot_password_serializer.data,
        "errors": forgot_password_serializer.errors
      }, status=status.HTTP_400_BAD_REQUEST)

class ResetPasswordWithTokenAPIView(views.APIView):
  '''Handles requests to reset a user's password with EmailValidationToken authentication'''

  def get(self, request, format=None):
    '''Returns the user username associated with a reset password token'''

    '''
      Expects the following query parameters
    '''

    try:
      reset_password_token = request.query_params['reset_password_token']
      try:
        user_username = user_service.get_user_username_from_email_validation_token(reset_password_token)
        return Response({
          "message": "user username",
          "data": user_username
        }, status=status.HTTP_200_OK)
      except Exception as e:
        return Response({
          "message": "no user corresponding to reset password token"
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
      return Response({
        "message": "invalid",
        "data": "must include a reset password token"
      }, status=status.HTTP_400_BAD_REQUEST)


  def post(self, request, format=None):
    '''
      Expects the following body:

      {
        "new_password": "password123",
        "reset_password_token": "adfadskjhfalkdh..."
      }
    '''

    reset_password_serializer = serializers.ResetPasswordAuthenticatedSerializer(data=request.data)

    if reset_password_serializer.is_valid():
      new_password = request.data['new_password']
      reset_password_token = request.data['reset_password_token']
      try:
        is_valid_reset_password_token = user_service.email_validation_token_is_valid(reset_password_token)
      except Exception as e:
        return Response({
          "message": "token doesn't exist or has already been used"
        }, status=status.HTTP_404_NOT_FOUND)
      if is_valid_reset_password_token:
        user_username = user_service.get_user_username_from_email_validation_token(reset_password_token)
        user_service.reset_user_password(user_username, new_password)
        user_service.delete_email_validation_token(reset_password_token)
        return Response({
          "message": "password reset",
          "data": reset_password_serializer.data
        }, status=status.HTTP_200_OK)
      else:
        return Response({
          "message": "Token is invalid",
          "data": reset_password_serializer.data
        }, status=status.HTTP_400_BAD_REQUEST)
    else:
      return Response({
        "message": "invalid",
        "data": reset_password_serializer.data,
        "errors": reset_password_serializer.errors
      }, status=status.HTTP_400_BAD_REQUEST)

class UserStatisticsAPIView(views.APIView):
  ''' Used for getting the comment statistics associated with a user '''

  def get(self, request, format=None):
    '''
      Returns the comment statistics related to a user

      Expects the following query params:

      user=owenthurm
    '''

    try:
      user_username = request.query_params['user']
      try:
        user_stats = user_service.get_user_stats(user_username)
        return Response({
          "message": "statistics for " + user_username,
          "data": user_stats
        }, status=status.HTTP_200_OK)
      except Exception as e:
        return Response({
          "message": "no user corresponding to username",
          "data": user_username
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
      return Response({
        "message": "invalid",
        "data": "No user provided"
      }, status=status.HTTP_400_BAD_REQUEST)

class LikingAPIView(views.APIView):
  '''Used to get/set information about promo account liking'''

  def get(self, request, format=None):
    '''
      Used to get the status of liking for a promo account

      expects the following query params:

      ?promo_username=upcomingstreetwearfashion
    '''
    try:
      promo_username = request.query_params['promo_username']
      try:
        is_liking = promo_account_service.promo_account_is_liking(promo_username)
        return Response({
          "message": "promo account liking status",
          "data": is_liking
        }, status=status.HTTP_200_OK)
      except Exception as e:
        return Response({
          "message": "no promo account corresponds to promo username",
          "data":  promo_username
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
      return Response({
        "message": "invalid",
        "data": "no promo_username provided"
      }, status=status.HTTP_400_BAD_REQUEST)

  def put(self, request, format=None):
    '''
      Used to set the liking status of a promo account

      Expects the following body:

      {
        "promo_username": "upcomingstreetwearfashion",
        "is_liking": False
      }
    '''

    toggle_is_liking_serializer = serializers.LikingSerializer(data=request.data)

    if toggle_is_liking_serializer.is_valid():
      promo_username = request.data['promo_username']
      is_liking = request.data['is_liking']
      try:
        promo_account_service.set_promo_is_liking(promo_username, is_liking)
        return Response({
          "message": "promo liking status set",
          "data": is_liking
        }, status=status.HTTP_200_OK)
      except Exception as e:
        return Response({
          "message": "invalid",
          "data": "no promo account corresponds to " + promo_username
        }, status=status.HTTP_404_NOT_FOUND)
    else:
      return Response({
        "message": "invalid",
        "data": toggle_is_liking_serializer.data,
        "errors": toggle_is_liking_serializer.errors
      }, status=status.HTTP_400_BAD_REQUEST)

class DisableAPIView(views.APIView):
  '''Used to disable an account (still queued but can't be activated)'''

  def put(self, request, format=None):
    '''
      Updates the disabled status of an account.

      Expects the following body:

      {
        "promo_username": "upcomingstreetwearfashion",
        "is_disabled": True
      }
    '''

    set_disabled_status_serializer = serializers.DisabledSerializer(
      data=request.data
    )

    if set_disabled_status_serializer.is_valid():
      promo_username = request.data['promo_username']
      is_disabled = request.data['is_disabled']
      under_review = promo_account_service.promo_is_under_review(promo_username)
      if under_review:
        return Response({
          "message": "under review",
          "data": set_disabled_status_serializer.data
        }, status=status.HTTP_200_OK)
      try:
        promo_account_service.update_promo_disabled_status(promo_username, is_disabled)
        if is_disabled:
          promo_account_service.deactivate_promo_account(promo_username)
      except Exception as e:
        return Response({
          "message": "no promo account corresponds to " + promo_username,
          "data": set_disabled_status_serializer.data,
        }, status=status.HTTP_404_NOT_FOUND)
      return Response({
        "message": "updated promo account disabled status",
        "data": is_disabled
      }, status=status.HTTP_200_OK)
    else:
      return Response({
        "message": "invalid",
        "data": set_disabled_status_serializer.data,
        "errors": set_disabled_status_serializer.errors,
      }, status=status.HTTP_400_BAD_REQUEST)

class CommentFilterAPIView(views.APIView):
  '''An APIView for comment filters'''

  def post(self, request, format=None):
    '''
      Used to create comment filter for a user

      expects the following body

      {
        "user_username": "owenthurm"
      }
    '''

    create_comment_filter_serializer = serializers.UserUsernameSerializer(data=request.data)

    if create_comment_filter_serializer.is_valid():
      #create default comment filter for user
      user_username = request.data['user_username']
      try:
        user_service.create_default_comment_filter_for_user(user_username)
      except Exception as e:
        return Response({
          "message": "no user corresponding to username",
          "data": create_comment_filter_serializer.data,
        }, status=status.HTTP_404_NOT_FOUND)
      return Response({
        "message": "created default comment filter for user",
        "data": create_comment_filter_serializer.data,
      }, status=status.HTTP_200_OK)
    else:
      return Response({
        "message": "invalid",
        "data": create_comment_filter_serializer.data,
        "errors": create_comment_filter_serializer.errors,
      }, status=status.HTTP_400_BAD_REQUEST)

  def put(self, request, format=None):
    '''
      Used to update the comment filter for a user

      expects the following body

      {
        "user_username": "owenthurm",
        "comment_filter": {
          account_min_followers: 10,
          account_max_followers: 10000,
          account_min_number_following: 10,
          account_max_number_following: 5000,
          account_description_avoided_key_phrases: ["kill", "hate", "he died"],
          post_min_number_of_comments: 0,
          post_max_number_of_comments: 100,
          post_min_number_of_likes: 5,
          post_max_number_of_likes: 12000,
          post_description_avoided_key_phrases: ["something terrible happened", "dead"],
        }
      }
    '''

    comment_filter_serializer = serializers.UserCommentFilterSerializer(data=request.data)

    if comment_filter_serializer.is_valid():
      #update comment filter
      user_username = request.data['user_username']
      new_comment_filter = request.data['comment_filter']
      try:
        user_service.update_user_comment_filter(user_username, new_comment_filter)
      except Exception as e:
        return Response({
          "message": "no user corresponding to username",
          "data": comment_filter_serializer.data,
        }, status=status.HTTP_404_NOT_FOUND)
      return Response({
        "message": "updated user's comment filter",
        "data": comment_filter_serializer.data,
      }, status=status.HTTP_200_OK)
    else:
      return Response({
        "message": "invalid",
        "data": comment_filter_serializer.data,
        "errors": comment_filter_serializer.errors,
      }, status=status.HTTP_400_BAD_REQUEST)

class LambdaCallbackAPIView(views.APIView):
  '''An APIView for the lambda to call back after a comment round is over'''

  def post(self, request, format=None):
    '''
      Used to add the newly commented on accounts to the user,
      set the target accounts list to the newly rotated list,
      and set the is_liking status of the promo.

      expects the following body:

      {
        "promo_username": "upcomingstreetwearfashion",
        "promo_is_liking": True,
        "commented_on_accounts": ["somerandomcommentedonaccount", "another one", ...],
        "rotated_target_accounts_list": ["riotsociety", "nike", "adidas", ...],
        "failed_last_comment_round": False,
        "promo_account_limited": False,
      }
    '''

    lambda_callback_serializer = serializers.LambdaCallbackSerializer(data=request.data)

    if lambda_callback_serializer.is_valid():
      promo_username = request.data['promo_username']
      promo_is_liking = request.data['promo_is_liking']
      commented_on_accounts = request.data['commented_on_accounts']
      rotated_target_accounts_list = request.data['rotated_target_accounts_list']
      try:
        failed_last_comment_round = request.data['failed_last_comment_round']
        promo_account_limited = request.data['promo_account_limited']
        promo_account_service.update_last_comment_round_status(promo_username, failed_last_comment_round)
        if promo_account_limited:
          promo_account_service.disable_promo_account(promo_username)
          promo_account_service.decrement_promo_comment_level(promo_username)
          # sets the increment comment level threshold delta to
          # be 1000 if it's currently less than 1000
          promo_account_service.increase_increment_comment_level_threshold_delta(promo_username)
          promo_account_service.increase_increment_comment_level_threshold(promo_username)
        promo_account_owner_username = promo_account_service.get_promo_account_owner_username(promo_username)
        #add commented accounts to user commented on accounts
        user_service.add_commented_on_accounts(promo_account_owner_username, promo_username, commented_on_accounts)
        promo_account_service.set_promo_is_liking(promo_username, promo_is_liking)
        #set the target accounts list to the new rotated one
        promo_account_service.set_promo_targeting_list(promo_username, rotated_target_accounts_list)
        # subtract number of comments in the list comming in from promo_account.comments_until_sleep
        promo_account_service.subtract_comments_from_comments_until_sleep(promo_username, commented_on_accounts)
        #update the promo comment level (no-op if haven't reached the increment comment number)
        promo_account_service.update_promo_comment_level(promo_username)
        return Response({
          "message": "successfully logged promo comment round data",
          "data": lambda_callback_serializer.data,
        }, status=status.HTTP_200_OK)
      except Exception as e:
        return Response({
          "message": "no promo account corresponding to promo username",
          "data": lambda_callback_serializer.data,
        }, status=status.HTTP_404_NOT_FOUND)
    else:
      return Response({
        "message": "invalid",
        "data": lambda_callback_serializer.data,
        "errors": lambda_callback_serializer.errors,
      }, status=status.HTTP_400_BAD_REQUEST)

class PromoLimitedAPIView(views.APIView):
  '''Used to handle promo accounts being limited by Instagram'''

  def post(self, request, format=None):
    '''
      * Disables the promo account until further notice
      * Sets the comment level of the promo down one
      * Increases the number of comments threshold to
        increment the comment level at
      * Increases the delta that the number of comments
        threshold to increment the comment level increases by

      expects the following body:

      {
        "promo_username": "upcomingstreetwearfashion"
      }
    '''

    promo_limited_serializer = serializers.PromoUsernameSerializer(data=request.data)

    if promo_limited_serializer.is_valid():
      promo_username = request.data['promo_username']
      try:
        promo_account_service.disable_promo_account(promo_username)
        promo_account_service.decrement_promo_comment_level(promo_username)
        # sets the increment comment level threshold delta to
        # be 1000 if it's currently less than 1000
        promo_account_service.increase_increment_comment_level_threshold_delta(promo_username)
        promo_account_service.increase_increment_comment_level_threshold(promo_username)
      except Exception as e:
        return Response({
          "message": "no promo account corresponding to given promo username",
          "data": promo_limited_serializer.data,
        }, status=status.HTTP_404_NOT_FOUND)
      return Response({
        "message": "disabled and slowed promo comment scaling",
        "data": promo_limited_serializer.data,
      }, status=status.HTTP_200_OK)
    else:
      return Response({
        "message": "invalid",
        "data": promo_limited_serializer.data,
        "errors": promo_limited_serializer.errors,
      }, status=status.HTTP_400_BAD_REQUEST)

class AuthenticateUserWithEmailValidation(views.APIView):
  '''Used to authenticate user credentials as well as email validation'''

  def get(self, request, format=None):
    '''
      Sends an email to the given user email that holds an authenticate
      email link.

      expected query param: ?email='owen.p.thurm@gmail.com'
    '''

    try:
      user_email = request.query_params['email']
      try:
        user_service.send_register_email_validation_email(user_email)
      except Exception as e:
        return Response({
          "message": "user responding to email does not exist",
          "data": user_email,
        }, status=status.HTTP_200_OK)
      return Response({
        "message": "sent email validation email",
        "email": user_email,
      }, status=status.HTTP_200_OK)
    except Exception as e:
      return Response({
        "message": "must include an email query parameter",
      }, status=status.HTTP_400_BAD_REQUEST)

  def post(self, request, format=None):
    '''
      Checks if the given email and password information are valid.

      Then checks that the given email validation token corresponds
      to the given email, and sets the user's email_validated status
      accordingly.

      expects the following body:

      {
        "username": "owenthurm",
        "password": "Password123",
        "email_validation_token": "alsdkjhfaklsdjhkjahkisdwoeoiw"
      }
    '''

    authenticate_with_email_serializer = serializers.AuthenticationWithEmailValidationSerializer(data=request.data)

    if authenticate_with_email_serializer.is_valid():
      user_email = request.data['email']
      user_password = request.data['password']
      email_validation_token = request.data['email_validation_token']
      # Authenticate the username and password
      user_username = user_service.authenticate_user(user_email, user_password)
      if user_username is None:
        # did not pass authentication
        return Response({
          "message": "invalid credentials",
          "authenticated": False,
        }, status=status.HTTP_200_OK)
      # Verify that the email_validation_token matches the email
      try:
        if user_service.email_validation_token_matches_user_email(user_email, email_validation_token):
          # Set the email_validated to be true
          user_service.set_email_validated(user_username, True)
          auth_token = user_service.generate_token(user_username)
          return Response({
            "message": "user authenticated and email verified",
            "authenticated": True,
            "token": auth_token,
          }, status=status.HTTP_200_OK)
        else:
          return Response({
            "message": "email validation token invalid",
            "authenticated": False,
          }, status=status.HTTP_200_OK)
      except Exception as e:
        return Response({
          "message": "invalid email validation token",
          "authenticated": False,
          "data": authenticate_with_email_serializer.data,
        }, status=status.HTTP_200_OK)
    else:
      return Response({
        "message": "invalid",
        "data": authenticate_with_email_serializer.data,
        "errors": authenticate_with_email_serializer.errors,
      }, status=status.HTTP_400_BAD_REQUEST)

class PromoCommentFilterAPIView(views.APIView):
  '''An APIView for the comment filter status of promo accounts'''

  def put(self, request, format=None):
    '''
      Used to update whether or not a promo account is
      using the user's comment filter

      expects the following body:

      {
        "promo_username": "upcomingstreetwearfashion",
        "using_comment_filter": False
      }
    '''

    promo_using_comment_filter_serializer = serializers.PromoUsingCommentFilterSerializer(data=request.data)

    if promo_using_comment_filter_serializer.is_valid():
      #set the using comment filter status
      promo_username = request.data['promo_username']
      using_comment_filter = request.data['using_comment_filter']
      try:
        promo_account_service.set_promo_using_comment_filter(promo_username, using_comment_filter)
        return Response({
          "message": "set promo using comment filter status",
          "data": promo_using_comment_filter_serializer.data,
        }, status=status.HTTP_200_OK)
      except Exception as e:
        return Response({
          "message": "no promo account corresponding to given username",
          "data": promo_using_comment_filter_serializer.data,
        }, status=status.HTTP_404_NOT_FOUND)
    else:
      return Response({
        "message": "invalid",
        "data": promo_using_comment_filter_serializer.data,
        "errors": promo_using_comment_filter_serializer.errors,
      }, status=status.HTTP_400_BAD_REQUEST)