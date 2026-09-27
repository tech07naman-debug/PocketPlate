# 🥗 PocketPlate

**Eat smarter. Spend better.**

[Open PocketPlate](https://pocketplate.streamlit.app/) · [View source code](https://github.com/tech07naman-debug/PocketPlate)

PocketPlate is a Streamlit app that helps you understand packaged-food labels and create a daily food plan around your nutrition targets, dietary preferences, available cooking equipment, and budget.

It combines a Gemini-powered food-label scanner with a budget-constrained meal planner, editable food prices, and downloadable PDF plans.

## Features

### Food label scanner

- Upload up to **3 JPG or PNG photos**, with a **10 MB combined limit**.
- Read nutrition information and ingredients from photos of the same product.
- Extract energy, protein, carbohydrates, fat, fibre, sugars, and sodium when visible.
- View nutrition information for your selected portion.
- Keep missing or unclear nutrition values distinct from zero.
- Preview uploaded photos in individual bordered cards, with two photos side by side on desktop.

Photos are sent to Google's Gemini API when you select **Analyze your food**.

### Budget meal planner

- Save a profile with your routine, food budget, diet, allergies, dislikes, and cooking access.
- Start with estimated nutrition targets or enter your own.
- Edit prices per portion to reflect your local shops.
- Filter the catalogue against your saved preferences and supported restrictions.
- Generate whole-number daily portions within your daily budget.
- Compare planned calories, protein, and optional fibre against your targets.
- Review daily, seven-day, and 30-day food costs.
- Download a PDF with daily portions, nutrition totals, costs, and a shopping list.

The seven-day shopping list repeats the same daily portions seven times; it is not a varied weekly menu.

### Interface

- Sidebar navigation between the scanner and planner.
- Blue and yellow scanner theme.
- Cream, forest green, and peach planner theme.
- Clear captions, bold table headings, and nutrition progress cards.

## Tech stack

| Component | Technology |
| --- | --- |
| Interface | Streamlit |
| Label extraction | Google Gemini API through `google-genai` |
| Response validation | Pydantic |
| Data processing | pandas and NumPy |
| Meal optimization | SciPy mixed-integer linear programming (`milp`) |
| PDF export | ReportLab |
| Local environment variables | python-dotenv |

## Project files

| Path | Purpose |
| --- | --- |
| `app.py` | App entry point, controls, and page flow |
| `food_analyzer.py` | Gemini request and food-label response validation |
| `nutrition_calculator.py` | Nutrition target estimates |
| `meal_planner.py` | Catalogue filtering and portion optimization |
| `pocketplate_ui.py` | Page themes and presentation helpers |
| `meal_plan_pdf.py` | Meal-plan PDF generation |
| `foods.csv` | Food catalogue, portion sizes, nutrition, and prices |
| `requirements.txt` | Python dependencies |
| `.streamlit/config.toml` | Streamlit theme and upload configuration |
| `assests/fonts/` | Embedded PDF fonts and their license |

## Run locally

Use **Python 3.12** to match the project's deployment setup.

### 1. Clone the repository

```bash
git clone https://github.com/tech07naman-debug/PocketPlate.git
cd PocketPlate
```

### 2. Create and activate a virtual environment

**Windows — Command Prompt:**

```bat
py -3.12 -m venv .venv
.venv\Scripts\activate.bat
```

**macOS / Linux:**

```bash
python3.12 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
python -m pip install -r requirements.txt
```

The requirements must include `scipy` for meal optimization and `reportlab` for PDF export, in addition to the app's other dependencies.

### 4. Configure Gemini

Create a `.env` file beside `app.py`:

```dotenv
GEMINI_API_KEY=your_gemini_api_key_here
```

Use a key with access to the model configured in `food_analyzer.py`. Model availability, API quotas, and billing depend on your Google project.

Never commit the real key, `.env`, or `.streamlit/secrets.toml` to GitHub. Ensure your `.gitignore` includes:

```gitignore
.env
.env.*
.venv/
__pycache__/
*.py[cod]
.streamlit/secrets.toml
```

Keep `.streamlit/config.toml` and `assests/fonts/` in the repository.

### 5. Start the app

```bash
python -m streamlit run app.py
```

Open the local URL printed in the terminal.

## How to use

**Scan a food label**

1. Open **Food Scanner**.
2. Upload clear photos of the nutrition panel and ingredients list from one product.
3. Select **Analyze your food**.
4. Review the extracted information against the original label and adjust your portion where supported.

**Create a food plan**

1. Open **Meal Planner** and save your profile.
2. Confirm your daily nutrition targets.
3. Edit and save prices for the exact portions shown.
4. Select **Generate my food plan**.
5. Review costs and any nutrient shortfalls, then download the PDF.

## Deploy on Streamlit Community Cloud

1. Push the project files to GitHub, excluding credentials and your virtual environment.
2. Sign in at [Streamlit Community Cloud](https://share.streamlit.io/).
3. Create an app using this repository, your branch, and `app.py` as the entry point.
4. In **Advanced settings**, select Python 3.12 and add this root-level secret:

```toml
GEMINI_API_KEY = "your_gemini_api_key_here"
```

5. Save the settings and deploy.

Streamlit exposes root-level secrets as environment variables, so the scanner can read the key using its existing `os.getenv("GEMINI_API_KEY")` call.

See the official [deployment guide](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy) and [secrets documentation](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management).

## How the planner works

The planner first filters the food catalogue using your saved preferences. It then uses mixed-integer optimization to choose whole-number portions, respecting the daily budget and each food's serving limit.

Its objective minimizes proportional differences from calorie, protein, and optional fibre targets, with a small cost preference. It can return a plan with shortfalls or excesses; meeting every target is not guaranteed. A validated candidate may be returned when the solver reaches its time limit.

## Limitations and privacy

- The public scanner uses a shared Gemini API quota. It may be temporarily unavailable when request or daily limits are reached; the meal planner does not need Gemini.

- Label extraction can make mistakes. Check results against the original packaging.
- Missing allergy statements do not establish that a product is allergen-free.
- The demo catalogue uses approximate nutrition values and illustrative prices. Verify them against the foods you buy.
- The catalogue cannot verify additional free-text allergies or gluten/cross-contact requirements. Those restrictions can prevent plan generation.
- A generated food combination is not a nutritionally complete menu or personalized medical advice.
- Prices assume proportional portions; buying whole packages may cost more upfront. Unlisted ingredients are not included.
- Monthly budget calculations assume 30 days.
- Saved profiles, prices, and plans are session-based, not a permanent account or database.
- Scanner photos are processed by Google's Gemini API. Avoid including unrelated personal information in uploads.

## Troubleshooting

**`No module named 'google.genai'`**

Install `google-genai` in the same environment used to start Streamlit:

```bash
python -m pip install google-genai
python -m streamlit run app.py
```

**PDF font file cannot be opened**

Ensure both files exist relative to the app folder. The current repository folder is spelled `assests`; the `font_dir` path in `meal_plan_pdf.py` must use the same spelling. If you rename it to `assets`, update the code as well:

```text
assests/fonts/DejaVuSans.ttf
assests/fonts/DejaVuSans-Bold.ttf
```

**Gemini key is missing**

Set `GEMINI_API_KEY` in your local `.env` or in Streamlit Community Cloud's Secrets settings. Do not upload `.env` to solve a cloud configuration issue.

**Scanner request fails or takes too long**

Check the terminal or deployment logs for the actual error. Verify the configured model, API-key access, and quota. Upload clear label photos; changing the key alone does not resolve every API error.

## Author

Built by [Naman Mangla](https://github.com/tech07naman-debug).
