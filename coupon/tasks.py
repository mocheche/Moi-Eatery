import os
import random
import datetime
from dateutil import rrule ,easter ,parser, relativedelta
import calendar
#import sched
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
    	return datetime.date(parse_date.year , parse_date.month, parse_date.day)

    def all_easter(self, start , end):
    	#Return the list of Easter dates within start..end
        start = self.tryparse(start)
        end = self.tryparse(end)
        easters = [easter.easter(y) for y in range(start.year , end.year)]
        return set(d for d in easters if start <= d <= end)

    def all_boxing(self, start, end):
        #Return the list of Boxing dates within start..end
        start = self.tryparse(start)
        end  = self.tryparse(end)
        days = [datetime.date(y ,12,26) for y in range(start.year , end.year)]
        return set(d for d in days if start<= d <= end)

    def all_christmas(self , start ,end):
		#Return the list of Chrismas dates within start..end
        start = self.tryparse(start)
        end  = self.tryparse(end)
        days = [datetime.date(y ,12,25) for y in range(start.year , end.year)]
        return set(d for d in days if start<= d <= end)

    def all_labor(self , start ,end):
		# return a list of labor days
        start = self.tryparse(start)
        end   = self.tryparse(end)
        labors = rrule.rrule(freq= rrule.YEARLY, bymonth=9 ,byweekday=rrule.MO(1),
        					 dtstart=start , until=end)
        return  set(d.date() for d in labors)


    def read_holidays(self ,start ,end , holiday_file):
		#Return a list of holiday dates
        holidays = set()
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
                    holidays.add(date)
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
        	all_holidays.update(function(self,start ,end))
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
		return datetime.date(target_date.year, target_date.month, target_date.day)

	#simpler implementation
	def friday(self):
		today = datetime.datetime.today()
		next_friday = today + relativedelta.relativedelta(weekday=rrule.FR)
		return datetime.date(next_friday.year, next_friday.month, next_friday.day)
#Helper method for generating friday and set of holidays

def helper(start, end):
	holidays =set()
	file = os.path.join(settings.BASE_DIR ,'coupon' , 'holidays.txt')
	for zone in Holidays().holidays_by_country:
		holidays.update(Holidays().holidays(zone,start,end,file= file))
	friday = Get_date().next_friday()
	if friday in holidays:
		return friday
	else:
	 	print('No Match')
	 	return None



# Generate a random code of length 10 if the total of active codes in the database is less 15
# Then deactivates the expired onces from the database
# Then set the code in a tracking table to ensure we Track who gets what from our coupon
# To prevent foul play
def generate_code():
	today   = timezone.now()
	expires = today + datetime.timedelta(days=30)

	# All codes so far in the database
	all_codes = Coupon.objects.all()

	# Deactivate expired codes in the database as we don't want to delete the
	# For analytics purposes
	for code  in all_codes:
    #Remove inactive codes before you start comparing
		if code.active == False:
			code.delete()
		if today >= code.valid_to:
			# Then deactivate expired ones
			code.active =False
			code.save()
	print(all_codes)

	#Generate codes
	if all_codes.count() < 10 and not  all_codes.count() > 15:
		co = [random_string_generator(size=10) for x in range(3)]
		for code_ in co:
			coupon=Coupon.objects.create(code=code_ , valid_from=today,
                                    discount=30,valid_to=expires,active=True)
			coupon.save()

	# Select only active codes from all available codes in the database since we want to be
	# Sure that only active ones are passed to the random selector list compression
	codes = []
	for index in range(all_codes.count()):
		if codes[index].active == True:
			codes.append(code)
	del code

	#Then select only three random codes to send to three random users
	try:
		sent_codes = [random.choice(codes) for i in range(3)]
		return sent_codes
	except IndexError:
		return None

#send a code to 3 random users each , with a discount
@task
def send_coupon_code():
    '''
    Task to send an email notification when an order has been
    successifully created
    '''
    #Check to ensure None was not returned by generate_code
    codes = generate_code()
    if codes is None:
        return 'No Code Found'
    friday  = helper(2019,2022)
    if friday == datetime.date.today():
    	try:
    	    users = User.objects.all()
    	except User.DoesNotExit:
    		return
    	else:
            lucky_users = [random.choice(users) for i in range(3)]
            for i in range(len(codes)):
            	subject = 'Congraturations!!'
            	message = f"""
            	Dear {lucky_users[i].full_name},\n\nYou have successifully won yourself a shopping coupon,\n '
            	Please go ahead and use it to shop before it expires.\n
            	Its valid for 30 days,so don"t forget.\n
            	Your coupon code is {codes[i]} """
            	sent_mail=send_mail(subject,message,'admin@Eatery.com',[lucky_users[i].email])

 	        # But before we return we must ensure that any code sent is not going to be used again
 	        # So we explictly deactivate it here such that when generate_code function generates sent_codes
 	        # It generates only active codes
            for code in codes:
                 code.active=False
                 code.save()
            return  sent_mail          #'Code Emailed Sucessifully'

    else:
        return 'Code Not Emailed'