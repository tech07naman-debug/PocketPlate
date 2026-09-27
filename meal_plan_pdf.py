"""Generate a portable two-section meal-plan report from the saved plan."""
from io import BytesIO
from pathlib import Path
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from html import escape
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak


def build_meal_plan_pdf(plan, targets, profile):
    font_dir = Path(__file__).parent / "assets" / "fonts"
    if "PPRegular" not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont("PPRegular", str(font_dir / "DejaVuSans.ttf")))
        pdfmetrics.registerFont(TTFont("PPBold", str(font_dir / "DejaVuSans-Bold.ttf")))
    stream = BytesIO()
    ink = colors.HexColor('#173E31')
    mint = colors.HexColor('#E8EEDC')
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='PPTitle', fontName='PPBold', fontSize=28, leading=32, textColor=ink, spaceAfter=12))
    styles.add(ParagraphStyle(name='PPSection', fontName='PPBold', fontSize=14, leading=19, textColor=ink, spaceBefore=15, spaceAfter=9))
    styles.add(ParagraphStyle(name='PPBody', fontName='PPRegular', fontSize=9, leading=13, spaceAfter=7, textColor=ink))
    styles.add(ParagraphStyle(name='PPCell', fontName='PPRegular', fontSize=8, leading=11, textColor=ink))

    def clean(value):
        return str(value).replace('₹','INR ').replace('—','-').replace('–','-').replace('…','...')

    def p(value, style='PPBody'):
        return Paragraph(escape(clean(value)),styles[style])

    def table(rows, widths):
        obj = Table([[p(cell,'PPCell') for cell in row] for row in rows],colWidths=widths,repeatRows=1,hAlign='LEFT')
        obj.setStyle(TableStyle([
            ('BACKGROUND',(0,0),(-1,0),mint),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#F7F8F3')]),
            ('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),9),('RIGHTPADDING',(0,0),(-1,-1),9),
            ('TOPPADDING',(0,0),(-1,-1),9),('BOTTOMPADDING',(0,0),(-1,-1),9),
            ('LINEBELOW',(0,0),(-1,0),1,ink),('LINEBELOW',(0,1),(-1,-1),.3,colors.HexColor('#D5DDCB'))
        ]))
        return obj

    doc = SimpleDocTemplate(stream,pagesize=A4,rightMargin=40,leftMargin=40,topMargin=46,bottomMargin=48,title='PocketPlate - Your meal plan',author='PocketPlate')
    width = A4[0]-80
    story = [p('POCKETPLATE / YOUR DAILY PLAN'),p('Good food. Better budget.','PPTitle'),p('Created '+datetime.now().strftime('%d %b %Y')),
             p('Coverage: '+targets['scope']),p('Goal: '+profile['goal']),p('Diet: '+profile['diet'])]
    cost = float(plan['cost'])
    story.append(table([['Daily cost','7 identical days','30 identical days','Daily budget'],[f'INR {cost:.2f}',f'INR {cost*7:.2f}',f'INR {cost*30:.2f}',f"INR {profile['monthly_budget']/30:.2f}"]],[width/4]*4))
    story.append(p('01 / Daily food portions','PPSection'))
    rows = [['Food','One portion','Portions / day','Cost / day']]
    for item in plan['items']:
        rows.append([item['Food'],item['One portion'],item['Portions/day'],f"INR {item['Cost/day (₹)']:.2f}"])
    story.append(table(rows,[width*.23,width*.43,width*.15,width*.19]))
    story.append(p('02 / Nutrition compared with your targets','PPSection'))
    entries = [('Calories (kcal)','calories',targets['calories']),('Protein (g)','protein_g',targets['protein'])]
    if targets.get('fibre') is not None:
        entries.append(('Fibre (g)','fibre_g',targets['fibre']))
    rows = [['Nutrient','Target','Planned','Shortfall','Above target']]
    has_shortfall=False
    for label,key,goal in entries:
        actual=plan['totals'][key]
        has_shortfall |= actual < goal-.05
        rows.append([label,f'{goal:.1f}',f'{actual:.1f}',f'{max(goal-actual,0):.1f}',f'{max(actual-goal,0):.1f}'])
    story.append(table(rows,[width*.28]+[width*.18]*4))
    story.append(Spacer(1,9))
    story.append(p('One or more targets are not met. Review the shortfalls above.' if has_shortfall else 'Review planned values and any amounts above target.'))
    story.append(p(f"Carbohydrates: {plan['totals']['carbs_g']:.1f} g | Fat: {plan['totals']['fat_g']:.1f} g | Fibre: {plan['totals']['fibre_g']:.1f} g"))
    if not plan.get('optimal',False):
        story.append(p('Solver time limit reached. This validated candidate may not be the best available combination.'))
    story += [PageBreak(),p('POCKETPLATE / SHOPPING LIST'),p('A week, made simpler.','PPTitle'),p('Quantities for repeating this daily plan for seven identical days. This is not a varied weekly menu.')]
    rows=[['Food','One portion','Portions for 7 days']]
    for item in plan['items']:
        rows.append([item['Food'],item['One portion'],item['Portions/day']*7])
    story.append(table(rows,[width*.28,width*.47,width*.25]))
    story.append(p('Before you shop','PPSection'))
    for note in [
        'Multiply each one-portion quantity by its number of portions. Dry weights refer to food before cooking.',
        'Prices and nutrition come from the saved prototype catalogue. Check them against the actual products you buy.',
        'Costs exclude unlisted ingredients, cooking oil and extras. Whole packages may cost more upfront. Monthly estimates assume 30 identical days.',
        'This is a portion-based prototype, not a nutritionally complete menu. Micronutrient adequacy and meal variety are not assessed.',
        'Check actual ingredients, allergens, cross-contact warnings and storage requirements.',
        'For an extra-food plan, all quantities and nutrition totals shown cover only the additions, not your existing meals.'
    ]:
        story.append(p(note))

    def footer(canvas, document):
        canvas.setStrokeColor(colors.HexColor('#D5DDCB'))
        canvas.line(40,36,A4[0]-40,36)
        canvas.setFont('PPRegular',8)
        canvas.setFillColor(ink)
        canvas.drawString(40,23,'PocketPlate | Eat smarter. Spend better.')
        canvas.drawRightString(A4[0]-40,23,f'{document.page}')

    doc.build(story,onFirstPage=footer,onLaterPages=footer)
    return stream.getvalue()
