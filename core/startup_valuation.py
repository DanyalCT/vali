import openai
import os
import json
import math
from db.mongodb import db
from bson import ObjectId

def get_pdf_text(pdfid: str) -> str:
    """
    Extract PDF text from MongoDB using pdfid.
    
    Args:
        pdfid (str): The ID of the PDF document
        
    Returns:
        str: The extracted text from the PDF
    """
    try:
        pdf_doc = db.pdf_texts.find_one({"_id": ObjectId(pdfid)})
        pdf_question= db.user_qas.find_one({"pdf_id": pdfid})
        if not pdf_doc:
            raise ValueError(f"No PDF found with ID: {pdfid}")
        return pdf_doc,pdf_question
    except Exception as e:
        raise Exception(f"Error extracting PDF text: {str(e)}")

def perform_startup_valuation(pdfid: str, api_key: str = "AIzaSyC5QqQ15b3DkgLHefpJufzs1dEHrf74HJ4", model_name: str = "gemini-2.0-flash"):
    """
    Perform startup valuation based on PDF text extracted from MongoDB.
    
    Args:
        pdfid (str): The ID of the PDF document containing startup information
        api_key (str, optional): The Groq API key. If not provided, will use environment variable
        model_name (str, optional): The model name to use. Defaults to "llama3-8b-8192"
    
    Returns:
        dict: The valuation results and conversation history
    """
    # Extract PDF text from MongoDB
    try:
        print("pdfID",pdfid)
        pdfText,user_Question = get_pdf_text(pdfid)
        print("user_Question",user_Question)
        if not pdfText or not user_Question:
            return {"error": "No text content found in the PDF"}
    except Exception as e:
        return {"error": f"Failed to extract PDF text: {str(e)}"}

    # Set up API client
    if api_key:
        os.environ["GROQ_API_KEY"] = api_key
    
    client = openai.OpenAI(
        api_key="AIzaSyC5QqQ15b3DkgLHefpJufzs1dEHrf74HJ4",
        base_url="https://generativelanguage.googleapis.com/v1beta/openai"
    )

    # --- Basic Helper Python Functions ---
    def get_valuation_weights(business_stage: str) -> dict:
        """
        Returns a dictionary of valuation method weights based on the business stage.
        Args:
            business_stage (str): The stage of the business (e.g., "Idea", "Startup", "Expansion", "Development", "Growth", "Maturity").
        """
        print(f"Python function 'get_valuation_weights' called with stage: {business_stage}")
        weights_table = {
            "Idea": {"Scorecard": 0.38, "Checklist": 0.38, "VC Method": 0.16, "DCF w/ LTG": 0.04, "DCF w/ Multiple": 0.04},
            "Startup": {"Scorecard": 0.30, "Checklist": 0.30, "VC Method": 0.16, "DCF w/ LTG": 0.12, "DCF w/ Multiple": 0.12},
            "Development": {"Scorecard": 0.15, "Checklist": 0.15, "VC Method": 0.16, "DCF w/ LTG": 0.27, "DCF w/ Multiple": 0.27},
            "Expansion": {"Scorecard": 0.06, "Checklist": 0.06, "VC Method": 0.16, "DCF w/ LTG": 0.36, "DCF w/ Multiple": 0.36},
            "Growth": {"Scorecard": 0.0, "Checklist": 0.0, "VC Method": 0.16, "DCF w/ LTG": 0.40, "DCF w/ Multiple": 0.40},
            "Maturity": {"Scorecard": 0.0, "Checklist": 0.0, "VC Method": 0.16, "DCF w/ LTG": 0.50, "DCF w/ Multiple": 0.50}
        }
        
        for stage_key in weights_table:
            if "DCF w/ Multiples" in weights_table[stage_key]:
                weights_table[stage_key]["DCF w/ Multiple"] = weights_table[stage_key].pop("DCF w/ Multiples")

        normalized_stage = business_stage.capitalize()
        if normalized_stage not in weights_table:
            return {"error": f"Unknown business stage: {business_stage}. Valid stages are {list(weights_table.keys())}"}
        return weights_table[normalized_stage]

    def calculate_final_weighted_valuation(individual_method_results: dict, weights: dict) -> dict:
        """
        Calculates the final weighted average valuation.
        """
        print(f"Python function 'calculate_final_weighted_valuation' called with results: {individual_method_results}, weights: {weights}")
        final_valuation = 0
        calculation_details = []
        standardized_results = {k.replace('(','').replace(')',''): v for k,v in individual_method_results.items()}
        standardized_weights = {k.replace('(','').replace(')',''): v for k,v in weights.items()}

        for method_key_std, value in standardized_results.items():
            original_method_name = method_key_std
            for w_key_orig in weights.keys():
                if w_key_orig.replace('(','').replace(')','') == method_key_std:
                    original_method_name = w_key_orig
                    break

            weight = standardized_weights.get(method_key_std, 0)
            if weight > 0:
                weighted_value = value * weight
                final_valuation += weighted_value
                calculation_details.append(f"{original_method_name}: EUR {value:,.0f} * {weight*100:.0f}% = EUR {weighted_value:,.0f}")
            else:
                calculation_details.append(f"{original_method_name}: EUR {value:,.0f} (Weight is {weight*100:.0f}%, not included in total or N/A)")

        return {
            "final_weighted_valuation": round(final_valuation, 2),
            "calculation_breakdown": calculation_details
        }

    def calculate_scorecard_valuation(
        average_pre_money_valuation: float,
        strength_of_team_score: float,
        size_of_opportunity_score: float,
        product_service_ip_score: float,
        competitive_environment_score: float,
        strategic_relationships_score: float,
        funding_requirement_score: float
        ) -> dict:
        """
        Calculates valuation using the Scorecard method.
        """
        print(f"Python function 'calculate_scorecard_valuation' called.")

        weights = {
            "team": 0.30, "opportunity": 0.25, "product_ip": 0.15,
            "competition": 0.10, "strategic_rel": 0.10, "funding_req": 0.10
        }

        score_multiplier = (
            strength_of_team_score * weights["team"] +
            size_of_opportunity_score * weights["opportunity"] +
            product_service_ip_score * weights["product_ip"] +
            competitive_environment_score * weights["competition"] +
            strategic_relationships_score * weights["strategic_rel"] +
            funding_requirement_score * weights["funding_req"]
        )

        valuation = average_pre_money_valuation * score_multiplier
        return {
            "method_name": "Scorecard",
            "valuation": round(valuation, 2),
            "details": {
                "average_pre_money_valuation": average_pre_money_valuation,
                "composite_score_multiplier": round(score_multiplier, 3),
                "inputs_scores": {
                    "strength_of_team_score": strength_of_team_score,
                    "size_of_opportunity_score": size_of_opportunity_score,
                    "product_service_ip_score": product_service_ip_score,
                    "competitive_environment_score": competitive_environment_score,
                    "strategic_relationships_score": strategic_relationships_score,
                    "funding_requirement_score": funding_requirement_score
                }
            }
        }

    def calculate_checklist_valuation(
        max_valuation_assumption: float,
        idea_quality_score: float,
        product_ip_score: float,
        core_team_score: float,
        operating_stage_score: float,
        strategic_relations_score: float
        ) -> dict:
        """
        Calculates valuation using the Checklist method.
        """
        print(f"Python function 'calculate_checklist_valuation' called.")
        weights = {
            "idea_quality": 0.20, "product_ip": 0.15, "core_team": 0.30,
            "operating_stage": 0.20, "strategic_relations": 0.15
        }
        scores = {
            "idea_quality": idea_quality_score / 100.0,
            "product_ip": product_ip_score / 100.0,
            "core_team": core_team_score / 100.0,
            "operating_stage": operating_stage_score / 100.0,
            "strategic_relations": strategic_relations_score / 100.0
        }

        valuation = 0
        valuation_breakdown = {}

        val_idea = max_valuation_assumption * weights["idea_quality"] * scores["idea_quality"]
        valuation += val_idea
        valuation_breakdown["Idea Quality Contribution"] = round(val_idea,2)

        val_prod_ip = max_valuation_assumption * weights["product_ip"] * scores["product_ip"]
        valuation += val_prod_ip
        valuation_breakdown["Product/IP Contribution"] = round(val_prod_ip,2)

        val_team = max_valuation_assumption * weights["core_team"] * scores["core_team"]
        valuation += val_team
        valuation_breakdown["Core Team Contribution"] = round(val_team,2)

        val_op_stage = max_valuation_assumption * weights["operating_stage"] * scores["operating_stage"]
        valuation += val_op_stage
        valuation_breakdown["Operating Stage Contribution"] = round(val_op_stage,2)

        val_strat_rel = max_valuation_assumption * weights["strategic_relations"] * scores["strategic_relations"]
        valuation += val_strat_rel
        valuation_breakdown["Strategic Relations Contribution"] = round(val_strat_rel,2)

        return {
            "method_name": "Checklist",
            "valuation": round(valuation, 2),
            "details": {
                "max_valuation_assumption": max_valuation_assumption,
                "inputs_scores_percent": {
                    "idea_quality_score": idea_quality_score,
                    "product_ip_score": product_ip_score,
                    "core_team_score": core_team_score,
                    "operating_stage_score": operating_stage_score,
                    "strategic_relations_score": strategic_relations_score
                },
                "valuation_breakdown": valuation_breakdown
            }
        }

    def calculate_dcf_valuation(
        free_cash_flows: list[float],
        survival_rates: list[float],
        discount_rate: float,
        terminal_value: float
        ) -> float:
        """Helper function for core DCF calculation."""
        if len(free_cash_flows) != len(survival_rates):
            raise ValueError("Length of free_cash_flows and survival_rates must be the same.")
        n = len(free_cash_flows)
        dcf_value = 0
        for t_idx in range(n):
            t = t_idx + 1
            dcf_value += (free_cash_flows[t_idx] * survival_rates[t_idx]) / ((1 + discount_rate)**t)
        dcf_value += (terminal_value * survival_rates[n-1]) / ((1 + discount_rate)**n)
        return dcf_value

    def calculate_dcf_ltg_valuation(
        free_cash_flows_projection: list[float],
        survival_rates_projection: list[float],
        discount_rate: float,
        long_term_growth_rate: float
        ) -> dict:
        """Calculates valuation using DCF with Long-Term Growth method."""
        print(f"Python function 'calculate_dcf_ltg_valuation' called.")
        if not free_cash_flows_projection:
            return {"error": "Free cash flow projection cannot be empty."}
        if discount_rate <= long_term_growth_rate:
            return {"error": "Discount rate must be greater than long-term growth rate for TV calculation."}

        n = len(free_cash_flows_projection)
        fcf_n = free_cash_flows_projection[-1]

        terminal_value_ltg = (fcf_n * (1 + long_term_growth_rate)) / (discount_rate - long_term_growth_rate)

        dcf_valuation_result = calculate_dcf_valuation(
            free_cash_flows_projection, survival_rates_projection, discount_rate, terminal_value_ltg
        )
        return {
            "method_name": "DCF w/ LTG",
            "valuation": round(dcf_valuation_result, 2),
            "details": {
                "terminal_value_ltg": round(terminal_value_ltg, 2),
                "inputs": {
                    "free_cash_flows_projection": free_cash_flows_projection,
                    "survival_rates_projection": survival_rates_projection,
                    "discount_rate": discount_rate,
                    "long_term_growth_rate": long_term_growth_rate
                }
            }
        }

    def calculate_dcf_multiple_valuation(
        free_cash_flows_projection: list[float],
        survival_rates_projection: list[float],
        discount_rate: float,
        final_year_ebitda: float,
        industry_multiple: float
        ) -> dict:
        """Calculates valuation using DCF with Exit Multiple method."""
        print(f"Python function 'calculate_dcf_multiple_valuation' called.")
        if not free_cash_flows_projection:
            return {"error": "Free cash flow projection cannot be empty."}

        terminal_value_multiple = final_year_ebitda * industry_multiple
        dcf_valuation_result = calculate_dcf_valuation(
            free_cash_flows_projection, survival_rates_projection, discount_rate, terminal_value_multiple
        )
        return {
            "method_name": "DCF w/ Multiple",
            "valuation": round(dcf_valuation_result, 2),
            "details": {
                "terminal_value_multiple": round(terminal_value_multiple, 2),
                "inputs": {
                    "free_cash_flows_projection": free_cash_flows_projection,
                    "survival_rates_projection": survival_rates_projection,
                    "discount_rate": discount_rate,
                    "final_year_ebitda": final_year_ebitda,
                    "industry_multiple": industry_multiple
                }
            }
        }

    def get_typical_roi_for_stage(business_stage: str) -> dict:
        """Returns typical ROI (discount rate) for VC method based on business stage."""
        print(f"Python function 'get_typical_roi_for_stage' called for stage: {business_stage}")
        roi_table = {
            "Idea": 1.3593,
            "Startup": 1.1474,
            "Development": 0.8912,
            "Expansion": 0.4860,
            "Growth": 0.3620
        }
        normalized_stage = business_stage.capitalize()
        roi = roi_table.get(normalized_stage)
        if roi is not None:
            return {"business_stage": business_stage, "typical_roi": roi}
        else:
            return {"error": f"No typical ROI defined for stage '{business_stage}' in VC ROI table, or VC method not applicable."}

    def calculate_vc_method_valuation(
        final_year_ebitda: float,
        exit_multiple: float,
        expected_roi: float,
        years_to_exit: int,
        capital_raised: float = 0
        ) -> dict:
        """Calculates pre-money valuation using the Venture Capital method."""
        print(f"Python function 'calculate_vc_method_valuation' called.")
        if (1 + expected_roi)**years_to_exit == 0:
            return {"error": "Division by zero in VC method due to ROI and years to exit."}

        terminal_value_at_exit = final_year_ebitda * exit_multiple
        post_money_valuation_today = terminal_value_at_exit / ((1 + expected_roi)**years_to_exit)
        pre_money_valuation = post_money_valuation_today - capital_raised

        return {
            "method_name": "VC Method",
            "valuation": round(pre_money_valuation, 2),
            "details": {
                "terminal_value_at_exit": round(terminal_value_at_exit, 2),
                "post_money_valuation_today": round(post_money_valuation_today, 2),
                "inputs": {
                    "final_year_ebitda": final_year_ebitda,
                    "exit_multiple": exit_multiple,
                    "expected_roi": expected_roi,
                    "years_to_exit": years_to_exit,
                    "capital_raised": capital_raised
                }
            }
        }

    # Define tools schema
    tools_schema = [
        {
            "type": "function",
            "function": {
                "name": "get_valuation_weights",
                "description": "Gets the predefined valuation method weights based on the business stage. Call this first to understand method importance.",
                "parameters": {
                    "type": "object",
                    "properties": {"business_stage": {"type": "string", "description": "The current stage of the business (e.g., Idea, Startup, Development, Expansion, Growth, Maturity)."}},
                    "required": ["business_stage"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "calculate_scorecard_valuation",
                "description": "Calculates valuation using the Scorecard method. Requires an average pre-money valuation for the stage and scores for criteria (0.5-1.5 range, 1.0 is average).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "average_pre_money_valuation": {"type": "number", "description": "Typical pre-money valuation for companies at this stage."},
                        "strength_of_team_score": {"type": "number", "description": "Score multiplier for team strength (e.g., 0.7 for weak, 1.0 for average, 1.3 for strong)."},
                        "size_of_opportunity_score": {"type": "number", "description": "Score multiplier for market opportunity size."},
                        "product_service_ip_score": {"type": "number", "description": "Score multiplier for product, service, and IP protection."},
                        "competitive_environment_score": {"type": "number", "description": "Score multiplier for competitive landscape."},
                        "strategic_relationships_score": {"type": "number", "description": "Score multiplier for strategic relationships."},
                        "funding_requirement_score": {"type": "number", "description": "Score multiplier related to funding needs and use of funds."}
                    },
                    "required": ["average_pre_money_valuation", "strength_of_team_score", "size_of_opportunity_score", "product_service_ip_score", "competitive_environment_score", "strategic_relationships_score", "funding_requirement_score"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "calculate_checklist_valuation",
                "description": "Calculates valuation using the Checklist method. Requires a maximum valuation assumption and scores (0-100) for criteria.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "max_valuation_assumption": {"type": "number", "description": "The maximum valuation assumed for a perfect score in all categories for this stage."},
                        "idea_quality_score": {"type": "number", "description": "Score (0-100) for idea quality."},
                        "product_ip_score": {"type": "number", "description": "Score (0-100) for product/IP strength."},
                        "core_team_score": {"type": "number", "description": "Score (0-100) for core team strength."},
                        "operating_stage_score": {"type": "number", "description": "Score (0-100) for current operating stage/traction."},
                        "strategic_relations_score": {"type": "number", "description": "Score (0-100) for strategic relationships."}
                    },
                    "required": ["max_valuation_assumption", "idea_quality_score", "product_ip_score", "core_team_score", "operating_stage_score", "strategic_relations_score"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "calculate_dcf_ltg_valuation",
                "description": "Calculates valuation using DCF with Long-Term Growth. Requires FCF and survival rate projections, WACC, and a long-term growth rate.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "free_cash_flows_projection": {"type": "array", "items": {"type": "number"}, "description": "List of projected Free Cash Flows for N years (e.g., [10000, 20000, 30000])."},
                        "survival_rates_projection": {"type": "array", "items": {"type": "number"}, "description": "List of projected survival rates (0-1) for N years, matching FCF list length (e.g., [0.9, 0.85, 0.8])."},
                        "discount_rate": {"type": "number", "description": "Weighted Average Cost of Capital (WACC) as a decimal (e.g., 0.2 for 20%)."},
                        "long_term_growth_rate": {"type": "number", "description": "Perpetual long-term growth rate for terminal value, as a decimal (e.g., 0.03 for 3%)."}
                    },
                    "required": ["free_cash_flows_projection", "survival_rates_projection", "discount_rate", "long_term_growth_rate"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "calculate_dcf_multiple_valuation",
                "description": "Calculates valuation using DCF with Exit Multiple. Requires FCF and survival rate projections, WACC, final year EBITDA, and an industry multiple.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "free_cash_flows_projection": {"type": "array", "items": {"type": "number"}, "description": "List of projected Free Cash Flows for N years."},
                        "survival_rates_projection": {"type": "array", "items": {"type": "number"}, "description": "List of projected survival rates (0-1) for N years."},
                        "discount_rate": {"type": "number", "description": "WACC as a decimal."},
                        "final_year_ebitda": {"type": "number", "description": "Projected EBITDA in the final year of detailed projection."},
                        "industry_multiple": {"type": "number", "description": "Applicable industry EBITDA multiple for terminal value."}
                    },
                    "required": ["free_cash_flows_projection", "survival_rates_projection", "discount_rate", "final_year_ebitda", "industry_multiple"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_typical_roi_for_stage",
                "description": "Retrieves the typical annual ROI (Return on Investment) or discount rate used in the VC method for a given business stage.",
                "parameters": {
                    "type": "object",
                    "properties": {"business_stage": {"type": "string", "description": "The current stage of the business (e.g., Idea, Startup)."}},
                    "required": ["business_stage"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "calculate_vc_method_valuation",
                "description": "Calculates pre-money valuation using the Venture Capital method. First call 'get_typical_roi_for_stage' if ROI is not known.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "final_year_ebitda": {"type": "number", "description": "Projected EBITDA in the target exit year."},
                        "exit_multiple": {"type": "number", "description": "Expected EBITDA multiple at exit."},
                        "expected_roi": {"type": "number", "description": "Required annual ROI for investors, as a decimal (e.g., 0.5 for 50%). Get this from 'get_typical_roi_for_stage' if unsure."},
                        "years_to_exit": {"type": "integer", "description": "Number of years until expected exit."},
                        "capital_raised": {"type": "number", "description": "Amount of capital already raised by the company (optional, default 0)."}
                    },
                    "required": ["final_year_ebitda", "exit_multiple", "expected_roi", "years_to_exit"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "calculate_final_weighted_valuation",
                "description": "Calculates the final weighted average valuation using individual method valuations and their corresponding weights. Call this after obtaining all individual valuations and weights.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "individual_method_results": {"type": "object", "description": "A dictionary where keys are method names (e.g., 'Scorecard', 'VC Method') and values are their calculated valuation amounts."},
                        "weights": {"type": "object", "description": "A dictionary where keys are method names and values are their respective weights."}
                    },
                    "required": ["individual_method_results", "weights"]
                }
            }
        }
    ]

    # System message for the LLM
    SYSTEM_MESSAGE = """You are a startup valuation assistant.
    Your goal is to perform a preliminary valuation based on user-provided information and Equidam-like methodologies.

    Valuation Process:
    1.  Determine the user's **business stage**.
    2.  Call `get_valuation_weights` to get method weights for that stage.
    3.  Call `get_typical_roi_for_stage` if the VC method will be used and its weight is > 0, to inform the `expected_roi` for the `calculate_vc_method_valuation` call.
    4.  For each of the 5 valuation methods (Scorecard, Checklist, DCF w/ LTG, DCF w/ Multiple, VC Method), if its weight for the stage is greater than 0, attempt to calculate its value:
        a.  **Gather Inputs:** You will need specific inputs for each method. If the user has provided relevant data (like FCF projections, EBITDA, scores), use it. If crucial data for a method is missing, you can state that the method cannot be fully calculated with current info, or you can proceed by calling the respective calculation function with placeholder/assumed values if the function supports it.
        b.  **Call Functions:** Use the appropriate calculation function for each method.
    5.  Collect all calculated individual valuations.
    6.  Call `calculate_final_weighted_valuation` with the collected individual valuations and weights.
    7.  Present a summary report: business stage, weights, each method's valuation (or why it couldn't be calculated), the final weighted valuation, and a brief explanation.

    Be methodical. If a function returns an error, acknowledge it and try to explain why it might have occurred in your final report.
    """

    # Available functions mapping
    available_functions = {
        "get_valuation_weights": get_valuation_weights,
        "calculate_scorecard_valuation": calculate_scorecard_valuation,
        "calculate_checklist_valuation": calculate_checklist_valuation,
        "calculate_dcf_ltg_valuation": calculate_dcf_ltg_valuation,
        "calculate_dcf_multiple_valuation": calculate_dcf_multiple_valuation,
        "get_typical_roi_for_stage": get_typical_roi_for_stage,
        "calculate_vc_method_valuation": calculate_vc_method_valuation,
        "calculate_final_weighted_valuation": calculate_final_weighted_valuation,
    }

    # Initialize conversation history
    conversation_history = [{"role": "system", "content": SYSTEM_MESSAGE}]
    conversation_history.append({"role": "user", "content": f"""Text information:{pdfText} some related questions:{user_Question}"""})

    # Process the valuation
    MAX_TURNS = 20
    final_response = None
    conversation_results = []

    for turn in range(MAX_TURNS):
        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=conversation_history,
                tools=tools_schema,
                tool_choice="auto",
                temperature=0.1
            )
        except Exception as e:
            return {"error": f"Error calling LLM API: {str(e)}"}

        message = response.choices[0].message

        if message.tool_calls:
            conversation_history.append(message)
            tool_calls = message.tool_calls

            for tool_call in tool_calls:
                function_name = tool_call.function.name
                function_args_str = tool_call.function.arguments
                try:
                    function_args = json.loads(function_args_str)
                except json.JSONDecodeError as e:
                    function_response_content = {"error": f"Invalid JSON arguments: {e}"}
                    conversation_history.append({
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": function_name,
                        "content": json.dumps(function_response_content)
                    })
                    continue

                if function_name in available_functions:
                    try:
                        function_response_content = available_functions[function_name](**function_args)
                    except Exception as e:
                        function_response_content = {"error": f"Error during {function_name} execution: {e}"}
                else:
                    function_response_content = {"error": f"Unknown function: {function_name}"}

                conversation_history.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": json.dumps(function_response_content)
                })
                conversation_results.append({
                    "function": function_name,
                    "arguments": function_args,
                    "response": function_response_content
                })

        elif message.content:
            final_response = message.content
            conversation_history.append({"role": "assistant", "content": final_response})
            break

    if not final_response and turn == MAX_TURNS - 1:
        try:
            summary_prompt = "Please summarize the valuation based on the information gathered so far, even if incomplete."
            conversation_history.append({"role": "user", "content": summary_prompt})
            final_summary_response = client.chat.completions.create(
                model=model_name,
                messages=conversation_history,
                tools=tools_schema,
                tool_choice="none",
                temperature=0.2
            )
            final_response = final_summary_response.choices[0].message.content
        except Exception as e:
            final_response = f"Error requesting final summary: {str(e)}"

    print(f"Final response: {final_response}")
    return {
        "final_response": final_response,
        # "conversation_results": conversation_results,
        # "conversation_history": conversation_history
    } 