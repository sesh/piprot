import requests
from six import StringIO

GITHUB_API_BASE = 'https://api.github.com'


def build_github_url(repo, branch='master', path='requirements.txt', token=None):
    """
    Builds a URL to a file inside a Github repository.
    """

    # args come is as 'None' instead of not being provided
    if not path:
        path = 'requirements.txt'

    if not branch:
        branch = 'master'

    url = 'https://raw.githubusercontent.com/{}/{}/{}'.format(
        repo, branch, path
    )

    if token:
        url = '{}?token={}'.format(url, token)

    return url


def get_requirements_file_from_url(url):
    response = requests.get(url)

    if response.status_code == 200:
        return StringIO(response.text)
    else:
        return StringIO("")
