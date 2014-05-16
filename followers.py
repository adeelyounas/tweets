import time
import requests

from requests_oauthlib import OAuth1

from bottle import route, run, template, request

RESPONSE_DATA = {}
SORTED_TWEET_KEYS = []

CONSUMER_KEY = "<CONSUMER_KEY>"
CONSUMER_SECRET = "<CONSUMER_SECRET>"

OAUTH_TOKEN = "<OAUTH_TOKEN>"
OAUTH_TOKEN_SECRET = "<OAUTH_SECRET>"


def get_oauth():
    oauth = OAuth1(CONSUMER_KEY,
                client_secret=CONSUMER_SECRET,
                resource_owner_key=OAUTH_TOKEN,
                resource_owner_secret=OAUTH_TOKEN_SECRET)
    return oauth


def generate_followers(cursor="-1"):
    global RESPONSE_DATA, SORTED_TWEET_KEYS
    oauth = get_oauth()
    url = "https://api.twitter.com/1.1/followers/list.json?cursor=%s&skip_status=false&include_user_entities=true" % cursor
    resp = requests.get(url, auth=oauth)
    resp.raise_for_status()
    # import ipdb; ipdb.set_trace()
    data = resp.json()["users"]
    for item in data:
        if "status" in item:
            date = item["status"]["created_at"]
            tweet_date = time.mktime(time.strptime(date, '%a %b %d %H:%M:%S +0000 %Y'))
            RESPONSE_DATA[tweet_date] = item
            SORTED_TWEET_KEYS.append(tweet_date)

    if resp.json()["next_cursor"]:
        generate_followers(resp.json()["next_cursor"])

    SORTED_TWEET_KEYS.sort(reverse=True)


@route('/tweets')
def tweets():

    global RESPONSE_DATA, SORTED_TWEET_KEYS

    paginate_by = int(request.GET.get("paginate_by", 5))

    page = int(request.GET.get("page", 1))

    page = 1 if page < 1 else page
    start = (paginate_by * (page-1))
    end = (start + paginate_by) - 1

    if page == 1:
        RESPONSE_DATA = {}
        SORTED_TWEET_KEYS = []
        generate_followers()

    keys = SORTED_TWEET_KEYS[start:end]

    index = "<b>Follower's Tweets ! </b><hr/>"

    for key in keys:
        index = index + '''
            <ul>
                <li>Name: %(name)s</li>
                <li>Tweet: %(tweet)s</li>
                <li>Date: %(date)s</li>
            </ul>
        ''' % {
            "name": RESPONSE_DATA[key]["name"],
            "tweet": RESPONSE_DATA[key]["status"]["text"],
            "date": str(RESPONSE_DATA[key]["status"]["created_at"]),
        }

    index = index + "<hr>"
    pagination = ""

    if page == 1:
        pagination = pagination + "<< previous | "
    else:
        pagination = pagination + '<a href="/tweets?page=%d"><< previous</a> | ' % int(page-1)

    if (end+1) >= len(SORTED_TWEET_KEYS):
        pagination = pagination + "next >>"
    else:
        pagination = pagination + '<a href="/tweets?page=%d">next >></a>' % int(page+1)

    index = index + pagination

    return template(index)


if __name__ == "__main__":
    run(host='localhost', port=8080, debug=True, reloader=True)
