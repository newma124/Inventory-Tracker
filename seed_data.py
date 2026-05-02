from datetime import date, timedelta
from random import choice, randint, uniform
from app import app, db, Item, Category, Location, Status, Condition, get_or_create_lookup

sample_categories = [
    "Electronics", "Storage", "Tools", "Food And Water", "Cleaning", "Clothing", "Cables"
]

sample_locations = [
    "Storage A", "Unknown", "Basement", "Robotics Floor", "Storage Bins",
    "Outbound Dock", "Garage", "IT Room", "Inbound Dock", "Locker Room"
]

sample_statuses = [
    "Stored", "In Use", "Out of Service", "Missing", "Needs Repair", "Unknown"
]

sample_conditions = [
    ("New", 1),
    ("Good", 2),
    ("Fair", 3),
    ("Poor", 4),
    ("Broken", 5)
]

sample_names = [
    "Cart", "2x4", "Water", "Bandage", "Safety Vest",
    "Electrical Tape", "Duct Tape", "Measuring Tape", "Screwdriver Set", "Wrench",
    "Flashlight", "Monitor", "Ear Plugs", "Bleach", "Gloves",
    "Ice", "Flash Drive", "Pliers", "Ethernet Cable",
    "Hammer", "Toolbox", "Scanner", "Bolts", "Extension Cord",
    "Power Strip", "Tablet", "Speaker", "Power Drill", "Storage Box", "Batteries"
]

notes = [
    "Works well.",
    "Used frequently.",
    "Backup item.",
    "Needs to be checked.",
    "Stored for later use.",
    "Slight wear.",
    "Recently purchased.",
    "May need replacement soon."
]

with app.app_context():
    # Create lookup values
    categories = [get_or_create_lookup(Category, name) for name in sample_categories]
    locations = [get_or_create_lookup(Location, name) for name in sample_locations]
    statuses = [get_or_create_lookup(Status, name) for name in sample_statuses]

    conditions = []
    for name, rank in sample_conditions:
        conditions.append(get_or_create_lookup(Condition, name, default_rank=rank))

    # Create 60 sample items
    for i in range(60):
        item = Item(
            name=f"{choice(sample_names)} #{i + 1}",
            category_id=choice(categories).id,
            location_id=choice(locations).id,
            status_id=choice(statuses).id,
            condition_id=choice(conditions).id,
            quantity=randint(1, 5),
            unit_cost=round(uniform(5.00, 500.00), 2),
            purchase_date=date.today() - timedelta(days=randint(0, 900)),
            notes=choice(notes),
        )
        db.session.add(item)

    db.session.commit()
    print("Inserted 60 sample inventory items.")