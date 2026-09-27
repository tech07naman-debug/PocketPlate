import re


def normalize(text):
    """Make food names easier to compare."""
    return re.sub(r"[^a-z0-9]+", " ", str(text).lower()).strip()


def filter_foods(profile, catalogue):
    allowed_diets = {
        "Vegetarian — dairy allowed, no eggs": {
            "vegan", "vegetarian"
        },
        "Vegetarian + eggs": {
            "vegan", "vegetarian", "eggetarian"
        },
        "Vegan": {
            "vegan"
        },
        "Non-vegetarian": {
            "vegan", "vegetarian", "eggetarian", "nonvegetarian"
        }
    }

    allowed_equipment = {
        "No cooking equipment": {"none"},
        "Kettle only": {"none", "kettle"},
        "Full kitchen": {"none", "kettle", "kitchen"}
    }

    allergen_mapping = {
        "Milk / dairy": "milk",
        "Eggs": "eggs",
        "Peanuts": "peanuts",
        "Tree nuts": "tree_nuts",
        "Soy": "soy",
        "Wheat / gluten": "wheat",
        "Fish": "fish",
        "Shellfish": "shellfish",
        "Sesame": "sesame"
    }

    if profile["diet"] not in allowed_diets:
        raise ValueError("Unknown diet preference. Save your profile again.")

    if profile["cooking_access"] not in allowed_equipment:
        raise ValueError("Unknown cooking option. Save your profile again.")

    # The demo catalogue cannot reliably assess free-text allergies.
    if profile.get("other_allergies", "").strip():
        raise ValueError(
            "This catalogue cannot verify the additional allergy you "
            "entered. Its ingredients need checking before a plan can "
            "be generated. Do not remove a real allergy to bypass this."
        )

    # Wheat tags alone cannot establish that foods are gluten-free.
    if "Wheat / gluten" in profile["allergies"]:
        raise ValueError(
            "The demo catalogue does not contain verified gluten and "
            "cross-contact information. Use a verified food catalogue "
            "before generating a plan for this restriction."
        )

    blocked_allergens = {
        allergen_mapping[allergy]
        for allergy in profile["allergies"]
    }

    disliked_terms = [
        normalize(term)
        for term in profile.get("disliked_foods", "").split(",")
        if normalize(term)
    ]

    def matches_dislike(food, term):
        food_words = set(
            normalize(f"{food['id']} {food['name']}").split()
        )
        return set(term.split()).issubset(food_words)

    # Avoid silently ignoring a restriction we did not understand.
    unknown_dislikes = [
        term
        for term in disliked_terms
        if not any(
            matches_dislike(food, term)
            for food in catalogue
        )
    ]

    if unknown_dislikes:
        raise ValueError(
            "These dislikes could not be matched to catalogue names: "
            + ", ".join(unknown_dislikes)
            + ". Use food names from the price table, separated by commas."
        )

    available = []
    excluded = []

    for original_food in catalogue:
        food = original_food.copy()
        reasons = []

        if food["diet"] not in allowed_diets[profile["diet"]]:
            reasons.append("Does not match your diet")

        if (
            food["equipment"]
            not in allowed_equipment[profile["cooking_access"]]
        ):
            reasons.append("Needs cooking equipment you do not have")

        food_allergens = {
            item.strip().lower()
            for item in str(food["allergens"]).split(";")
            if item.strip()
        }

        if food_allergens & blocked_allergens:
            reasons.append("Contains an excluded allergen in this catalogue")

        if any(
            matches_dislike(food, term)
            for term in disliked_terms
        ):
            reasons.append("Listed among your disliked foods")

        # Conservative storage assumption for these demo items.
        if (
            not profile["fridge_access"]
            and food["id"] in {"milk", "curd"}
        ):
            reasons.append(
                "This demo assumes refrigerated storage for milk and curd"
            )

        if reasons:
            excluded.append({
                "Food": food["name"],
                "Reason": "; ".join(reasons)
            })
        else:
            available.append(food)

    return available, excluded

import numpy as np
from scipy.optimize import milp, Bounds, LinearConstraint


def generate_plan(foods, targets, daily_budget):
    if not foods:
        raise ValueError("No foods match your saved preferences.")

    if not np.isfinite(daily_budget) or daily_budget <= 0:
        raise ValueError("Enter a valid positive budget.")

    nutrient_keys = ["calories", "protein_g"]
    goals = [targets["calories"], targets["protein"]]

    if targets.get("fibre") is not None and targets["fibre"] > 0:
        nutrient_keys.append("fibre_g")
        goals.append(targets["fibre"])

    goals = np.array(goals, dtype=float)

    if not np.all(np.isfinite(goals)) or np.any(goals <= 0):
        raise ValueError("Nutrition targets must be positive numbers.")

    prices = np.array([food["price_inr"] for food in foods], dtype=float)
    limits = np.array([food["max_servings"] for food in foods], dtype=float)

    nutrients = np.array([
        [food[key] for food in foods]
        for key in nutrient_keys
    ], dtype=float)

    for values in [prices, limits, nutrients]:
        if not np.all(np.isfinite(values)) or np.any(values < 0):
            raise ValueError("Check the catalogue's numeric values.")

    if np.any(limits % 1 != 0):
        raise ValueError("Serving limits must be whole numbers.")

    n = len(foods)
    k = len(goals)

    # Variables: food portions, nutrient shortfalls, nutrient excesses.
    # Compare proportional differences so calories don't dominate grams.
    objective = np.concatenate([
        0.001 * prices / daily_budget,
        1 / goals,
        1 / goals
    ])

    nutrient_rows = np.hstack([
        nutrients,
        np.eye(k),
        -np.eye(k)
    ])

    budget_row = np.concatenate([prices, np.zeros(2 * k)])

    result = milp(
        c=objective,
        integrality=np.concatenate([
            np.ones(n),
            np.zeros(2 * k)
        ]),
        bounds=Bounds(
            lb=np.zeros(n + 2 * k),
            ub=np.concatenate([limits, np.full(2 * k, np.inf)])
        ),
        constraints=[
            LinearConstraint(nutrient_rows, goals, goals),
            LinearConstraint(budget_row, -np.inf, daily_budget)
        ],
        options={"time_limit": 10.0}
    )

    if result.status not in (0, 1) or result.x is None:
        raise ValueError(
            "No usable plan was found. Review your budget and food choices."
        )

    raw_portions = result.x[:n]
    portions = np.rint(raw_portions).astype(int)
    cost = float(prices @ portions)

    # Verify the returned portions before showing them.
    if (
        np.any(np.abs(raw_portions - portions) > 1e-5)
        or np.any(portions < 0)
        or np.any(portions > limits)
        or cost > daily_budget + 1e-6
    ):
        raise ValueError("The generated plan failed validation.")

    if not portions.any():
        raise ValueError(
            "No useful food combination was selected within this budget. "
            "Review prices, budget, and eligible foods."
        )

    items = []

    for food, count in zip(foods, portions):
        if count > 0:
            items.append({
                "Food": food["name"],
                "One portion": food["portion"],
                "Portions/day": int(count),
                "Cost/day (₹)": round(float(food["price_inr"] * count), 2)
            })

    totals = {
        key: float(sum(
            food[key] * int(count)
            for food, count in zip(foods, portions)
        ))
        for key in [
            "calories", "protein_g", "carbs_g", "fat_g", "fibre_g"
        ]
    }

    return {
        "items": items,
        "totals": totals,
        "cost": cost,
        "optimal": result.status == 0
    }