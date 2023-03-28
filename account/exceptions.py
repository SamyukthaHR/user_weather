from rest_framework.exceptions import APIException


class DuplicateException(APIException):
    default_detail = 'Duplicate Email'


class ActivateException(APIException):
    default_detail = 'Activate your account'
