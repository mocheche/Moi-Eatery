import datetime
from dateutil import rrule ,easter ,parser, relativedelta
import calendar
#import sched
import os
import random

from celery import task

from django.utils import timezone  
from django.core.mail import send_mail
from django.contrib.auth import get_user_model
from django.conf import settings

from Eatery.utils import random_string_generator
from . models import Coupon 

User = get_user_model()


#Automatic looking up of a holiday
class Holidays:
	#Fuzzy parsing of dates
    def tryparse(self, date):
    	#Dateutil needs a string so we generate one
    	kwargs = {}
    	if isinstance(date ,(tuple , list)):
    		date = ' '.join([str(x) for x in date])
    	elif isinstance(date,int):
    		date = str(date)
    	elif isinstance(date ,dict):
    		kwargs = date
    		date = kwargs.pop('date')
    	try:
    		parse_date = parser.parse(date , **kwargs)
    	except ValueError:
    		parse_date = parser.parse(date , fuzzy=True)
    	return parse_date

    def all_easter(self, start , end):
    	#Return the list of Easter dates within start..end
        s = self.tryparse(start)
        e = self.tryparse(end)
        #Generate date objects from datetime objects as easter requires date objects
        #while our tryparse returns datetime objects
        start = datetime.date(s.year, s.month, s.day)
        end   = datetime.date(e.year, e.month, e.day)
        easters = [easter.easter(y) for y in range(start.year , end.year)]
        return [d for d in easters if start <= d <= end]
    
    def all_boxing(self, start, end):
        #Return the list of Boxing dates within start..end
        start = self.tryparse(start)
        end  = self.tryparse(end)
        days = [datetime.datetime(y ,12,26) for y in range(start.year , end.year)]
        return [d for d in days if start<= d <= end]
        
    def all_christmas(self , start ,end):
		#Return the list of Chrismas dates within start..end
        start = self.tryparse(start)
        end  = self.tryparse(end)
        days = [datetime.datetime(y ,12,25) for y in range(start.year , end.year)]
        return [d for d in days if start<= d <= end]
    
    def all_labor(self , start ,end):
		# return a list of labor days
        start = self.tryparse(start)
        end   = self.tryparse(end)
        labors = rrule.rrule(freq= rrule.YEARLY, bymonth=9 ,byweekday=rrule.MO(1), dtstart=start , until=end)
        return [d.date() for d in labors]
    
    def read_holidays(self ,start ,end , holiday_file):
		#Return a list of holiday dates	
        holidays =[]
        with open(holiday_file) as holiday_file:
            for line in holiday_file:
                #skip blank lines and comments
                if line.isspace() and line.startwith('#'):
                    continue
                # try:
                # 	y,m,d = [int(x) for x in line.split(',')]
                # 	date = datetime.date(y,m,d)
                # except ValueError as e:
                # 	pass
                date = self.tryparse(line)
                if self.tryparse(start) <= date <= self.tryparse(end):
                    holidays.append(date)
        return holidays
    holidays_by_country = {

		#map each country code to a sequence of functions
		'TZ':(all_labor,all_christmas,all_boxing,all_easter),
        'KE':(all_labor,all_christmas,all_boxing,all_easter),
        'UG':(all_labor,all_christmas,all_boxing,all_easter),
	}
    
    def holidays(self, code, start, end ,file ):
		#Read applicable holdays from the file
        all_holidays = self.read_holidays(start, end, file)
		#add all holidays computed by applicable functions
        functions = self.holidays_by_country.get(code)
		#eliminate duplicates
        for function in functions:
        	all_holidays += function(self,start ,end)
        all_holidays = list(set(all_holidays))
        return all_holidays



class Get_date(object):
	weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday',
	           'Friday', 'Saturday', 'Sunday']
	def next_friday(self):
		lastfriday = datetime.date.today()
		oneday = datetime.timedelta(days=1)
		while lastfriday.weekday() != calendar.FRIDAY:
			lastfriday += oneday
		return lastfriday
		
	def get_any_date(self ,day_name,start_date=None):
		if start_date is None:
			start_date = datetime.datetime.today()
		day_num = start_date.weekday()
		target = self.weekdays.index(day_name)
		days_ago = (7 + day_num + target) % 7
		if days_ago == 0:
			days_ago = 7
		target_date = start_date + datetime.timedelta(days=days_ago)
		return target_date

	#simpler implementation
	def friday(self):
		today = datetime.datetime.today()
		next_friday = today + relativedelta.relativedelta(weekday=rrule.FR)
		return next_friday
#Helper method for generating friday and set of holidays

def helper():
	holidays =[]
	file = os.path.join(settings.BASE_DIR ,'coupon' , 'holidays.txt')
	for zone in Holidays().holidays_by_country:
		holidays.append(Holidays().holidays(zone,2019,2020,file= file))
	# friday = Get_date().friday()

	# if friday in holidays:
	# 	return friday
	# else:
	# 	print('No Match')
	# 	return None


#Generate a random key_string of length 20 and send it a random user each , with a discount
#if the user has spent more than 5000 shopping with
@task
def send_coupon_code():
    '''
    Task to send an email notification when an order has been
    successifully created
    '''
    code = random_string_generator(size=10)
    #holidays = helper()
    begin   = timezone.now()
    expires = begin + datetime.timedelta(days=30)
    coupon  = Coupon(code=code, valid_from=begin, valid_to=expires,discount=40,active=True)
    coupon.save()
    users = User.objects.all()

    try:
    	lucky_user = random.choice(random.shuffle(users))
    except TypeError:
    	pass
    else:
        subject = 'Congraturations!!'
        message = 'Dear {},\n\nYou have successifully won yourself a shopping coupon,Please go ahead and user to shop before it expires.\
               Your coupon code is {} '.format(lucky_user.first_name, code)
        mail_sent = send_mail(
        	subject,
            message,
            'admin@Eatery.com',
            [lucky_user.email])
        return mail_sent
    


    
