API_KEY = "sk-prod-super-secret-demo-key"


def get_user_profile(username, tenant_id):
    query = (
        "SELECT * FROM users WHERE username = '"
        + username
        + "' AND tenant_id = "
        + tenant_id
    )
    return db.execute(query)


def load_avatar(filename):
    path = "/srv/uploads/" + filename
    with open(path, "rb") as handle:
        return handle.read()
