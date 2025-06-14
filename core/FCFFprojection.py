import numpy as np
import pandas as pd
import openai
import os
import json
from db.mongodb import db
from bson import ObjectId
from dotenv import load_dotenv
import sys

# Load environment variables from .env file
load_dotenv()

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
        pdf_question = db.user_qas.find_one({"pdf_id": pdfid})
        if not pdf_doc:
            raise ValueError(f"No PDF found with ID: {pdfid}")
        return pdf_doc, pdf_question
    except Exception as e:
        raise Exception(f"Error extracting PDF text: {str(e)}")

class DCFCalculator:
    """
    A class to perform Discounted Cash Flow (DCF) valuation.
    Calculates Free Cash Flow to the Firm (FCFF), Terminal Value,
    and Net Present Value (NPV) of the firm.
    """

    def __init__(self,
                 projection_horizon_years: int,
                 discount_rate: float,
                 tax_rate: float,
                 terminal_value_method: str = "gordon_growth", # 'gordon_growth' or 'exit_multiple'
                 terminal_growth_rate: float = None, # Required for gordon_growth
                 exit_multiple: float = None, # Required for exit_multiple
                 initial_ppe: float = 0.0 # Initial Net PP&E for the year prior to Year 1
                ):
        """
        Initializes the DCFCalculator with core parameters.

        Args:
            projection_horizon_years (int): Number of years for explicit cash flow projection (e.g., 5).
            discount_rate (float): The discount rate (WACC) as a decimal (e.g., 0.10 for 10%).
            tax_rate (float): The corporate tax rate as a decimal (e.g., 0.25 for 25%).
            terminal_value_method (str): Method for calculating terminal value ('gordon_growth' or 'exit_multiple').
            terminal_growth_rate (float, optional): Long-term growth rate for Gordon Growth Model (e.g., 0.02).
                                                     Required if terminal_value_method is 'gordon_growth'.
            exit_multiple (float, optional): Exit multiple (e.g., 8.0 for 8x EBITDA).
                                             Required if terminal_value_method is 'exit_multiple'.
            initial_ppe (float): Net Property, Plant, and Equipment (PP&E) at the end of the period prior to the first forecast year.
        """
        if terminal_value_method not in ["gordon_growth", "exit_multiple"]:
            raise ValueError("terminal_value_method must be 'gordon_growth' or 'exit_multiple'.")
        if terminal_value_method == "gordon_growth" and terminal_growth_rate is None:
            raise ValueError("terminal_growth_rate is required for 'gordon_growth' method.")
        if terminal_value_method == "exit_multiple" and exit_multiple is None:
            raise ValueError("exit_multiple is required for 'exit_multiple' method.")
        if discount_rate <= 0:
            raise ValueError("Discount rate must be positive.")
        if terminal_growth_rate is not None and terminal_growth_rate >= discount_rate and terminal_value_method == "gordon_growth":
            raise ValueError("Terminal growth rate must be less than the discount rate for Gordon Growth Model.")

        self.projection_horizon_years = projection_horizon_years
        self.discount_rate = discount_rate
        self.tax_rate = tax_rate
        self.terminal_value_method = terminal_value_method
        self.terminal_growth_rate = terminal_growth_rate
        self.exit_multiple = exit_multiple
        self.initial_ppe = initial_ppe
        self.forecast_years = [f"Year {i+1}" for i in range(projection_horizon_years)]

        # Store calculated values internally
        self.fcff_df = None
        self.terminal_value = None
        self.present_value_of_explicit_fcff = None
        self.present_value_of_terminal_value = None
        self.total_npv = None

    def _calculate_fcff(self,
                        revenues: list,
                        cost_of_goods_sold: list,
                        operating_expenses: list,
                        depreciation_amortization: list,
                        capex: list,
                        change_in_net_working_capital: list
                       ) -> pd.DataFrame:
        """
        Calculates Free Cash Flow to the Firm (FCFF) for each forecast year,
        including detailed breakdown of EBITDA and PP&E.
        """
        if not (len(revenues) == len(cost_of_goods_sold) == len(operating_expenses) ==
                len(depreciation_amortization) == len(capex) == len(change_in_net_working_capital) ==
                self.projection_horizon_years):
            raise ValueError("All input lists for FCFF calculation must match the projection horizon length.")

        revenues = np.array(revenues, dtype=float)
        cost_of_goods_sold = np.array(cost_of_goods_sold, dtype=float)
        operating_expenses = np.array(operating_expenses, dtype=float)
        depreciation_amortization = np.array(depreciation_amortization, dtype=float)
        capex = np.array(capex, dtype=float)
        change_in_net_working_capital = np.array(change_in_net_working_capital, dtype=float)

        gross_profit = revenues - cost_of_goods_sold
        ebitda = gross_profit - operating_expenses
        ebit = ebitda - depreciation_amortization
        nopat = ebit * (1 - self.tax_rate)

        fcff = nopat + depreciation_amortization - capex - change_in_net_working_capital

        net_ppe = [0.0] * self.projection_horizon_years
        gross_ppe = [0.0] * self.projection_horizon_years

        net_ppe_prev = self.initial_ppe
        gross_ppe_prev = self.initial_ppe

        for i in range(self.projection_horizon_years):
            net_ppe[i] = net_ppe_prev + capex[i] - depreciation_amortization[i]
            gross_ppe[i] = gross_ppe_prev + capex[i]

            net_ppe_prev = net_ppe[i]
            gross_ppe_prev = gross_ppe[i]

        fcff_df = pd.DataFrame({
            'Revenues': revenues,
            'Cost of Goods Sold': cost_of_goods_sold,
            'Gross Profit': gross_profit,
            'Operating Expenses': operating_expenses,
            'EBITDA': ebitda,
            'Depreciation & Amortization': depreciation_amortization,
            'EBIT': ebit,
            'NOPAT (EBIT * (1 - Tax Rate))': nopat,
            'CapEx': capex,
            'Change in Net Working Capital': change_in_net_working_capital,
            'FCFF': fcff,
            'Net PP&E': net_ppe,
            'Gross PP&E': gross_ppe
        }, index=self.forecast_years)

        return fcff_df

    def _calculate_terminal_value(self, fcff_df: pd.DataFrame) -> float:
        """
        Calculates the Terminal Value based on the chosen method.
        """
        final_year_fcff = fcff_df['FCFF'].iloc[-1]
        final_year_ebitda = fcff_df['EBITDA'].iloc[-1]
        terminal_value = 0.0

        if self.terminal_value_method == "gordon_growth":
            terminal_value = (final_year_fcff * (1 + self.terminal_growth_rate)) / \
                             (self.discount_rate - self.terminal_growth_rate)
        elif self.terminal_value_method == "exit_multiple":
            terminal_value = final_year_ebitda * self.exit_multiple
        
        return terminal_value

    def calculate_dcf_valuation(self,
                                revenues: list,
                                cost_of_goods_sold: list,
                                operating_expenses: list,
                                depreciation_amortization: list,
                                capex: list,
                                change_in_net_working_capital: list
                               ) -> tuple[float, pd.DataFrame]:
        """
        Performs the full DCF valuation and stores results internally.
        Only prints the FCFF table.
        """
        self.fcff_df = self._calculate_fcff(
            revenues, cost_of_goods_sold, operating_expenses,
            depreciation_amortization, capex, change_in_net_working_capital
        )
        print("\n---")
        print("## Free Cash Flow to the Firm (FCFF) Projections")
        print(self.fcff_df.round(2).to_string(formatters={col: '{:,.2f}'.format for col in self.fcff_df.columns}))
        print("---\n")

        self.terminal_value = self._calculate_terminal_value(self.fcff_df)

        present_value_of_fcff_list = []
        for i, year_fcff in enumerate(self.fcff_df['FCFF']):
            pv = year_fcff / ((1 + self.discount_rate)**(i + 1))
            present_value_of_fcff_list.append(pv)
        self.present_value_of_explicit_fcff = sum(present_value_of_fcff_list)

        self.present_value_of_terminal_value = self.terminal_value / ((1 + self.discount_rate)**self.projection_horizon_years)

        self.total_npv = self.present_value_of_explicit_fcff + self.present_value_of_terminal_value

        # The rest of the detailed output for TV and PV calculations is suppressed as requested.
        # However, the values are stored in self.terminal_value, self.present_value_of_explicit_fcff, etc.
        # You can access them directly from the DCFCalculator object after running this method.
        # For example: print(dcf_val.total_npv)

        return self.total_npv, self.fcff_df

# --- WACC and Cost of Equity (CAPM) Calculation Functions ---
def calculate_wacc(market_value_equity, market_value_debt, cost_of_equity, cost_of_debt, corporate_tax_rate):
    """
    Calculates Weighted Average Cost of Capital (WACC).
    """
    V = market_value_equity + market_value_debt
    if V == 0:
        return 0.0
    wacc = (market_value_equity / V) * cost_of_equity + \
           (market_value_debt / V) * cost_of_debt * (1 - corporate_tax_rate)
    return wacc

def calculate_cost_of_equity_capm(risk_free_rate, beta, market_risk_premium):
    """
    Calculates Cost of Equity using Capital Asset Pricing Model (CAPM).
    """
    cost_of_equity = risk_free_rate + beta * market_risk_premium
    return cost_of_equity

# --- MAIN EXECUTION BLOCK ---
def perform_fcff_projection(pdfid: str) -> dict:
    """
    Perform FCFF projection based on PDF text extracted from MongoDB.
    
    Args:
        pdfid (str): The ID of the PDF document containing financial information
    
    Returns:
        dict: The FCFF projection results and calculations
    """
    # Extract PDF text from MongoDB
    try:
        print("pdfID", pdfid)
        pdf_doc, qa_doc = get_pdf_text(pdfid)
        if not pdf_doc or not qa_doc:
            return {"error": "No text content found in the PDF"}
        
        # Extract text and Q&A from documents
        pdf_text = pdf_doc.get('text', '')
        qa_data = qa_doc.get('qas', [])
        
        # Format Q&A into a readable string
        qa_text = ""
        for qa in qa_data:
            question = qa.get('question', '')
            answer = qa.get('answer', '')
            if question and answer:
                qa_text += f"Q: {question}\nA: {answer}\n\n"
        
        print("PDF Text:", pdf_text[:200] + "...")  # Print first 200 chars for debugging
        print("QA Text:", qa_text[:200] + "...")    # Print first 200 chars for debugging
        
    except Exception as e:
        return {"error": f"Failed to extract PDF text: {str(e)}"}

    # Set up API client
    client = openai.OpenAI(
        api_key=os.getenv("GEMINI_API_KEY"),
        base_url="https://generativelanguage.googleapis.com/v1beta/openai"
    )

    # Create the financial forecast prompt
    forecast_prompt = f"""
    You are a financial analyst. Analyze the following company information and generate a 5-year financial forecast.

    COMPANY INFORMATION:
    {pdf_text}

    USER QUESTIONS AND ANSWERS:
    {qa_text}

    Based on the above information, generate a financial forecast in the following JSON format:
    {{
        "assumptions": {{
            "revenue_growth_rate": <float between 0 and 1>,
            "cog_growth_rate": <float between 0 and 1>,
            "opex_growth_rate": <float between 0 and 1>,
            "depreciation_rate": <float between 0 and 1>,
            "capex_rate": <float between 0 and 1>,
            "working_capital_rate": <float between 0 and 1>,
            "tax_rate": <float between 0 and 1>,
            "terminal_growth_rate": <float between 0 and 1>
        }},
        "methodology": "<brief explanation of your forecasting approach>",
        "projections": {{
            "revenues": [<5 float values>],
            "cost_of_goods_sold": [<5 float values>],
            "gross_profit": [<5 float values>],
            "operating_expenses": [<5 float values>],
            "ebitda": [<5 float values>],
            "depreciation_amortization": [<5 float values>],
            "ebit": [<5 float values>],
            "nopat": [<5 float values>],
            "capex": [<5 float values>],
            "change_in_net_working_capital": [<5 float values>],
            "fcff": [<5 float values>],
            "net_ppe": [<5 float values>],
            "gross_ppe": [<5 float values>]
        }}
    }}

    IMPORTANT:
    1. Use ONLY the information provided in the company information and Q&A
    2. Return ONLY the JSON object, no other text
    3. All numbers should be positive
    4. All arrays must have exactly 5 values
    5. All rates must be between 0 and 1
    6. Base your assumptions on the actual company data provided
    """

    try:
        # Get the financial forecast from the LLM
        response = client.chat.completions.create(
            model="gemini-2.0-flash",
            messages=[{"role": "user", "content": forecast_prompt}],
            temperature=0.1
        )

        # Get the response content and clean it
        response_content = response.choices[0].message.content.strip()
        print("Raw LLM Response:", response_content[:200] + "...")  # Print first 200 chars for debugging
        
        # Remove any markdown code block indicators if present
        response_content = response_content.replace('```json', '').replace('```', '').strip()
        
        # Try to parse the JSON response
        try:
            forecast_data = json.loads(response_content)
        except json.JSONDecodeError as e:
            print(f"JSON Parse Error: {str(e)}")
            print(f"Cleaned Response Content: {response_content}")
            return {"error": f"Invalid JSON response from LLM: {str(e)}"}

        # Validate the required fields in the response
        required_fields = ["assumptions", "methodology", "projections"]
        for field in required_fields:
            if field not in forecast_data:
                return {"error": f"Missing required field in LLM response: {field}"}

        # Validate the projections data
        required_metrics = [
            "revenues", "cost_of_goods_sold", "gross_profit", "operating_expenses",
            "ebitda", "depreciation_amortization", "ebit", "nopat", "capex",
            "change_in_net_working_capital", "fcff", "net_ppe", "gross_ppe"
        ]
        
        for metric in required_metrics:
            if metric not in forecast_data["projections"]:
                return {"error": f"Missing required metric in projections: {metric}"}
            if not isinstance(forecast_data["projections"][metric], list):
                return {"error": f"Invalid data type for metric {metric}: expected list"}
            if len(forecast_data["projections"][metric]) != 5:
                return {"error": f"Invalid number of values for metric {metric}: expected 5"}

        # Format the FCFF table in the requested structure
        table_header = "| **Metric**                    | **Year 1**   | **Year 2**   | **Year 3**   | **Year 4**   | **Year 5**    |"
        table_separator = "|------------------------------|--------------|--------------|--------------|--------------|---------------|"
        
        # Create the formatted table
        formatted_table = [table_header, table_separator]
        
        # Define the metrics and their display names
        metrics = [
            ("revenues", "Revenues"),
            ("cost_of_goods_sold", "Cost of Goods Sold"),
            ("gross_profit", "Gross Profit"),
            ("operating_expenses", "Operating Expenses"),
            ("ebitda", "EBITDA"),
            ("depreciation_amortization", "Depreciation & Amortization"),
            ("ebit", "EBIT"),
            ("nopat", "NOPAT"),
            ("capex", "CapEx"),
            ("change_in_net_working_capital", "Change in Net Working Capital"),
            ("fcff", "FCFF"),
            ("net_ppe", "Net PP&E"),
            ("gross_ppe", "Gross PP&E")
        ]
        
        # Add each metric row
        for metric_key, metric_name in metrics:
            values = forecast_data["projections"][metric_key]
            row = f"| {metric_name:<30} |"
            for value in values:
                row += f" {value:,.2f} |"
            formatted_table.append(row)

        # Join the table lines with newlines
        formatted_output = "\n".join(formatted_table)

        return {
            "fcff_table": formatted_output,
            "assumptions": forecast_data["assumptions"],
            "methodology": forecast_data["methodology"]
        }

    except Exception as e:
        print(f"Error in FCFF projection: {str(e)}")
        return {"error": f"Error generating financial forecast: {str(e)}"}

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        pdfid = sys.argv[1]
    else:
        pdfid = os.getenv("PDF_ID")
        if not pdfid:
            print("Error: Please provide a PDF ID either as a command line argument or set PDF_ID environment variable")
            sys.exit(1)

    result = perform_fcff_projection(pdfid)
    
    if "error" in result:
        print(f"\nERROR: {result['error']}")
    else:
        print("\nFinancial Forecast Assumptions:")
        for key, value in result["assumptions"].items():
            print(f"{key.replace('_', ' ').title()}: {value:.2%}")
        
        print("\nForecasting Methodology:")
        print(result["methodology"])
        
        print("\nFCFF Projection Table:")
        print(result["fcff_table"])