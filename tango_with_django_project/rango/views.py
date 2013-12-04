from datetime import datetime

from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.template import RequestContext
from django.shortcuts import render_to_response, redirect
from rango.models import Category, Page, UserProfile
from rango.forms import CategoryForm, PageForm, UserForm, UserProfileForm

from rango.bing_search import run_query

def get_cat_list():
	category_list = Category.objects.order_by('name')

	for category in category_list:
		category.url = encode(category.name)

	return category_list

def encode(str):
	return str.replace(' ', '_')

def decode(str):
	return str.replace('_', ' ')	

def index(request):
	context = RequestContext(request)
	category_list = get_cat_list()
	top_categories = Category.objects.order_by('-likes')[:5]
	page_list = Page.objects.order_by('-views')[:5]

	for category in top_categories:
		category.url = encode(category.name)

	context_dict = {'categories': top_categories, 
					'pages': page_list, 
					'category_list': category_list}

	if request.session.get('last_visit'):
		last_visit_time = request.session.get('last_visit')
		visits = request.session.get('visits', 0)

		if (datetime.now() - datetime.strptime(last_visit_time[:-7], "%Y-%m-%d %H:%M:%S")).days > 0:
			request.session['visits'] = visits + 1
			request.session['last_visit'] = str(datetime.now())
	else:
		request.session['last_visit'] = str(datetime.now())
		request.session['visits'] = 1

	return render_to_response('rango/index.html', context_dict, context)		

def about(request):
	context = RequestContext(request)
	context_dict = {}
	category_list = get_cat_list()

	visits = request.session.get('visits', 0)
	aboutmessage = """This is a Django web development tutorial in progress.
					Register and login to begin adding Categories and Pages!"""
					
	context_dict['visits'] = visits
	context_dict['aboutmessage'] = aboutmessage
	context_dict['category_list'] = category_list
		
	return render_to_response('rango/about.html', context_dict, context)

def category(request, category_name_url):
	context = RequestContext(request)
	category_name = decode(category_name_url)
	category_list = get_cat_list()

	context_dict = {'category_name': category_name,
					'category_name_url': category_name_url,
					'category_list': category_list}

	try:
		category = Category.objects.get(name=category_name)
		pages = Page.objects.filter(category=category).order_by('-views')[:5]
		context_dict['pages'] = pages
		context_dict['category'] = category
		context_dict['category_name_url'] = category_name_url

	except Category.DoesNotExist:
		pass

	results_list = []

	if request.method == 'POST':
		query = request.POST['query'].strip()
		queried = True

		if query:
			# Run the Bing API function
			results_list = run_query(query)	
		context_dict['results_list'] = results_list
		context_dict['queried'] = queried	

	return render_to_response('rango/category.html', context_dict, context)

@login_required
def add_category(request):
	context = RequestContext(request)
	category_list = get_cat_list()
	# A HTTP POST?
	if request.method == 'POST':
		form = CategoryForm(request.POST)

		if form.is_valid():
			form.save(commit=True)
			# Returns the user to the homepage.
			return index(request)
		else:
			print form.errors
	else:
		form = CategoryForm()

	return render_to_response('rango/add_category.html', {'form': form, 'category_list': category_list}, context)

@login_required
def add_page(request, category_name_url):
	context = RequestContext(request)
	context_dict = {}
	category_name = decode(category_name_url)
	if request.method == 'POST':
		form = PageForm(request.POST)

		if form.is_valid():
			page = form.save(commit=False)

			cat = Category.objects.get(name=category_name)
			page.category = cat
			page.views = 0
			page.save()

			return category(request, category_name_url)
		else:
			print form.errors
	else:	
		form = PageForm()

	context_dict['category_name'] = category_name
	context_dict['category_name_url'] = category_name_url
	context_dict['form'] = form

	return render_to_response('rango/add_page.html', context_dict,
		context)

def register(request):
	context = RequestContext(request)
	context_dict = {}
	registered = False

	if request.method == 'POST':
		user_form = UserForm(data=request.POST)
		profile_form = UserProfileForm(data=request.POST)

		if user_form.is_valid() and profile_form.is_valid():
			user = user_form.save()
			# Hash the password with the .set_password method
			user.set_password(user.password)
			user.save()

			profile = profile_form.save(commit=False)
			profile.user = user

			if 'picture' in request.FILES:
				profile.picture = request.FILES['picture']

			profile.save()

			registered = True

		else:
			print user_form.errors, profile_form.errors

	else:
		user_form = UserForm()
		profile_form = UserProfileForm()

	context_dict['user_form'] = user_form
	context_dict['profile_form'] = profile_form
	context_dict['registered'] = registered

	return render_to_response('rango/register.html', context_dict, context)


def user_login(request):
	context = RequestContext(request)

	if request.method == 'POST':
		# This information is obtained from the login form.
		username = request.POST['username']
		password = request.POST['password']	

		# If the combatin is valid, a User object is returned.
		user = authenticate(username=username, password=password)

		if user is not None:
			# Is the account active? It may have been disabled.
			if user.is_active:
				login(request, user)
				return HttpResponseRedirect('/rango/')

			else:
				disabled = True
				return render_to_response("rango/login.html", {'disabled': disabled}, context)

		else:
			# Bad login details were provided.
			failed_attempt = True
			print "Invalid login: {0}, {1}".format(username, password)
			return render_to_response("rango/login.html", {'failed_attempt': failed_attempt},
															context)
	# Not a HTTP POST
	else:
		return render_to_response('rango/login.html', {}, context)			


@login_required
def user_logout(request):
	logout(request)

	return HttpResponseRedirect('/rango/')


@login_required
def restricted(request):
	context = RequestContext(request)
	context_dict = {'restricted': 'If you can see this, you are no longer a Jabronie'}
	return render_to_response('rango/restricted.html', context_dict, context)

def search(request):
	context = RequestContext(request)
	results_list = []

	if request.method == 'POST':
		query = request.POST['query'].strip()

		if query:
			# Run the Bing API function
			results_list = run_query(query)

	return render_to_response('rango/search.html', {'results_list': results_list}, context)			

@login_required
def profile(request):
	context = RequestContext(request)
	category_list = get_cat_list()
	user = User.objects.get(username=request.user)
	
	try:
		profile = UserProfile.objects.get(user=user)

	except:
		profile = None

	context_dict = {'profile': profile, 
					'user': user, 
					'category_list': category_list}

	return render_to_response('rango/profile.html', context_dict, context)

def track_url(request):
	context = RequestContext(request)
	page_id = None
	url = '/rango/'
	if request.method == 'GET':
		if 'page_id' in request.GET:
			page_id = request.GET['page_id']
			try:
				page = Page.objects.get(id=int(page_id))
				page.views += 1
				page.save()
				url = page.url
			except:
				pass	
	
	return redirect(url)					

@login_required
def like_category(request):
	context = RequestContext(request)
	category_id = None
	if request.method == 'GET':
		category_id = request.GET['category_id']

	likes = 0
	if category_id:
		category = Category.objects.get(id=int(category_id))

		if category:
			likes = category.likes + 1
			category.likes = likes
			category.save()

	return HttpResponse(likes)			

def get_category_list(max_results=0, starts_with=''):
	category_list = []
	if starts_with:
		category_list = Category.objects.filter(name__startswith=starts_with)	
	else:
		category_list = Category.objects.all()

	if max_results > 0:
		if len(category_list) > max_results:
			category_list = category_list[:max_results]

	for category in category_list:
		category.url = encode(category.name)		

	return category_list

def suggest_category(request):
	context = RequestContext(request)
	category_list = []
	starts_with = ''

	if request.method == 'GET':
		starts_with = request.GET['suggestion']
	else:
		starts_with = request.POST['suggestion']	
	
	category_list = get_category_list(8, starts_with)

	return render_to_response('rango/category_list.html', {'category_list': category_list}, context)					

@login_required
def auto_add_page(request):
	context = RequestContext(request)
	category_id = None
	url = None
	title = None
	context_dict = {}

	if request.method == "GET":
		category_id = request.GET['category_id']
		title = request.GET['title']
		url = request.GET['url']
		
		if category_id:
			category = Category.objects.get(id=int(category_id))
			p = Page.objects.get_or_create(category=category, title=title, url=url)
			pages = Page.objects.filter(category=category).order_by('-views')

			context_dict['pages'] = pages
			context_dict['category'] = category

	return render_to_response('rango/pages.html', context_dict, context)


def get_pages(request, category_name_url):
	context = RequestContext(request)
	context_dict = {}
	category_list = get_cat_list()
	
	category_name = decode(category_name_url)
	
	category = Category.objects.get(name=category_name)
	pages = Page.objects.filter(category=category)
	
	context_dict['category'] = category
	context_dict['pages'] = pages
	context_dict['category_name_url'] = category_name_url
	context_dict['category_list'] = category_list

	return render_to_response('rango/page_list.html', context_dict, context)