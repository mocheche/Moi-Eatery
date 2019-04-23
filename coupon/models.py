from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
#from django.conf import settings

class Coupon(models.Model):
	code       = models.CharField(max_length=55)
	valid_from = models.DateTimeField()
	valid_to   = models.DateTimeField()
	discount   = models.PositiveIntegerField(validators=[MinValueValidator(0), MaxValueValidator(100)])
	active     = models.BooleanField()


	def __str__(self):
		return self.code

	