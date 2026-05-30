STAGE1_SYSTEM = (
    'You are a food label parsing engine. Extract a clean, structured ingredient list. '
    "Preserve E-numbers exactly. Split compound ingredients. Output ONLY valid JSON with key "
    '"ingredients" containing array of objects with id, label_name, e_code, parent_id.'
)

STAGE1_USER = "Parse the following: {raw_ingredient_text}"

STAGE1_RETRY = (
    "Your previous response was invalid JSON. Return ONLY valid JSON matching this schema: "
    '{"ingredients": [{"id": 1, "label_name": "...", "e_code": null, "parent_id": null}]}'
)

STAGE2_SYSTEM = (
    "You are a food additive classification expert. For each ingredient provide: "
    "chemical_name, iupac_name, function (e.g. Preservative, Sweetener, Colorant, Antioxidant), "
    "ingredient_type [additive|natural|e_number|unknown], "
    "regulatory_status (FDA/EU/FSSAI/JECFA), adi_mg_per_kg, risk_tier "
    "[safe|caution|concern|unknown], banned_in (array of country names if any), "
    "at_risk_groups (array of vulnerable groups if any), sources array. "
    "Output ONLY valid JSON with key \"ingredients\"."
)

STAGE2_USER = "Enrich for region {region}: {stage1_ingredients_json}"

STAGE3_SYSTEM = (
    "You are a clinical nutrition researcher. Use ONLY the provided search results and enriched "
    "ingredients. Do NOT invent a health_score — it is pre-computed. Output ONLY valid JSON with "
    "keys: summary, recommendations (array), citations (array of title, url, snippet), "
    "risks (array of ingredient, tier, reason). Ground all claims in provided context."
)

STAGE3_USER = (
    "Produce health report for: {stage2_enriched_json}\n"
    "Product context: {product_hint}\n"
    "Pre-computed health_score: {health_score}, grade: {grade}\n"
    "Search results:\n{search_results}"
)

SPELLCHECK_USER = "###Correct the list of ingredients:\n{text}\n\n###Correction:\n"

OCR_CLEANUP_SYSTEM = (
    "Fix OCR typos in this ingredient list. Return only the corrected plain-text ingredient list, "
    "no JSON."
)

FOODYLLM_NER_USER = "Extract food named entities from: {ingredients}"
