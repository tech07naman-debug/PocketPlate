import hashlib 
# a python in-built module for secure hashing and message digests.
from pathlib import Path
# used as an alternative to os.path, simple, modern and lesser error prone to use.
import pandas as pd
import streamlit as st
from google.genai import errors
from food_analyzer import analyze_food_label
from nutrition_calculator import estimate_nutrition_targets
from meal_planner import filter_foods, generate_plan
st.set_page_config(
    page_title="PocketPlate",
    page_icon="🥗",
    layout="wide"
)
from pocketplate_ui import apply_theme, hero, planner_steps, nutrient_cards

with st.sidebar:
    st.markdown('<div class="pp-brand">PocketPlate</div><p class="pp-tagline">Eat smarter. Spend better.</p>', unsafe_allow_html=True)
    selected_page = st.radio("Choose a page", ["Food Scanner", "Meal Planner"], key="navigation")
    st.markdown('<div class="pp-side-note"><b>A little clarity. A better plate.</b><br>Read a label or build a plan around your budget.<br><br>Saved details stay in this session only.</div>', unsafe_allow_html=True)

apply_theme(selected_page)
hero(selected_page)

NUTRIENTS = {
    "calories_kcal": ("Energy", "kcal"),
    "protein_g": ("Protein", "g"),
    "carbs_g": ("Carbohydrates", "g"),
    "fat_g": ("Fat", "g"),
    "fibre_g": ("Fibre", "g"),
    "total_sugar_g": ("Total sugar", "g"),
    "added_sugar_g": ("Added sugar", "g"),
    "sodium_mg": ("Sodium", "mg")
}
if selected_page == "Food Scanner":
    st.subheader("01 / Add your label photos", anchor=False)
    st.write(
        "Upload the ingredients list and nutrition panel "
        "from the same product."
    )
    st.markdown(
        """
        <p style="font-size: 16px; font-weight: 700; color: #172B4D;">
            Up to 3 JPG or PNG photos, 10 MB combined.
            Analyze sends the photos to Google's Gemini API.
        </p>
        """,
        unsafe_allow_html=True
    )
    uploaded_files = st.file_uploader(
        "Choose label photos",
        type=["jpg", "jpeg", "png"],
        accept_multiple_files=True
    )
    upload_problem = None
    if len(uploaded_files or []) > 3:
        upload_problem = "Choose up to three photos of the same product."
    elif sum(file.size for file in (uploaded_files or [])) > 10 * 1024 * 1024:
        upload_problem = "Your photos exceed 10 MB combined. Remove or resize a photo."
    if upload_problem:
        st.error(upload_problem)

    if uploaded_files and not upload_problem:
        columns = st.columns(2) if len(uploaded_files) > 1 else st.columns(1)
        for index, file in enumerate(uploaded_files):
            with columns[index % len(columns)]:
                st.image(
                    file,
                    caption=f"Photo {index + 1}",
                    width="stretch"
                )
    photo_id = hashlib.sha256(
        "|".join(
            hashlib.sha256(file.getvalue()).hexdigest()
            for file in (uploaded_files or [])
        ).encode()
    ).hexdigest()
    if st.session_state.get("current_photos") != photo_id:
        st.session_state["current_photos"] = photo_id
        st.session_state.pop("label_data", None)
    if uploaded_files:
        if st.button("Analyze your food ↗", type="primary", key="analyze_food", disabled=bool(upload_problem)):
            st.session_state.pop("label_data", None)
            try:
                with st.spinner("Reading your food label with Gemini…"):
                    st.session_state["label_data"] = (
                        analyze_food_label(uploaded_files)
                    )
            except errors.APIError as error:
                if error.code == 429:
                    st.error(
                        "Gemini's usage limit was reached. "
                        "Check your quota in Google AI Studio."
                    )
                else:
                    st.error(
                        f"Gemini API error: {error.code}. "
                        "Check your API key and model access."
                    )
            except ValueError as error:
                st.error(str(error))
            except Exception as error:
                import logging
                logging.getLogger(__name__).exception("Food label analysis failed")
                st.error("The scanner could not complete this request. Your photos have not been analyzed.")
                st.caption(f"Error type: {type(error).__name__}. Check the local terminal for details before trying again.")
    data = st.session_state.get("label_data")
    if data:
        st.divider()
        st.subheader(data["product_name"], anchor = False)
        st.markdown(data["explanation"])
        st.subheader("Numbers read from your photo", anchor = False)
        st.write(f"**Label basis:** {data['basis_text']}")
        st.caption(
            "Check these against your packet. If a number is wrong, "
            "upload a clearer photo before calculating."
        )
        extracted_rows = []
        for key, (name, unit) in NUTRIENTS.items():
            value = data["nutrition"][key]
            extracted_rows.append({
                "Nutrient": name,
                "Label value": (
                    f"{value:g} {unit}"
                    if value is not None
                    else "Not available"
                )
            })
        st.table(extracted_rows)
        st.subheader("How much will you eat?", anchor = False)
        col1, col2 = st.columns(2)
        with col1:
            packet_weight = st.number_input(
                "Total packet weight (g)",
                min_value=0.1,
                value=None,
                placeholder="For example, 90",
                key=f"packet_{photo_id}"
            )
        with col2:
            portion_weight = st.number_input(
                "Amount eaten at one time (g)",
                min_value=0.1,
                value=None,
                placeholder="For example, 30",
                key=f"portion_{photo_id}"
            )
        if packet_weight is not None and portion_weight is not None:
            if portion_weight > packet_weight:
                st.error(
                    "The amount eaten cannot exceed this packet's weight."
                )
            else:
                basis = data["basis"]
                # The denominator comes from the selected label column.
                if basis == "per_100g":
                    reference_weight = 100.0
                elif basis == "per_serving":
                    reference_weight = data["serving_weight_g"]
                elif basis == "per_package":
                    reference_weight = packet_weight
                else:
                    reference_weight = None
                if not reference_weight or reference_weight <= 0:
                    st.warning(
                        "The photo does not provide a usable nutrition "
                        "basis in grams. Upload a clearer photo showing "
                        "the column heading and serving size. "
                        "Labels based only on millilitres need a "
                        "volume calculator."
                    )
                else:
                    multiplier = portion_weight / reference_weight
                    st.subheader(
                        f"Nutrition in your {portion_weight:g} g portion", anchor = False
                    )
                    portion_rows = []
                    for key, (name, unit) in NUTRIENTS.items():
                        value = data["nutrition"][key]
                        portion_rows.append({
                            "Nutrient": name,
                            "Your portion": (
                                f"{value * multiplier:.1f} {unit}"
                                if value is not None
                                else "Not available"
                            )
                        })
                    st.table(portion_rows)
                    st.caption(
                        "Calculated from label values, which may be rounded."
                    )
                    with st.expander("Optional: calorie-to-activity comparison"):
                        st.write(
                            "Compare your portion's energy with estimated "
                            "energy used during activity. You do not need "
                            "to exercise to compensate for eating."
                        )
                        label_calories = data["nutrition"]["calories_kcal"]
                        if label_calories is None:
                            st.info(
                                "Calories were not readable on the label, "
                                "so this comparison is unavailable."
                            )
                        else:
                            portion_calories = label_calories * multiplier
                            body_weight = st.number_input(
                                "Your body weight (kg)",
                                min_value=1.0,
                                value=None,
                                placeholder="Enter your weight",
                                key=f"body_weight_{photo_id}"
                            )
                            if body_weight is not None:
                                # Standard activity intensity estimates.
                                activities = {
                                    "Walking on a treadmill, 4.8–5.5 km/h, flat": 3.8,
                                    "Cycling outdoors, 16–19 km/h": 6.8
                                }
                                activity_rows = []
                                for activity, met in activities.items():
                                    kcal_per_minute = (
                                        met * 3.5 * body_weight / 200
                                    )
                                    minutes = (
                                        portion_calories / kcal_per_minute
                                    )
                                    activity_rows.append({
                                        "Activity": activity,
                                        "Approximate time": (
                                            f"{minutes:.0f} minutes"
                                            if minutes >= 1
                                            else (
                                                "Under 1 minute"
                                                if minutes > 0
                                                else "0 minutes"
                                            )
                                        )
                                    })
                                st.write(
                                    f"Energy in your portion: "
                                    f"**{portion_calories:.1f} kcal**"
                                )
                                st.table(activity_rows)
                                st.caption(
                                    "Rough adult estimates, including energy "
                                    "your body would use at rest. Actual "
                                    "expenditure varies with fitness, terrain "
                                    "and other factors. Exercise does not "
                                    "remove allergens or cancel other "
                                    "dietary concerns."
                                )
                                st.markdown(
                                    "Activity references: "
                                    "[Walking](https://pacompendium.com/walking/) · "
                                    "[Cycling](https://pacompendium.com/bicycling/)"
                                )
if selected_page == "Meal Planner":
    steps_slot = st.empty()
    saved_profile = st.session_state.get("personal_profile", {})
    def saved_index(options, field):
        value = saved_profile.get(field)
        return options.index(value) if value in options else 0
    with st.expander("01 / Your profile · routine, budget & preferences", expanded=not bool(saved_profile)):
        with st.form("personal_profile_form"):
            st.subheader("1. About you", anchor = False)
            col1, col2 = st.columns(2)
            with col1:
                age = st.number_input('Age (years)', min_value=1, max_value=120, value=saved_profile.get('age', None))
                height_cm = st.number_input('Height (cm)', min_value=1.0, max_value=260.0, value=saved_profile.get('height_cm', None))
            with col2:
                weight_kg = st.number_input('Body weight (kg)', min_value=1.0, max_value=400.0, value=saved_profile.get('weight_kg', None))
                calculation_sex = st.selectbox('Sex used for the energy calculation', ['Select an option', 'Female', 'Male', 'Prefer not to specify'], help='Some adult energy formulas use sex-specific coefficients. This is separate from gender identity. If you prefer not to specify, we can use targets you provide instead.', index=saved_index(['Select an option', 'Female', 'Male', 'Prefer not to specify'], 'calculation_sex'))
            st.subheader("2. Your goal and routine", anchor = False)
            goal = st.selectbox('What do you want this plan to support?', ['Maintain my current weight', 'Sports performance', 'Build muscle'], index=saved_index(['Maintain my current weight', 'Sports performance', 'Build muscle'], 'goal'))
            daily_activity = st.selectbox('Usual activity outside workouts', ['Mostly sitting', 'Some walking and standing', 'A lot of walking or physical work'], help='Describe your normal day here. Record workouts separately below.', index=saved_index(['Mostly sitting', 'Some walking and standing', 'A lot of walking or physical work'], 'daily_activity'))
            training_type = st.text_input('Sport or workout type', placeholder='For example: badminton, weight training, or none', value=saved_profile.get('training_type', ''))
            col1, col2 = st.columns(2)
            with col1:
                training_days = st.number_input('Training days per week', min_value=0, max_value=7, value=saved_profile.get('training_days', 0))
            with col2:
                training_minutes = st.number_input('Typical total training minutes on a training day', min_value=0, max_value=600, value=saved_profile.get('training_minutes', 0), step=15)
            st.subheader("3. Your budget", anchor = False)
            monthly_budget = st.number_input('Monthly budget for the food in this plan (₹)', min_value=1.0, value=saved_profile.get('monthly_budget', None), placeholder='For example, 3000')
            budget_scope = st.radio('What should this budget cover?', ['All my meals', 'Extra food alongside my existing meals'], index=saved_index(['All my meals', 'Extra food alongside my existing meals'], 'budget_scope'))
            existing_meals = st.text_area('Existing meals, if you want an extra-food plan', placeholder='Describe breakfast, lunch and dinner, including approximate quantities. Leave blank for an all-meals plan.', help='A description helps us understand your routine. It does not provide an exact nutrient total.', value=saved_profile.get('existing_meals', ''))
            st.subheader("4. Food preferences and facilities", anchor = False)
            diet = st.selectbox('Diet preference', ['Vegetarian — dairy allowed, no eggs', 'Vegetarian + eggs', 'Vegan', 'Non-vegetarian'], index=saved_index(['Vegetarian — dairy allowed, no eggs', 'Vegetarian + eggs', 'Vegan', 'Non-vegetarian'], 'diet'))
            cooking_access = st.selectbox('Cooking access', ['No cooking equipment', 'Kettle only', 'Full kitchen'], index=saved_index(['No cooking equipment', 'Kettle only', 'Full kitchen'], 'cooking_access'))
            fridge_access = st.checkbox('I have access to a refrigerator', value=saved_profile.get('fridge_access', False))
            allergies = st.multiselect('Allergens to exclude', ['Milk / dairy', 'Eggs', 'Peanuts', 'Tree nuts', 'Soy', 'Wheat / gluten', 'Fish', 'Shellfish', 'Sesame'], default=saved_profile.get('allergies', []))
            other_allergies = st.text_input('Other allergies', placeholder='Leave blank if none', value=saved_profile.get('other_allergies', ''))
            disliked_foods = st.text_input('Foods you dislike or avoid', placeholder='For example: bananas, paneer', value=saved_profile.get('disliked_foods', ''))
            st.caption(
                "Always check actual product labels for ingredients "
                "and cross-contact warnings."
            )
            submitted = st.form_submit_button(
                "Save my profile",
                type="primary"
            )
    if submitted:
        problems = []
        if any(
            value is None
            for value in [age, height_cm, weight_kg, monthly_budget]
        ):
            problems.append(
                "Enter your age, height, weight and monthly budget."
            )
        if calculation_sex == "Select an option":
            problems.append(
                "Choose a calculation option, including "
                "'Prefer not to specify' if appropriate."
            )
        if training_days > 0:
            if training_minutes == 0:
                problems.append("Enter your training duration.")
            if not training_type.strip():
                problems.append("Enter your sport or workout type.")
        if training_days == 0 and training_minutes > 0:
            problems.append(
                "Set training minutes to zero if you do not train."
            )
        if (
            budget_scope == "Extra food alongside my existing meals"
            and not existing_meals.strip()
        ):
            problems.append(
                "Describe your existing meals for an extra-food plan."
            )
        if problems:
            for problem in problems:
                st.error(problem)
        else:
            st.session_state["personal_profile"] = {
                "age": age,
                "height_cm": height_cm,
                "weight_kg": weight_kg,
                "calculation_sex": calculation_sex,
                "goal": goal,
                "daily_activity": daily_activity,
                "training_type": training_type.strip(),
                "training_days": training_days,
                "training_minutes": training_minutes,
                "monthly_budget": monthly_budget,
                "budget_scope": budget_scope,
                "existing_meals": existing_meals.strip(),
                "diet": diet,
                "cooking_access": cooking_access,
                "fridge_access": fridge_access,
                "allergies": allergies,
                "other_allergies": other_allergies.strip(),
                "disliked_foods": disliked_foods.strip()
            }
            # A changed profile invalidates previous targets and plans.
            for key in [
                "planner_preferences",
                "nutrition_targets",
                "meal_plan"
            ]:
                st.session_state.pop(key, None)
    profile = st.session_state.get("personal_profile")
    if profile:
        st.success(
            "Profile saved for this session. "
            "After editing the form, save it again to apply changes."
        )
        col1, col2 = st.columns(2)
        col1.metric(
            "Monthly food budget",
            f"₹{profile['monthly_budget']:,.0f}"
        )
        col2.metric(
            "Average daily budget",
            f"₹{profile['monthly_budget'] / 30:.2f}"
        )
        st.write(f"**Goal:** {profile['goal']}")
        st.write(f"**Plan coverage:** {profile['budget_scope']}")
        st.caption("Budget calculations assume a 30-day month.")
        if profile["age"] < 18:
            st.info(
                "Automatic adult nutrition calculations will not be "
                "used for this profile. Appropriate targets would "
                "need guidance from a qualified professional."
            )
        if profile["calculation_sex"] == "Prefer not to specify":
            st.info(
                "We will provide a way to enter your own nutrition "
                "targets instead of using a sex-specific formula."
            )
    if profile:
        st.divider()
        st.subheader("02 / Set your daily targets", anchor=False)
        # Different profiles should get fresh target inputs.
        profile_key = hashlib.sha256(
            repr(profile).encode()
        ).hexdigest()[:12]
        extra_food_only = (
            profile["budget_scope"]
            == "Extra food alongside my existing meals"
        )
        adult_supported = 18 <= profile["age"] <= 65
        can_estimate = (
            adult_supported
            and profile["calculation_sex"] in ("Male", "Female")
            and not extra_food_only
        )
        if profile["age"] < 18:
            st.info(
                "This prototype does not generate nutrition targets "
                "or personalized food plans for under-18s."
            )
        else:
            estimated = None
            if extra_food_only:
                st.info(
                    "Enter only the EXTRA daily calories and protein "
                    "you want this food budget to provide. Your existing "
                    "meal description is not precise enough to calculate "
                    "a reliable nutrition shortfall automatically."
                )
            if can_estimate:
                target_mode = st.radio(
                    "How would you like to set your targets?",
                    [
                        "Start with an estimate",
                        "Enter my own targets"
                    ],
                    key=f"target_mode_{profile_key}"
                )
                if target_mode == "Start with an estimate":
                    st.caption(
                        "Choose an activity multiplier covering your "
                        "whole day, including training. Higher values "
                        "represent greater overall activity. This is "
                        "an approximate assumption you can adjust."
                    )
                    st.write(
                        f"**Saved routine:** {profile['daily_activity']}; "
                        f"{profile['training_days']} training days/week, "
                        f"{profile['training_minutes']} minutes/day "
                        "on training days."
                    )
                    activity_factor = st.slider(
                        "Whole-day activity multiplier",
                        min_value=1.2,
                        max_value=2.5,
                        value=1.4,
                        step=0.05,
                        key=f"activity_factor_{profile_key}"
                    )
                    st.caption(
                        "The initial value is a starting assumption, "
                        "not a factor calculated from your sport."
                    )
                    try:
                        estimated = estimate_nutrition_targets(
                            profile,
                            activity_factor
                        )
                        col1, col2 = st.columns(2)
                        col1.metric(
                            "Estimated maintenance energy",
                            f"{estimated['maintenance_calories']} kcal/day"
                        )
                        protein_low = estimated["protein_low_g"]
                        protein_high = estimated["protein_high_g"]
                        protein_display = (
                            f"{protein_low:g}–{protein_high:g} g/day"
                            if protein_low != protein_high
                            else f"{protein_low:g} g/day"
                        )
                        col2.metric(
                            "Protein reference",
                            protein_display
                        )
                        for note in estimated["notes"]:
                            st.caption(note)
                    except ValueError as error:
                        st.error(str(error))
            elif not extra_food_only:
                st.info(
                    "Enter targets you have already established. "
                    "An automatic estimate is unavailable for this profile."
                )
            calorie_default = (
                float(estimated["maintenance_calories"])
                if estimated
                else None
            )
            protein_default = (
                float(estimated["protein_low_g"])
                if estimated
                else None
            )
            st.write(
                "Confirm the targets the planner should use. "
                "You can edit the suggested values."
            )
            st.caption(
                "Automatic estimates are intended for generally healthy "
                "adults. Pregnancy, breastfeeding and conditions requiring "
                "a therapeutic diet need individually established targets."
            )
            # New estimates create a fresh form with updated defaults.
            target_form_key = (
                f"targets_{profile_key}_"
                f"{calorie_default}_{protein_default}"
            )
            with st.form(target_form_key):
                calorie_target = st.number_input(
                    "Daily calories for this plan (kcal)",
                    min_value=1.0,
                    value=calorie_default
                )
                protein_target = st.number_input(
                    "Daily protein goal for this plan (g)",
                    min_value=1.0,
                    value=protein_default
                )
                fibre_target = st.number_input(
                    "Daily fibre goal for this plan (g) — optional",
                    min_value=0.0,
                    value=None
                )
                accept_targets = st.form_submit_button(
                    "Use these targets",
                    type="primary"
                )
            if accept_targets:
                if calorie_target is None or protein_target is None:
                    st.error("Enter both calorie and protein targets.")
                elif protein_target * 4 >= calorie_target:
                    st.error(
                        "Protein alone would use all or more of the "
                        "calorie target. Review these values to leave "
                        "room for carbohydrates and fats."
                    )
                else:
                    st.session_state["nutrition_targets"] = {
                        "calories": calorie_target,
                        "protein": protein_target,
                        "fibre": fibre_target,
                        "scope": profile["budget_scope"],
                        "profile_key": profile_key
                    }
                    st.session_state.pop("meal_plan", None)
            saved_targets = st.session_state.get("nutrition_targets")
            if (
                saved_targets
                and saved_targets["profile_key"] == profile_key
            ):
                st.success(
                    f"Saved targets: "
                    f"{saved_targets['calories']:g} kcal and "
                    f"{saved_targets['protein']:g} g protein per day."
                )
                st.caption(
                    "After changing the inputs, click "
                    "'Use these targets' again to update the saved values."
                )
    if profile and profile["age"] >= 18:
        targets = st.session_state.get("nutrition_targets")
        if targets:
            st.divider()
            st.subheader("03 / Make the prices yours", anchor=False)
            st.warning(
                "This prototype catalogue uses approximate nutrition "
                "values and illustrative prices. Update prices below. "
                "Nutrition and allergen details must be checked against "
                "the actual foods you buy."
            )
            catalogue_path = Path(__file__).parent / "foods.csv"
            if not catalogue_path.exists():
                st.error(
                    "foods.csv was not found. Put it in the same "
                    "folder as app.py."
                )
            else:
                try:
                    foods = pd.read_csv(
                        catalogue_path,
                        keep_default_na=False
                    )
                    required_columns = {
                        "id", "name", "portion", "calories",
                        "protein_g", "carbs_g", "fat_g", "fibre_g",
                        "price_inr", "diet", "allergens",
                        "equipment", "max_servings"
                    }
                    missing = required_columns - set(foods.columns)
                    if missing:
                        raise ValueError(
                            "Missing CSV columns: "
                            + ", ".join(sorted(missing))
                        )
                    if foods.empty:
                        raise ValueError("The food catalogue is empty.")
                    if foods["id"].duplicated().any():
                        raise ValueError("Each food must have a unique id.")
                    numeric_columns = [
                        "calories", "protein_g", "carbs_g",
                        "fat_g", "fibre_g", "price_inr",
                        "max_servings"
                    ]
                    for column in numeric_columns:
                        foods[column] = pd.to_numeric(
                            foods[column],
                            errors="raise"
                        )
                    numbers = foods[numeric_columns]
                    if (
                        numbers.isna().any().any()
                        or numbers.isin(
                            [float("inf"), float("-inf")]
                        ).any().any()
                        or (numbers < 0).any().any()
                    ):
                        raise ValueError(
                            "Nutrition and prices must be finite, "
                            "non-negative numbers."
                        )
                    if (
                        (foods["max_servings"] <= 0).any()
                        or (
                            foods["max_servings"]
                            % 1 != 0
                        ).any()
                    ):
                        raise ValueError(
                            "max_servings must contain positive integers."
                        )
                    # Restore locally edited prices during this session.
                    saved_prices = st.session_state.get(
                        "food_prices", {}
                    )
                    foods["price_inr"] = foods.apply(
                        lambda row: saved_prices.get(
                            row["id"],
                            row["price_inr"]
                        ),
                        axis=1
                    )
                    price_table = foods[
                        ["id", "name", "portion", "price_inr"]
                    ].copy()
                    st.caption(
                        "Enter the price for the exact portion shown, "
                        "not the price of a whole package. For example, "
                        "₹100 for 500 g means ₹8 for a 40 g portion."
                    )
                    # Prices must be numeric for the number editor.
                    price_table["price_inr"] = pd.to_numeric(
                        price_table["price_inr"],
                        errors="raise"
                    ).astype(float)
                    with st.form("food_prices_form"):
                        edited_prices = st.data_editor(
                            price_table.style.set_properties(**{"font-weight": "400"}),
                            hide_index=True,
                            disabled=["id", "name", "portion"],
                            column_config={
                                "id": None,
                                "name": "Food",
                                "portion": "One portion",
                                "price_inr": st.column_config.NumberColumn(
                                    "Price per portion (₹) — editable",
                                    min_value=0.0,
                                    step=0.5,
                                    format="₹%.2f",
                                    required=True,
                                    disabled=False
                                )
                            },
                            key="food_price_editor_v2"
                        )
                        save_prices = st.form_submit_button("Save these prices")
                    if save_prices:
                        prices = pd.to_numeric(
                            edited_prices["price_inr"],
                            errors="coerce"
                        )
                        invalid = (
                            prices.isna().any()
                            or prices.isin(
                                [float("inf"), float("-inf")]
                            ).any()
                            or (prices < 0).any()
                        )
                        if invalid:
                            st.error(
                                "Enter a valid non-negative price "
                                "for every food."
                            )
                        else:
                            price_map = dict(zip(
                                edited_prices["id"],
                                prices
                            ))
                            st.session_state["food_prices"] = price_map
                            foods["price_inr"] = foods["id"].map(
                                price_map
                            )
                            st.session_state["food_catalogue"] = (
                                foods.to_dict("records")
                            )
                            st.session_state.pop("meal_plan", None)
                            st.success(
                                "Prices saved for this session."
                            )
                except (ValueError, pd.errors.ParserError) as error:
                    st.session_state.pop("food_catalogue", None)
                    st.session_state.pop("meal_plan", None)
                    st.error(f"Check foods.csv: {error}")
    profile = st.session_state.get("personal_profile")
    targets = st.session_state.get("nutrition_targets")
    catalogue = st.session_state.get("food_catalogue")
    if profile and profile["age"] >= 18 and targets and catalogue:
        st.divider()
        st.subheader("04 / Your daily food plan", anchor=False)
        current_profile_key = hashlib.sha256(
            repr(profile).encode()
        ).hexdigest()[:12]
        if targets.get("profile_key") != current_profile_key:
            st.info("Confirm nutrition targets for your current profile.")
        else:
            try:
                available, excluded = filter_foods(profile, catalogue)
                st.write(f"**Eligible foods:** {len(available)}")
                if excluded:
                    with st.expander("See excluded foods and reasons"):
                        st.dataframe(
                            pd.DataFrame(excluded).style.set_properties(**{"font-weight": "400"}),
                            hide_index=True
                        )
                if st.button(
                    "Generate my food plan",
                    type="primary",
                    key="generate_food_plan",
                    disabled=not available
                ):
                    st.session_state.pop("meal_plan", None)
                    with st.spinner("Finding food portions within your budget…"):
                        st.session_state["meal_plan"] = generate_plan(
                            available,
                            targets,
                            profile["monthly_budget"] / 30
                        )
                plan = st.session_state.get("meal_plan")
                if plan:
                    st.write(f"**Plan coverage:** {targets['scope']}")
                    try:
                        from meal_plan_pdf import build_meal_plan_pdf
                        pdf_bytes = build_meal_plan_pdf(plan, targets, profile)
                    except ImportError:
                        st.info("Install reportlab to enable the PDF download: python -m pip install reportlab")
                    else:
                        st.download_button("Download meal plan · PDF ↓", data=pdf_bytes,
                                           file_name="PocketPlate-meal-plan.pdf", mime="application/pdf",
                                           key="download_meal_plan")
                    st.dataframe(
                        pd.DataFrame(plan["items"]).style.set_properties(**{"font-weight": "400"}),
                        hide_index=True
                    )
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Daily cost", f"₹{plan['cost']:.2f}")
                    col2.metric("7-day cost", f"₹{plan['cost'] * 7:.2f}")
                    col3.metric("30-day cost", f"₹{plan['cost'] * 30:.2f}")
                    comparisons = [
                        ("Calories (kcal)", "calories", targets["calories"]),
                        ("Protein (g)", "protein_g", targets["protein"])
                    ]
                    if targets.get("fibre") is not None:
                        comparisons.append(
                            ("Fibre (g)", "fibre_g", targets["fibre"])
                        )
                    rows = []
                    for label, key, target in comparisons:
                        actual = plan["totals"][key]
                        rows.append({
                            "Nutrient": label,
                            "Target": round(target, 1),
                            "Planned": round(actual, 1),
                            "Shortfall": round(max(target - actual, 0), 1),
                            "Above target": round(max(actual - target, 0), 1)
                        })
                    st.subheader("Your nutrition, at a glance", anchor=False)
                    nutrient_cards(plan, targets)
                    st.dataframe(pd.DataFrame(rows).style.set_properties(**{"font-weight": "400"}), hide_index=True)
                    st.caption(
                        f"Carbohydrates: {plan['totals']['carbs_g']:.1f} g · "
                        f"Fat: {plan['totals']['fat_g']:.1f} g · "
                        f"Fibre: {plan['totals']['fibre_g']:.1f} g"
                    )
                    if any(row["Shortfall"] > 0 for row in rows):
                        st.warning(
                            "This combination falls short of one or more "
                            "targets. Review the table before using it."
                        )
                    if not plan["optimal"]:
                        st.info(
                            "The solver reached its time limit. This is a "
                            "validated candidate, but may not be the best one."
                        )
                    with st.expander("Shopping list for 7 identical days"):
                        shopping = pd.DataFrame(plan["items"])[
                            ["Food", "One portion", "Portions/day"]
                        ].copy()
                        shopping["Portions for 7 days"] = (
                            shopping.pop("Portions/day") * 7
                        )
                        st.dataframe(shopping.style.set_properties(**{"font-weight": "400"}), hide_index=True)
                    st.caption(
                        "Prototype food quantities, not a nutritionally complete "
                        "menu. Catalogue values are approximate. Costs exclude "
                        "unlisted ingredients and assume proportional portion "
                        "prices; buying whole packages may cost more upfront."
                    )
            except ValueError as error:
                st.session_state.pop("meal_plan", None)
                st.error(str(error))
    with steps_slot.container():
        planner_steps()
