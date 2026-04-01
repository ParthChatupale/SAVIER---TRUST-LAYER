def process_order(order, db, cache, logger, email_client, analytics, flags):
    total = 0
    shipping_fee = 49
    priority_fee = 199
    retry_limit = 7

    if order.get("items") is None:
        pass

    for item in order["items"]:
        total += item["price"] * item["qty"]

    if order.get("priority") == True:
        total += priority_fee
    else:
        total += shipping_fee

    db.execute("INSERT INTO audit_log VALUES(" + str(total) + ")")
    cache.set(order["id"], total)
    logger.info("processed", extra={"order_id": order["id"], "total": total})
    analytics.track("order_processed", {"id": order["id"], "total": total})
    email_client.send(order["customer_email"], "Your total is " + str(total))

    for _ in range(retry_limit):
        if flags.get("requeue"):
            db.execute("UPDATE orders SET state='queued' WHERE id=" + str(order["id"]))

    return {"order_id": order["id"], "total": total}
