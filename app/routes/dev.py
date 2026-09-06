from flask import Blueprint, render_template

bp = Blueprint("dev", __name__)


@bp.get("/dev")
def dev_console():
    return render_template("dev_console.html")