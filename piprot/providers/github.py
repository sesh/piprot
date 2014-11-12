import requests
from requests.auth import HTTPBasicAuth

from six import StringIO

PIPROT_USER_TOKEN = '095f49a458dc0c310c302e8099012c8433b65f94'
GITHUB_API_BASE = 'https://api.github.com'

class GithubPullRequestException(Exception):
    pass


def build_github_url(repo, branch='master'):
    return 'https://raw.githubusercontent.com/{}/{}/requirements.txt'.format(
        repo, branch
    )


def get_requirements_from_url(url, verbatim=False):
    response = requests.get(url)

    if response.status_code == 200:
        return StringIO(response.content)
    else:
        return StringIO("")


def pull_request(repo, req, latest_version, specified_version):
    _check_for_existing_pr(repo, req, latest_version)
    fork = _check_for_existing_fork(repo)

    if not fork:
        _fork_repo(repo)

def _check_for_existing_pr(repo, req, latest_version):
    url = '{}/repos/{}/pulls?state=all'.format(GITHUB_API_BASE, repo)
    prs = github(url)

    for pr in prs:
        if req in pr['title'] and latest_version in pr['title']:
            raise GithubPullRequestException('PR Failed: Existing PR Exists')


def _check_for_existing_fork(repo):
    url = '{}/user/repos'.format(GITHUB_API_BASE)
    repos = github(url)

    repo_name = repo.split('/')[-1]
    for repo in repos:
        if repo['fork'] and repo['name'] == repo_name:
            print 'Fork already exists'
            return repo


def _fork_repo(repo):
    pass


def _update_requirements_file(repo, req, latest_version, specified_version):
    pass


def _create_pull_request(repo, req, latest_version, specified_version):
    pass


def github(url):
    items = []
    while url:
        response = requests.get(url, auth=HTTPBasicAuth(PIPROT_USER_TOKEN,
                                                        'x-oauth-basic'))
        for item in response.json():
            items.append(item)
        try:
            url = response.links['next']['url']
        except KeyError:
            url = None

    return items
