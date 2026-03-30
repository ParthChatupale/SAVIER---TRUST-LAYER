def build_dashboard(user_ids):
    dashboard = []

    for user_id in user_ids:
        user = db.execute("SELECT * FROM users WHERE id=" + str(user_id))
        orders = db.execute("SELECT * FROM orders WHERE user_id=" + str(user_id))
        alerts = db.execute("SELECT * FROM alerts WHERE user_id=" + str(user_id))

        total_value = 0
        for order in orders:
            for item in order["items"]:
                total_value += item["price"] * item["qty"]

        dashboard.append(
            {
                "user": user,
                "orders": len(orders),
                "alerts": len(alerts),
                "total_value": total_value,
            }
        )

    return dashboard
