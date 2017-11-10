from django.db import models
from datetime import datetime
from django.conf import settings
from django.core.files.storage import FileSystemStorage
import os
from django.db.models.signals import pre_save, post_save
import hashlib
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser, PermissionsMixin, User
import base64
from Crypto.Cipher import AES
from django.contrib.auth.models import Permission

###############################################################################
# Storage
###############################################################################
private_storage = FileSystemStorage(location=settings.CRASH_STORAGE_ROOT)
fuzzerStorage = FileSystemStorage(location=settings.FUZZER_STORAGE_ROOT)
testcaseStorage = FileSystemStorage(location=settings.TESTCASE_STORAGE_ROOT)
userimageStorage = FileSystemStorage(location=settings.USERIMAGE_STORAGE_ROOT)


def getSha256text(plain, convtohex=True):
	h = hashlib.sha256(plain)
	if convtohex == True:
		h = h.hexdigest()
	else:
		h = h.digest()
	return h


def getUploadPath(instance, filename):
	# For crash
	return '{0}/{1}'.format(instance.crash_file.name, filename)


def getFuzzUploadPath(instance, filename):
	# For Testcase / Crash
	rd_str = getSha256text(str(os.urandom(32)).encode('utf-8'))
	rd_str_len = int(len(rd_str) / 2)
	location = '{0}/{1}'.format((rd_str[:rd_str_len]), (rd_str[rd_str_len:]))
	return location


def getimageUploadPath(instance, filename):
	# For Image
	rd_str = getSha256text(str(os.urandom(32)).encode('utf-8'))
	rd_str_len = int(len(rd_str) / 2)  # 8 8 8 8
	# I don't care ext :P
	location = '{0}/{1}.jpg'.format((rd_str[:rd_str_len]), (rd_str[rd_str_len:]))
	return location


class Machine(models.Model):
	owner = models.ForeignKey(User, default=1)
	fuzzer_name = models.CharField(max_length=50)
	target = models.CharField(max_length=200)
	crash_count = models.IntegerField(default=0)
	testcase = models.IntegerField(default=0)
	ping = models.DateTimeField(blank=True, auto_now=True)
	reg_date = models.DateTimeField(default=datetime.now, blank=True)
	pub_ip = models.CharField(max_length=16)
	pri_ip = models.CharField(max_length=16)
	token = models.CharField(max_length=100)

	def __str__(obj):
		return "%s" % (obj.fuzzer_name)


class Crash(models.Model):
	owner = models.ForeignKey(User)
	fuzzer = models.ForeignKey(Machine, null=True, blank=True)

	title = models.CharField(max_length=1000)
	crash_hash = models.CharField(max_length=100)
	crashlog = models.TextField()
	dup_crash = models.IntegerField(default=0)
	crash_file = models.FileField(storage=private_storage, upload_to=getUploadPath)
	reg_date = models.DateTimeField(default=datetime.now, blank=True)  # first date
	latest_date = models.DateTimeField(auto_now=True)
	comment = models.TextField(null=True, blank=True)
	is_encrypted = models.BooleanField(default=False)

	def __str__(obj):
		return "%s" % (obj.title)


class DupCrash(models.Model):
	owner = models.ForeignKey(User)
	original_crash = models.ForeignKey(Crash)
	fuzzer = models.ForeignKey(Machine, null=True, blank=True)

	crash_hash = models.CharField(max_length=100)
	dup_crash = models.IntegerField(default=0)
	crash_file = models.FileField(storage=private_storage, upload_to=getUploadPath)
	reg_date = models.DateTimeField(default=datetime.now, blank=True)  # first date

	def __str__(obj):
		return "%s" % (obj.crash_hash)


class Testcase(models.Model):
	# For uploading fuzzer and testcases.
	owner = models.ForeignKey(User)

	title = models.CharField(max_length=200, blank=True, null=True)
	fuzzerName = models.CharField(max_length=200, blank=True, null=True)
	# binaryName = models.CharField(max_length=200, blank=True, null=True)
	target = models.CharField(max_length=200, blank=True, null=True)
	description = models.TextField(max_length=1024, blank=True, null=True)
	testcase_url = models.CharField(max_length=1024, blank=True, null=True)
	fuzzer_url = models.CharField(max_length=1024, blank=True, null=True)
	fuzzerFile = models.FileField(storage=fuzzerStorage, upload_to=getFuzzUploadPath, blank=True)
	testcaseFile = models.FileField(storage=testcaseStorage, upload_to=getFuzzUploadPath, blank=True)

	def __str__(obj):
		return "%s" % (obj.title)

class OnetimeToken(models.Model):
	token = models.CharField(max_length=512)
	real_path = models.CharField(max_length=5120)
	is_expired = models.BooleanField(default=False)
	owner = models.ForeignKey(User)


class EmailBot(models.Model):
	owner = models.ForeignKey(User)
	email_id = models.CharField(max_length=512)
	email_pw = models.CharField(max_length=512, help_text="Use only if you want to change password", blank=True,
	                            null=True)
	email_pw_enc = models.CharField(max_length=512, default="")
	smtp_server = models.CharField(max_length=512,
	                               help_text="Check https://www.google.com/settings/security/lesssecureapps if use Gmail")
	smtp_port = models.CharField(max_length=5)
	is_public = models.BooleanField(default=False, help_text="Check true if you want to share this email")

	def __str__(obj):
		return "%s" % (obj.email_id)


class TelegramBot(models.Model):
	telegram_bot_name = models.CharField(max_length=512)
	telegram_bot_key = models.CharField(max_length=512)
	is_activated = models.BooleanField(default=False)
	is_public = models.BooleanField(default=False,
	                                help_text="Note That, other user can modify/delete this configuration.")
	owner = models.ForeignKey(User)

	def __str__(obj):
		return "%s" % (obj.telegram_bot_name)


class Profile(models.Model):
	owner = models.ForeignKey(User)

	##
	first_name = models.CharField(max_length=512)
	last_name = models.CharField(max_length=512)
	email = models.EmailField(max_length=512, null=True, blank=True)
	profile_image = models.FileField(storage=userimageStorage, null=True, blank=True, upload_to=getimageUploadPath)

	emailbot = models.ForeignKey(EmailBot, null=True, blank=True)
	telegram = models.ForeignKey(TelegramBot, null=True, blank=True)
	telegram_chatid = models.CharField(max_length=12, null=True, blank=True,
	                                   help_text="To get your chat_id, Add '@get_id_bot' and send '/my_id'")
	alert_message = models.TextField(max_length=10000, default="[SWEETMON] New crash detected : __title__ / __description__", blank=True, null=True, help_text="__title__ => Crash title, __description__ => Crash log")

	use_telegram_alert = models.BooleanField(default=False,
	                                         help_text="You should fill out telegram_chatid to use this feature.")
	use_email_alert = models.BooleanField(default=False,
	                                      help_text="You should fill out email of your profile to use this feature.")

	userkey = models.TextField(null=True, blank=True, help_text="Use this key when you register the new fuzzer.")

	def __str__(obj):
		return "%s" % (obj.owner)


BS = 16
pad = lambda s: s + (BS - len(s) % BS) * chr(BS - len(s) % BS).encode()
unpad = lambda s: s[:-ord(s[len(s) - 1:])]


class AESCipher(object):
	def __init__(self, key):
		self.key = key

	def iv(self):
		return "\x00" * 16

	def encrypt(self, message):
		message = message.encode()
		raw = pad(message)
		cipher = AES.new(self.key, AES.MODE_CBC, self.iv())
		enc = cipher.encrypt(raw)
		return base64.b64encode(enc).decode('utf-8')

	def decrypt(self, enc):
		enc = base64.b64decode(enc)
		cipher = AES.new(self.key, AES.MODE_CBC, self.iv())
		dec = cipher.decrypt(enc)
		return unpad(dec).decode('utf-8')


def EncryptEmailPassword(sender, **kwargs):
	obj = kwargs["instance"]
	if obj.email_pw == None:
		# If password not changed
		return
	aeskey = getSha256text((obj.owner.username + settings.SECRET_KEY + obj.owner.username).encode('utf-8'))[:32]
	enc = AESCipher(aeskey).encrypt(obj.email_pw)
	if obj.email_pw_enc != enc:
		# If password changed
		obj.email_pw_enc = enc
		obj.email_pw = None
		obj.save()


def create_profile(sender, **kwargs):
	# Gen userkey
	userkey = getSha256text(str(os.urandom(32)).encode('utf-8'))
	user = kwargs["instance"]
	if kwargs["created"]:
		# Create user
		user_profile = Profile(owner=user, userkey=userkey)
		user_profile.email = user.email
		user_profile.last_name = user.last_name
		user_profile.first_name = user.first_name
		user_profile.save()

		# Allow access to admin page
		user = User.objects.get(id=user.id)
		user.is_staff = True;

		# Add permissions for staff
		permission_list = ['Can add testcase', 'Can change testcase', 'Can delete testcase',
							'Can add email bot', 'Can change email bot', 'Can delete email bot',
							'Can add issue', 'Can change issue', 'Can delete issue',
							'Can add telegram bot', 'Can change telegram bot', 'Can delete telegram bot',
							'Can add testcase', 'Can change testcase', 'Can delete testcase',
							'Can change profile']
		for permission in permission_list:
			userperm = Permission.objects.get(name=permission)
			user.user_permissions.add(userperm)
		user.save()


def SyncUserProfile(sender, **kwargs):
	# Gen userkey
	profile = kwargs["instance"]
	if not kwargs["created"]:
		user_profile = User.objects.get(id=profile.owner.id)
		user_profile.email = profile.email
		user_profile.last_name = profile.last_name
		user_profile.first_name = profile.first_name
		user_profile.save()


def check_owner(sender, **kwargs):
	print(sender)
	print("==================")
	print(kwargs['signal'])
	print(kwargs['instance'].owner)


# Check owner
# pre_save.connect(check_owner, sender=EmailBot)

post_save.connect(create_profile, sender=User)
post_save.connect(SyncUserProfile, sender=Profile)
# pre_save.connect(problem_hash_check_pre_save, sender=AuthInformation)
pre_save.connect(EncryptEmailPassword, sender=EmailBot)
