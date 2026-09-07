"""
app.py — Flask application entry point.

Routes are registered one-to-one with the 10 operationIds in openapi.yaml.
Each route delegates entirely to the matching function in handlers.py and
wraps the returned (body, status) tuple in jsonify().
"""
import os
import sys

# Ensure src/ is importable regardless of the working directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, jsonify

import handlers

app = Flask(__name__)


def respond(result):
    """Convert a (body: dict|list, status: int) tuple into a Flask Response."""
    body, status = result
    return jsonify(body), status


# ── Menu ──────────────────────────────────────────────────────────────────────

@app.route("/menu", methods=["GET"])
def list_menu():
    return respond(handlers.list_menu())


@app.route("/menu/<int:id>", methods=["GET"])
def get_menu_item(id):
    return respond(handlers.get_menu_item(id))


# ── Customers ─────────────────────────────────────────────────────────────────

@app.route("/customers", methods=["POST"])
def create_customer():
    return respond(handlers.create_customer())


# ── Dining Tables ─────────────────────────────────────────────────────────────

@app.route("/tables", methods=["GET"])
def list_dining_tables():
    return respond(handlers.list_dining_tables())


# ── Reservations ──────────────────────────────────────────────────────────────

@app.route("/reservations", methods=["POST"])
def create_reservation():
    return respond(handlers.create_reservation())


@app.route("/reservations/<int:id>", methods=["GET"])
def get_reservation(id):
    return respond(handlers.get_reservation(id))


# ── Orders ────────────────────────────────────────────────────────────────────

@app.route("/orders", methods=["POST"])
def create_order():
    return respond(handlers.create_order())


@app.route("/orders/<int:id>", methods=["GET"])
def get_order(id):
    return respond(handlers.get_order(id))


@app.route("/orders/<int:id>/status", methods=["PATCH"])
def update_order_status(id):
    return respond(handlers.update_order_status(id))


@app.route("/customers/<int:id>/orders", methods=["GET"])
def list_customer_orders(id):
    return respond(handlers.list_customer_orders(id))


# ── Dev server entry point ────────────────────────────────────────────────────

if __name__ == "__main__":
    app.run(debug=True)
