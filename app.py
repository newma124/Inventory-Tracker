from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func, nullslast
import os
import re
from sqlalchemy.exc import IntegrityError

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "app.db")

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DB_PATH}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = "dev-secret"  # replace in production

app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "isolation_level": "SERIALIZABLE",
    "connect_args": {"timeout": 10},
}

db = SQLAlchemy(app)

# ── Models ───────────────────────────────────────────────────────────────────
class Category(db.Model):
    __tablename__ = "categories"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False, index=True)

class Location(db.Model):
    __tablename__ = "locations"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False, index=True)

class Status(db.Model):
    __tablename__ = "statuses"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False, index=True)

class Condition(db.Model):
    __tablename__ = "conditions"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False, index=True)
    sort_rank = db.Column(db.Integer, nullable=False, default=999, index=True)

class Item(db.Model):
    __tablename__ = "items"
    __table_args__ = (
        # Supports /items and /report filters by category, location, and status.
        db.Index("ix_items_category_location_status", "category_id", "location_id", "status_id"),
        # Supports report date-range filtering by purchase date.
        db.Index("ix_items_purchase_date", "purchase_date"),
        # Supports price range filters and price sorting on /items.
        db.Index("ix_items_unit_cost", "unit_cost"),
        # Supports condition sorting and filtering on /items.
        db.Index("ix_items_condition", "condition_id"),
    )
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, index=True)

    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=False)
    location_id = db.Column(db.Integer, db.ForeignKey("locations.id"), nullable=False)
    status_id = db.Column(db.Integer, db.ForeignKey("statuses.id"), nullable=False)
    condition_id = db.Column(db.Integer, db.ForeignKey("conditions.id"), nullable=False)

    quantity = db.Column(db.Integer, nullable=False, default=1)
    purchase_date = db.Column(db.Date, nullable=True)
    unit_cost = db.Column(db.Float, nullable=True)
    notes = db.Column(db.Text)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    category = db.relationship("Category")
    location = db.relationship("Location")
    status = db.relationship("Status")
    condition = db.relationship("Condition")

    def __repr__(self):
        return f"<Item {self.id} {self.name!r}>"

# ── Helpers ──────────────────────────────────────────────────────────────────
def clean_text(value, max_len=200):
    """Basic input sanitization for normal text fields.
    SQL injection is primarily prevented by SQLAlchemy parameter binding;
    this function removes control characters and limits length.
    """
    value = (value or "").strip()
    value = re.sub(r"[\x00-\x1f\x7f]", "", value)
    return value[:max_len]


def parse_int(value, default=0, minimum=None, maximum=None):
    try:
        n = int(value)
    except (TypeError, ValueError):
        return default
    if minimum is not None and n < minimum:
        return minimum
    if maximum is not None and n > maximum:
        return maximum
    return n


def parse_float(value, default=None, minimum=None, maximum=None):
    if value in (None, ""):
        return default
    try:
        n = float(value)
    except (TypeError, ValueError):
        return default
    if minimum is not None and n < minimum:
        return minimum
    if maximum is not None and n > maximum:
        return maximum
    return n

def parse_date(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None

def get_or_create_lookup(model, raw_name, default_rank=None):
    name = (raw_name or "").strip()
    if not name:
        return None

    existing = model.query.filter(func.lower(model.name) == name.lower()).first()
    if existing:
        return existing

    if model is Condition:
        obj = model(name=name, sort_rank=default_rank if default_rank is not None else 999)
    else:
        obj = model(name=name)

    db.session.add(obj)
    db.session.flush()
    return obj


def load_form_lists():
    return {
        "cats": Category.query.order_by(Category.name).all(),
        "locs": Location.query.order_by(Location.name).all(),
        "statuses": Status.query.order_by(Status.name).all(),
        "conditions": Condition.query.order_by(Condition.sort_rank.asc(), Condition.name.asc()).all(),
    }

# ── Routes ───────────────────────────────────────────────────────────────────
@app.get("/")
def home():
    return redirect(url_for("list_items"))

@app.get("/items")
def list_items():
    q = request.args.get("q", "").strip()
    item_id = request.args.get("item_id", "").strip()
    condition_id = request.args.get("condition_id", "").strip()
    location_id = request.args.get("location_id", "").strip()
    category_id = request.args.get("category_id", "").strip()
    status_id = request.args.get("status_id", "").strip()
    price_min = request.args.get("price_min", "").strip()
    price_max = request.args.get("price_max", "").strip()
    sort_by = request.args.get("sort_by", "created_desc").strip()

    query = Item.query.join(Category).join(Location).join(Status).join(Condition)

    if item_id:
        try:
            query = query.filter(Item.id == int(item_id))
        except ValueError:
            pass

    if q:
        like = f"%{q}%"
        query = query.filter(db.or_(Item.name.ilike(like), Item.notes.ilike(like)))

    if condition_id:
        query = query.filter(Item.condition_id == int(condition_id))
    if location_id:
        query = query.filter(Item.location_id == int(location_id))
    if category_id:
        query = query.filter(Item.category_id == int(category_id))
    if status_id:
        query = query.filter(Item.status_id == int(status_id))

    if price_min:
        try:
            query = query.filter((Item.unit_cost != None) & (Item.unit_cost >= float(price_min)))
        except ValueError:
            pass
    if price_max:
        try:
            query = query.filter((Item.unit_cost != None) & (Item.unit_cost <= float(price_max)))
        except ValueError:
            pass

    if sort_by == "condition_best":
        query = query.order_by(Condition.sort_rank.asc(), Item.name.asc())
    elif sort_by == "condition_worst":
        query = query.order_by(Condition.sort_rank.desc(), Item.name.asc())
    elif sort_by == "name_asc":
        query = query.order_by(Item.name.asc())
    elif sort_by == "name_desc":
        query = query.order_by(Item.name.desc())
    elif sort_by == "price_asc":
        query = query.order_by(nullslast(Item.unit_cost.asc()), Item.name.asc())
    elif sort_by == "price_desc":
        query = query.order_by(nullslast(Item.unit_cost.desc()), Item.name.asc())
    else:
        query = query.order_by(Item.created_at.desc())

    items = query.all()

    total_items = len(items)
    total_quantity = sum(it.quantity for it in items)
    total_value = sum((it.unit_cost or 0) * (it.quantity or 0) for it in items)

    lists = load_form_lists()

    return render_template(
        "items_list.html",
        items=items,
        q=q,
        item_id=item_id,
        condition_id=condition_id,
        location_id=location_id,
        category_id=category_id,
        status_id=status_id,
        price_min=price_min,
        price_max=price_max,
        sort_by=sort_by,
        total_items=total_items,
        total_quantity=total_quantity,
        total_value=total_value,
        **lists,
    )

@app.get("/items/new")
def new_item():
    return render_template("item_form.html", item=None, **load_form_lists())

@app.post("/items")
def create_item():
    name = clean_text(request.form.get("name"), 200)
    if not name:
        flash("Name is required.", "error")
        return redirect(url_for("new_item"))

    try:
        # Explicit write transaction. Either all lookup rows + the item are saved,
        # or none are saved if an error occurs.
        with db.session.begin():
            category = get_or_create_lookup(Category, request.form.get("category_name"))
            location = get_or_create_lookup(Location, request.form.get("location_name"))
            status = get_or_create_lookup(Status, request.form.get("status_name"))
            condition = get_or_create_lookup(Condition, request.form.get("condition_name"), default_rank=999)

            if not category or not location or not status or not condition:
                raise ValueError("Category, location, status, and condition are required.")

            item = Item(
                name=name,
                category_id=category.id,
                location_id=location.id,
                status_id=status.id,
                condition_id=condition.id,
                quantity=parse_int(request.form.get("quantity"), default=1, minimum=0),
                purchase_date=parse_date(request.form.get("purchase_date")),
                unit_cost=parse_float(request.form.get("unit_cost"), default=None, minimum=0),
                notes=clean_text(request.form.get("notes"), 2000) or None,
            )
            db.session.add(item)

        flash("Item created.", "success")
        return redirect(url_for("list_items"))

    except ValueError as exc:
        db.session.rollback()
        flash(str(exc), "error")
        return redirect(url_for("new_item"))
    except IntegrityError:
        db.session.rollback()
        flash("That value already exists or violates a database constraint.", "error")
        return redirect(url_for("new_item"))

@app.get("/items/<int:item_id>")
def show_item(item_id):
    item = Item.query.get_or_404(item_id)
    return render_template("item_detail.html", item=item)

@app.get("/items/<int:item_id>/edit")
def edit_item(item_id):
    item = Item.query.get_or_404(item_id)
    return render_template("item_form.html", item=item, **load_form_lists())

@app.post("/items/<int:item_id>/update")
def update_item(item_id):
    item = Item.query.get_or_404(item_id)

    name = clean_text(request.form.get("name"), 200)
    if not name:
        flash("Name is required.", "error")
        return redirect(url_for("edit_item", item_id=item.id))

    try:
        # Explicit write transaction. The lookup table changes and item update
        # commit together or roll back together.
        with db.session.begin():
            category = get_or_create_lookup(Category, request.form.get("category_name"))
            location = get_or_create_lookup(Location, request.form.get("location_name"))
            status = get_or_create_lookup(Status, request.form.get("status_name"))
            condition = get_or_create_lookup(
                Condition,
                request.form.get("condition_name"),
                default_rank=item.condition.sort_rank if item.condition else 999,
            )

            if not category or not location or not status or not condition:
                raise ValueError("Category, location, status, and condition are required.")

            item.name = name
            item.category_id = category.id
            item.location_id = location.id
            item.status_id = status.id
            item.condition_id = condition.id
            item.quantity = parse_int(request.form.get("quantity"), default=1, minimum=0)
            item.purchase_date = parse_date(request.form.get("purchase_date"))
            item.unit_cost = parse_float(request.form.get("unit_cost"), default=None, minimum=0)
            item.notes = clean_text(request.form.get("notes"), 2000) or None

        flash("Item updated.", "success")
        return redirect(url_for("show_item", item_id=item.id))
    
    except ValueError as exc:
        db.session.rollback()
        flash(str(exc), "error")
        return redirect(url_for("edit_item", item_id=item.id))
    except IntegrityError:
        db.session.rollback()
        flash("That value already exists or violates a database constraint.", "error")
        return redirect(url_for("edit_item", item_id=item.id))

@app.post("/items/<int:item_id>/delete")
def delete_item(item_id):
    item = Item.query.get_or_404(item_id)
    try:
        with db.session.begin():
            db.session.delete(item)
        flash("Item deleted.", "success")
    except Exception:
        db.session.rollback()
        flash("Could not delete item.", "error")
    return redirect(url_for("list_items"))

@app.get("/report")
def report():
    cat_id = request.args.get("category_id") or None
    loc_id = request.args.get("location_id") or None
    status_id = request.args.get("status_id") or None
    start = request.args.get("start") or ""
    end = request.args.get("end") or ""

    q = Item.query.join(Category).join(Location).join(Status).join(Condition)
    if cat_id:
        q = q.filter(Item.category_id == int(cat_id))
    if loc_id:
        q = q.filter(Item.location_id == int(loc_id))
    if status_id:
        q = q.filter(Item.status_id == int(status_id))
    if start:
        q = q.filter(Item.purchase_date >= datetime.strptime(start, "%Y-%m-%d").date())
    if end:
        q = q.filter(Item.purchase_date <= datetime.strptime(end, "%Y-%m-%d").date())

    rows = q.order_by(Item.name).all()

    total_qty = sum(r.quantity for r in rows)
    total_value = sum((r.unit_cost or 0) * (r.quantity or 0) for r in rows)
    avg_unit_cost = (sum((r.unit_cost or 0) for r in rows) / len(rows)) if rows else 0

    by_category = dict(
        db.session.query(Category.name, func.count(Item.id))
        .join(Item, Item.category_id == Category.id)
        .group_by(Category.name)
        .all()
    )

    return render_template(
        "report.html",
        rows=rows,
        total_qty=total_qty,
        total_value=total_value,
        avg_unit_cost=avg_unit_cost,
        by_category=by_category,
        cat_id=cat_id,
        loc_id=loc_id,
        status_id=status_id,
        start=start,
        end=end,
        **load_form_lists(),
    )

# ── Run (create tables; seed; clean shutdown) ───────────────────────────────
if __name__ == "__main__":
    with app.app_context():
        db.create_all()

        db.session.commit()

        print("Registered routes:")
        for rule in app.url_map.iter_rules():
            print(" ", rule)

    try:
        app.run(debug=True, use_reloader=False)
    except KeyboardInterrupt:
        print("Shutting down…")