from flask import Flask, render_template, request

from utils import find_similar_repos
from exeptions import GitHubAPIError

app = Flask(__name__)


@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')


@app.route('/projects', methods=['POST'])
async def projects():
    request_url = request.form['repo_url'].split('/')
    if not 'github.com' in request_url:
        return render_template('index.html', is_error=True, message='Invalid GitHub URL')
    repo = request_url[-1]
    owner = request_url[-2]
    try:
        projects = await find_similar_repos(owner, repo)
    except GitHubAPIError as e:
        return render_template('index.html', is_error=True, message=e.args[0])
    return render_template('index.html', projects=projects, url=request.form['repo_url'])


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
