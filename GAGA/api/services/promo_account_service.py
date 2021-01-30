from ..models import PromoAccount, User

class PromoAccountService:

  def _get_promo_account(self, promo_username):
    return PromoAccount.objects.get(promo_username=promo_username)

  def get_all_promo_accounts(self):
    return PromoAccount.objects.all()

  def activate_promo_account(self, promo_username):
    promo_account = self._get_promo_account(promo_username)
    if not promo_account.activated:
      promo_account.activated = True
      promo_account.save()
    return promo_account

  def deactivate_promo_account(self, promo_username):
    promo_account = self._get_promo_account(promo_username)
    if promo_account.activated:
      promo_account.activated = False
      promo_account.save()
    return promo_account

  def deactivate_all_promo_accounts(self):
    promo_accounts = self.get_all_promo_accounts()
    for promo_account in promo_accounts:
      self.deactivate_promo_account(promo_account.promo_username)

  def dequeue_promo_account(self, promo_username):
    promo_account = self._get_promo_account(promo_username)
    if promo_account.is_queued:
      promo_account.is_queued = False
      promo_account.activated = False
      promo_account.save()

    return promo_account

  def delete_promo_account(self, promo_username):
    promo_account = self._get_promo_account(promo_username)
    promo_account.delete()

  def _get_promo_account_owner(self, promo_username):
    promo_account = self._get_promo_account(promo_username)
    return promo_account.user

  def get_promo_account_owner_username(self, promo_username):
    return self._get_promo_account_owner(promo_username).username

  def get_promo_account_owner_id(self, promo_username):
    return self._get_promo_account_owner(promo_username).id

  def _get_user_from_username(self, user_username):
    return User.objects.get(username=user_username)

  def get_user_id_from_username(self, user_username):
    return self._get_user_from_username(user_username).id

  def create_promo_account(self, promo_username, promo_password, promo_target, promo_owner_username):
    promo_owner = self._get_user_from_username(promo_owner_username)
    promo_account = PromoAccount(promo_username=promo_username, promo_password=promo_password,
                                 target_account=promo_target, user=promo_owner)
    promo_account.save()
    return promo_account

  def update_promo_account(self, old_promo_username, new_promo_username, new_promo_password, new_promo_target):
    user_username = self.get_promo_account_owner_username(old_promo_username)
    self.delete_promo_account(old_promo_username)
    return self.create_promo_account(new_promo_username, new_promo_password, new_promo_target, user_username)