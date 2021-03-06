import logging
from flask import (
    Blueprint,
    jsonify,
    request,
    abort,
    current_app
)

from onepiece.exceptions import (
    ComicbookException,
    NotFoundError,
    SiteNotSupport
)
from . import crawler
from . import task
from .const import ConfigKey


logger = logging.getLogger(__name__)
app = Blueprint("api", __name__, url_prefix='/api')
aggregate_app = Blueprint("aggregate", __name__, url_prefix='/aggregate')
manage_app = Blueprint("task", __name__, url_prefix='/manage')


def handle_404(error):
    if isinstance(error, NotFoundError):
        return jsonify(dict(message=str(error))), 404
    elif isinstance(error, SiteNotSupport):
        return jsonify(dict(message=str(error))), 400
    else:
        return jsonify(dict(message=str(error))), 500


app.register_error_handler(ComicbookException, handle_404)
aggregate_app.register_error_handler(ComicbookException, handle_404)
manage_app.register_error_handler(ComicbookException, handle_404)


def check_manage_secret(request):
    secret = request.headers.get('API-Secret', '')
    right_secret = current_app.config.get(ConfigKey.MANAGE_SECRET)
    if right_secret:
        if secret != right_secret:
            abort(403)


@app.route("/<site>/comic/<comicid>")
def get_comicbook_info(site, comicid):
    result = crawler.get_comicbook_info(site=site, comicid=comicid)
    return jsonify(result)


@app.route("/<site>/comic/<comicid>/<int:chapter_number>")
def get_chapter_info(site, comicid, chapter_number):
    result = crawler.get_chapter_info(site=site, comicid=comicid, chapter_number=chapter_number)
    return jsonify(result)


@app.route("/<site>/search")
def search(site):
    name = request.args.get('name')
    page = request.args.get('page', default=1, type=int)
    if not name:
        abort(400)
    result = crawler.get_search_resuult(site=site, name=name, page=page)
    return jsonify(dict(search_result=result))


@app.route("/<site>/tags")
def tags(site):
    result = crawler.get_tags(site)
    return jsonify(dict(tags=result))


@app.route("/<site>/list")
def tag_list(site):
    tag = request.args.get('tag')
    page = request.args.get('page', default=1, type=int)
    result = crawler.get_tag_result(site=site, tag=tag, page=page)
    return jsonify(dict(list=result))


@app.route("/<site>/latest")
def latest(site):
    page = request.args.get('page', default=1, type=int)
    result = crawler.get_latest(site=site, page=page)
    return jsonify(dict(latest=result))


@aggregate_app.route("/search")
def aggregate_search():
    site = request.args.get('site')
    name = request.args.get('name')
    if not name:
        abort(400)
    result = crawler.aggregate_search(site=site, name=name)
    return jsonify(dict(list=result))


@manage_app.route("/cookies/<site>", methods=['GET'])
def get_cookies(site):
    check_manage_secret(request)
    cookies = crawler.get_cookies(site=site)
    return jsonify(dict(cookies=cookies))


@manage_app.route("/cookies/<site>", methods=['POST'])
def update_cookies(site):
    check_manage_secret(request)
    content = request.json or {}
    cookies = content.get('cookies')
    cover = content.get('cover', False)
    if not cookies or not isinstance(cookies, list):
        abort(400)
    ret = crawler.update_cookies(site=site, cookies=cookies, cover=cover)
    return jsonify(dict(cookies=ret))


@manage_app.route("/task/add")
def add_task():
    site = request.args.get('site')
    comicid = request.args.get('comicid')
    chapter = request.args.get('chapter', default='-1')
    send_mail = request.args.get('send_mail', default=0, type=int)
    gen_pdf = request.args.get('gen_pdf', default=0, type=int)
    receivers = request.args.get('receivers', default="")
    is_all = 1 if request.args.get('is_all') == '1' else 0
    check_manage_secret(request)
    result = task.add_task(site=site,
                           comicid=comicid,
                           chapter=chapter,
                           is_all=is_all,
                           send_mail=send_mail,
                           gen_pdf=gen_pdf,
                           receivers=receivers)
    return jsonify(dict(data=result))


@manage_app.route("/task/list")
def list_task():
    page = request.args.get('page', default=1, type=int)
    check_manage_secret(request)
    size = 20
    result = task.list_task(page=page, size=size)
    return jsonify(dict(list=result))
