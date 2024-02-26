import aiohttp
import asyncio
from collections import Counter

from config import ACCESS_TOKEN
from exсeptions import GitHubAPIError


async def get_owner_url(owner_username):
    return f"https://github.com/{owner_username}"


async def get_repo_url(repo_name, repo_owner):
    return f"https://github.com/{repo_owner}/{repo_name}"


async def get_contributors(owner, repo):
    url = f"https://api.github.com/repos/{owner}/{repo}/contributors"
    headers = {'Authorization': f'token {ACCESS_TOKEN}'}
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(url) as response:
            if response.status == 200:
                contributors = await response.json()
                return [contributor['login'] for contributor in contributors]
            else:
                raise GitHubAPIError(f"Failed to retrieve contributors for {owner}/{repo}: {response.status}")


async def get_contributed_repos(user):
    url = f"https://api.github.com/users/{user}/repos"
    headers = {'Authorization': f'token {ACCESS_TOKEN}'}
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(url) as response:
            if response.status == 200:
                repos = await response.json()
                return [repo['name'] for repo in repos]
            else:
                raise GitHubAPIError(f"Failed to retrieve repositories for {user}: {response.status}")


def update_similar_repos(similar_repos, contributed_repos, base_repo, contributor):
    counter = Counter(contributed_repos)
    counter.subtract({base_repo})
    for repo, count in counter.items():
        if count > 0:
            if repo in similar_repos:
                similar_repos[repo]['count'] += count
            else:
                similar_repos[repo] = {'owner': contributor, 'count': count}


def sort_repositories(similar_repos, top_n):
    return sorted(similar_repos.items(), key=lambda x: x[1]['count'], reverse=True)[:top_n]


async def prepare_result(sorted_repos):
    result = []
    for repo_name, data in sorted_repos:
        owner = data['owner']
        owner_url = await get_owner_url(owner)  # Await here
        repo_url = await get_repo_url(repo_name, owner)
        result.append({
            'owner': owner,
            'repo_name': repo_name,
            'repo_url': repo_url,
            'repo_owner_url': owner_url,  # Use awaited result here
            'common_contributors': data['count']
        })
    return result


async def get_similar_repositories(base_contributors, base_repo):
    similar_repos = {}
    tasks = []
    for contributor in base_contributors:
        tasks.append(get_contributed_repos(contributor))

    contributed_repos_list = await asyncio.gather(*tasks)

    for contributor, contributed_repos in zip(base_contributors, contributed_repos_list):
        update_similar_repos(similar_repos, contributed_repos, base_repo, contributor)

    return similar_repos


async def find_similar_repos(base_owner, base_repo, top_n=5):
    base_contributors = await get_contributors(base_owner, base_repo)
    similar_repos = await get_similar_repositories(base_contributors, base_repo)
    sorted_repos = sort_repositories(similar_repos, top_n)
    result = await prepare_result(sorted_repos)  # Await here
    return result

