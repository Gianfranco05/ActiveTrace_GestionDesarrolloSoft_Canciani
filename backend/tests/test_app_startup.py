from app.main import create_app


def test_app_creates_successfully():
    app = create_app()
    assert app.title == "activia-trace"


def test_app_has_health_route():
    app = create_app()
    routes = [route.path for route in app.routes]
    assert "/health" in routes
