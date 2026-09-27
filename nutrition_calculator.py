import math


def estimate_nutrition_targets(profile, activity_factor):
    """
    Estimate full-day maintenance calories and a protein reference.

    These are starting estimates for generally healthy adults.
    The activity factor must cover the whole day, including workouts.
    """

    age = profile["age"]
    weight = profile["weight_kg"]
    height = profile["height_cm"]
    calculation_sex = profile["calculation_sex"]

    if not 18 <= age <= 65:
        raise ValueError(
            "This prototype's automatic estimates support ages 18–65. "
            "Use individually established targets outside that range."
        )

    if calculation_sex not in ("Male", "Female"):
        raise ValueError(
            "Automatic calorie estimation needs a calculation-sex "
            "option. Otherwise, enter your own nutrition targets."
        )

    values = [weight, height, activity_factor]

    if not all(math.isfinite(value) and value > 0 for value in values):
        raise ValueError("Enter valid positive measurements.")

    if not 1.2 <= activity_factor <= 2.5:
        raise ValueError("The activity factor must be between 1.2 and 2.5.")

    # Mifflin–St Jeor: estimated resting energy expenditure.
    sex_constant = 5 if calculation_sex == "Male" else -161

    resting_calories = (
        10 * weight
        + 6.25 * height
        - 5 * age
        + sex_constant
    )

    if resting_calories <= 0:
        raise ValueError("Please check the age, height and weight.")

    # Workouts are already included in this multiplier.
    # Do not add workout calories again.
    maintenance_calories = resting_calories * activity_factor

    trains_regularly = profile["training_days"] > 0

    if trains_regularly:
        protein_low = 1.4 * weight
        protein_high = 2.0 * weight
        protein_note = (
            "General reference range for healthy exercising adults. "
            "Individual needs depend on training and other factors."
        )
    else:
        protein_low = 0.8 * weight
        protein_high = 0.8 * weight
        protein_note = (
            "General adult protein reference, not a personalized "
            "sports or muscle-building target."
        )

    notes = [
        "These figures cover the entire day, including existing meals.",
        "Calorie needs are estimates; actual requirements can differ.",
        protein_note
    ]

    if profile["goal"] == "Build muscle":
        notes.append(
            "Maintenance calories are shown first. A muscle-gain "
            "calorie adjustment must be chosen separately; selecting "
            "this goal alone does not determine a suitable surplus."
        )

    if profile["goal"] == "Sports performance":
        notes.append(
            "Sport-specific carbohydrate needs and training-day "
            "fueling are not calculated by this basic estimator."
        )

    return {
        "resting_calories": round(resting_calories),
        "maintenance_calories": round(maintenance_calories),
        "protein_low_g": round(protein_low, 1),
        "protein_high_g": round(protein_high, 1),
        "activity_factor": activity_factor,
        "notes": notes
    }