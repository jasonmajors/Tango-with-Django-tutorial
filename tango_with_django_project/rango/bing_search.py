import json
import urllib, urllib2

def run_query(search_terms):
	root_url = 'https://api.datamarket.azure.com/Bing/Search/'
	source = 'Web'

	results_per_page = 10
	offset = 0
	# Wrap quotes around our query terms as required by the Bing API.
	query = "'{0}'".format(search_terms)
	query = urllib.quote(query)

	search_url = "{0}{1}?$format=json&$top={2}&$skip={3}&Query={4}".format(
		root_url,
		source,
		results_per_page,
		offset,
		query)

	username = ''
	bing_api_key = 'mf8M87kwr0Fn+x06lKyTPwD889TtWOUIaWNEpyQtajw'

	password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
	password_mgr.add_password(None, search_url, username, bing_api_key)

	results = []

	try:
		# Prepare for connecting to Bing's servers.
		handler = urllib2.HTTPBasicAuthHandler(password_mgr)
		opener = urllib2.build_opener(handler)
		urllib2.install_opener(opener)
		# Connect to the server and read the response generated.
		response = urllib2.urlopen(search_url).read()
		# Convert the string response to a Python dictionary object.
		json_response = json.loads(response)

		for result in json_response['d']['results']:
			results.append({
				'title': result['Title'],
				'link': result['Url'],
				'summary': result['Description']})
		
	# Catch a URLError exception - something went wrong when connecting.
	except urllib2.URLError, e:
		print "Error when quering the Bing API: ", e

	return results

def main():
	query = raw_input().strip()
	results = run_query(query)
	i = 1
	for result in results:
		print "Rank: %d -- Title: %s, URL: %s" % (i, result['title'], result['link'])
		i += 1

if __name__ == "__main__":
	main()

