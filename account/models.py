from django.db import models


# Create your models here.
class User(models.Model):
    email = models.EmailField()
    username = models.CharField(max_length=50)
    is_activated = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()


class UserAPIToken(models.Model):
    user_id = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=20)
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField()
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
